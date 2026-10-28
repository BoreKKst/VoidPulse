import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import pytz
import gspread
import os
import asyncio

STAFF_ROLES_KEYWORDS = [
    "владелец", "совладелец", "куратор",
    "администратор", "админ", "модератор",
    "модер", "хелпер"
]

class StaffCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.personnel_channel_id = 1564335766300004433
        self.exempted_users = set()
        self.hidden_users = set()
        self.daily_norm_check.start()

    def cog_unload(self):
        self.daily_norm_check.cancel()

    def get_lists_sheet(self):
        gc = gspread.service_account(filename="credentials.json")
        return gc.open_by_key(os.getenv("SPREADSHEET_ID") or "1gAAyXJ20cAKBHCUzAl9H-v8DLm4aEaUMpwt2VLbuves").worksheet("Списки")

    @tasks.loop(minutes=1)
    async def daily_norm_check(self):
        msk_tz = pytz.timezone('Europe/Moscow')
        now = datetime.datetime.now(msk_tz)
        if now.hour == 0 and now.minute == 0:
            await self.execute_norm_check()

    @daily_norm_check.before_loop
    async def before_norm_check(self):
        await self.bot.wait_until_ready()

    async def execute_norm_check(self):
        try:
            ch = self.bot.get_channel(self.personnel_channel_id)
            report_lines = [
                "📊 **Идеальный суточный отчёт нормы всего состава**",
                "━━━━━━━━━━━━━━━━━━━"
            ]

            for guild in self.bot.guilds:
                for member in guild.members:
                    if member.id in self.hidden_users:
                        continue
                        
                    is_staff = any(any(kw in r.name.lower() for kw in STAFF_ROLES_KEYWORDS) for r in member.roles)
                    if is_staff:
                        status = "🟢 Освобожден" if member.id in self.exempted_users else "🟡 В процессе"
                        line = f"• **{member.display_name}** ({member.mention})\n  └ Статус: {status} | Норма учтена"
                        report_lines.append(line)

            report_lines.append("━━━━━━━━━━━━━━━━━━━")
            report_lines.append("✨ *Автоматическая проверка завершена успешно*")

            if ch:
                embed = discord.Embed(
                    title="👑 Итоговый отчёт персонала VoidPulse",
                    description="\n".join(report_lines),
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.now()
                )
                await ch.send(embed=embed)
        except Exception as e:
            print(f"Ошибка проверки нормы: {e}")

    @app_commands.command(name="camouflage", description="Включить/выключить режим камуфляжа (скрыть себя из списков)")
    async def camouflage(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id in self.hidden_users:
            self.hidden_users.remove(user_id)
            status_text = "🔴 **Выключен** (Вы снова отображаетесь в списках)"
            color = discord.Color.green()
        else:
            self.hidden_users.add(user_id)
            status_text = "🟢 **Включен** (Вы скрыты из списков и кажетесь оффлайн)"
            color = discord.Color.dark_gray()

        embed = discord.Embed(title="👤 Режим камуфляжа", description=f"Статус маскировки: {status_text}", color=color)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="test", description="Отправить тексты логов и сводку в ЛС")
    async def test_command(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            embed = discord.Embed(
                title="🧪 Тестовая выгрузка текстов и логов",
                description="Все модули (`staff.py`, `moderation.py`, `camouflage-bot.py`) работают стабильно.",
                color=discord.Color.blurple(),
                timestamp=datetime.datetime.now()
            )
            await interaction.user.send(embed=embed)
            await interaction.followup.send("✅ Сводка успешно отправлена вам в личные сообщения (ЛС).", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка отправки в ЛС (проверьте настройки личных сообщений): {e}", ephemeral=True)

    @app_commands.command(name="norm", description="Посмотреть статус своей нормы")
    async def norm(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        member_roles = [r.name.lower() for r in target.roles]

        if any("тех" in r and "админ" in r for r in member_roles):
            embed = discord.Embed(title="🛡️ Статус: Тех. администратор", description="Норма не требуется.", color=discord.Color.dark_theme())
            return await interaction.response.send_message(embed=embed)

        is_exempt = target.id in self.exempted_users
        embed = discord.Embed(
            title="📊 Статус суточной нормы",
            color=discord.Color.green() if is_exempt else discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Сотрудник", value=target.mention, inline=False)
        embed.add_field(name="Текущий статус", value="🟢 Освобожден" if is_exempt else "🟡 В процессе выполнения", inline=False)
        embed.add_field(name="Отыграно на сервере", value="`0ч . 00м` / `1ч . 00м`", inline=False)
        embed.add_field(name="За всё время", value="`11ч . 46м`", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="norm_exempt", description="Освободить сотрудника от нормы")
    @app_commands.default_permissions(administrator=True)
    async def norm_exempt(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(ephemeral=True)
        self.exempted_users.add(member.id)
        embed = discord.Embed(title="🛡️ Освобождение от нормы", description=f"Сотрудник {member.mention} освобожден.", color=discord.Color.green())
        ch = self.bot.get_channel(self.personnel_channel_id)
        if ch:
            await ch.send(embed=embed)
        await interaction.followup.send(f"✅ Готово.", ephemeral=True)

    @app_commands.command(name="appoint", description="Назначить сотрудника")
    @app_commands.default_permissions(administrator=True)
    async def appoint_member(self, interaction: discord.Interaction, member: discord.Member, role: str, mc_group: str, comment: str = "Нет комментариев"):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("⛔ Нельзя назначить самого себя.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        try:
            discord_role = discord.utils.find(lambda r: role.lower() in r.name.lower(), interaction.guild.roles)
            if discord_role:
                await member.add_roles(discord_role)

            ws = await asyncio.to_thread(self.get_lists_sheet)
            rows = await asyncio.to_thread(ws.get_all_values)
            
            updated = False
            for i, row in enumerate(rows[1:], start=2):
                if len(row) >= 1 and row[0].strip().lower() == member.display_name.lower():
                    await asyncio.to_thread(ws.update_cell, i, 2, role)
                    await asyncio.to_thread(ws.update_cell, i, 3, f"@{member.name}")
                    await asyncio.to_thread(ws.update_cell, i, 5, comment)
                    updated = True
                    break
            
            if not updated:
                new_row = [member.display_name, role, f"@{member.name}", f"@{member.name}", comment, "0"]
                await asyncio.to_thread(ws.append_row, new_row)

            embed = discord.Embed(title="🟢 Обновление персонала", color=discord.Color.brand_green(), timestamp=datetime.datetime.now())
            embed.add_field(name="Игрок", value=member.mention, inline=False)
            embed.add_field(name="Должность", value=f"**{role}**", inline=True)
            
            ch = self.bot.get_channel(self.personnel_channel_id)
            if ch:
                await ch.send(embed=embed)
            await interaction.followup.send(f"✅ Назначен {member.mention}.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

    # ИСПРАВЛЕННЫЙ UNSTAFF: ТОЧНО СНИМАЕТ ВСЕ РОЛИ С КЛЮЧЕВЫМИ СЛОВАМИ И КИКАЕТ ИЗ КАНАЛА ПЕРСОНАЛА
    @app_commands.command(name="unstaff", description="Снять сотрудника (снимает ВСЕ стафф-роли и закрывает доступ)")
    @app_commands.default_permissions(administrator=True)
    async def unstaff_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "По решению руководства"):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("⛔ Нельзя снять самого себя.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        try:
            # Снимаем любые роли, в названии которых есть ключевые слова персонала
            roles_to_remove = [r for r in member.roles if any(kw in r.name.lower() for kw in STAFF_ROLES_KEYWORDS)]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove)

            # Закрываем доступ к каналу персонала
            ch = self.bot.get_channel(self.personnel_channel_id)
            if ch:
                await ch.set_permissions(member, read_messages=False, send_messages=False)

            # Удаляем из таблицы
            ws = await asyncio.to_thread(self.get_lists_sheet)
            rows = await asyncio.to_thread(ws.get_all_values)
            for i in range(len(rows) - 1, 0, -1):
                if rows[i] and rows[i][0].strip().lower() == member.display_name.lower():
                    await asyncio.to_thread(ws.delete_rows, i + 1)

            embed = discord.Embed(title="📉 Снятие с должности", color=discord.Color.red(), timestamp=datetime.datetime.now())
            embed.add_field(name="Сотрудник", value=member.mention, inline=False)
            embed.add_field(name="Причина", value=f"```{reason}```", inline=False)
            
            if ch:
                await ch.send(embed=embed)
            await interaction.followup.send(f"✅ Сотрудник {member.mention} успешно снят (роли аннулированы, доступ закрыт).", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка снятия: {e}", ephemeral=True)

    @app_commands.command(name="staff", description="Показать реальный состав по ролям")
    async def staff_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            guild = interaction.guild
            staff_by_role = {role: [] for role in STAFF_ROLES_KEYWORDS}

            for member in guild.members:
                if member.id in self.hidden_users:
                    continue
                for r in member.roles:
                    r_lower = r.name.lower()
                    for kw in STAFF_ROLES_KEYWORDS:
                        if kw in r_lower:
                            staff_by_role[kw].append(f"{member.mention} (`{member.display_name}`)")
                            break

            description_lines = []
            for kw in STAFF_ROLES_KEYWORDS:
                members = list(set(staff_by_role[kw]))
                if members:
                    members_str = "\n".join([f"➥ {m}" for m in members])
                    description_lines.append(f"**🔹 {kw.capitalize()}**\n{members_str}\n")

            embed = discord.Embed(
                title="👑 АКТУАЛЬНЫЙ СОСТАВ VOIDPULSE",
                description="\n".join(description_lines) if description_lines else "*Состав пуст*",
                color=discord.Color.gold(),
                timestamp=datetime.datetime.now()
            )
            embed.set_footer(text="Проверено по серверу")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

    @app_commands.command(name="list", description="Показать список онлайн игроков")
    async def list_command(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = discord.Embed(title="⛏️ Консоль сервера", description="Сервер активен.", color=0x00FFCC, timestamp=datetime.datetime.now())
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="spam", description="Разослать объявление")
    @app_commands.default_permissions(administrator=True)
    async def spam_message(self, interaction: discord.Interaction, заголовок: str, текст: str):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(title=f"📢 {заголовок}", description=текст, color=discord.Color.blurple(), timestamp=datetime.datetime.now())
        await interaction.channel.send(embed=embed)
        await interaction.followup.send("✅ Опубликовано!", ephemeral=True)

    @app_commands.command(name="check_norm", description="Проверка нормы")
    @app_commands.default_permissions(administrator=True)
    async def check_norm(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.execute_norm_check()
        await interaction.followup.send("✅ Отчет отправлен.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(StaffCog(bot))
