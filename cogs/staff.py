import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import pytz
import gspread
import os
import asyncio

STAFF_ROLES_ORDER = [
    "Владелец", "Со-Владелец", "Куратор",
    "Ст.Администратор", "Администратор", "Ст.Модератор",
    "Модератор", "Хелпер"
]

class StaffCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.personnel_channel_id = 1564335766300004433
        self.exempted_users = set()
        self.daily_norm_check.start()

    def cog_unload(self):
        self.daily_norm_check.cancel()

    def get_lists_sheet(self):
        gc = gspread.service_account(filename="credentials.json")
        return gc.open_by_key(os.getenv("SPREADSHEET_ID") or "1gAAyXJ20cAKBHCUzAl9H-v8DLm4aEaUMpwt2VLbuves").worksheet("Списки")

    def parse_role(self, role_str):
        role_lower = role_str.strip().lower()
        if "со-владелец" in role_lower or "совладелец" in role_lower:
            return "Со-Владелец"
        elif "владелец" in role_lower:
            return "Владелец"
        elif "куратор" in role_lower:
            return "Куратор"
        elif "ст.администратор" in role_lower or "старший администратор" in role_lower:
            return "Ст.Администратор"
        elif "администратор" in role_lower:
            return "Администратор"
        elif "ст.модератор" in role_lower or "старший модератор" in role_lower:
            return "Ст.Модератор"
        elif "модератор" in role_lower:
            return "Модератор"
        elif "хелпер" in role_lower:
            return "Хелпер"
        return None

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
            ws = await asyncio.to_thread(self.get_lists_sheet)
            rows = await asyncio.to_thread(ws.get_all_values)
            ch = self.bot.get_channel(self.personnel_channel_id)

            report_lines = [
                "📊 **Суточный отчёт по норме (00:00 МСК)**",
                "━━━━━━━━━━━━━━━━━━━"
            ]

            if len(rows) > 1:
                seen = set()
                for row in rows[1:]:
                    if len(row) >= 2 and row[0].strip() and row[1].strip():
                        nick = row[0].strip()
                        if nick in seen: continue
                        seen.add(nick)
                        
                        role = row[1].strip()
                        hours_played = row[5].strip() if len(row) > 5 and row[5].strip() else "0"
                        matched_role = self.parse_role(role)

                        if matched_role:
                            if nick in self.exempted_users:
                                status = "🟢 Освобожден"
                                time_info = "Норма не требуется"
                            else:
                                status = "🟡 В процессе"
                                time_info = f"Отыграно: {hours_played} ч. | За всё время учтено"
                                
                            line = f"• **{nick}** • `{matched_role}`\n  └ Статус: {status}\n  └ {time_info}"
                            report_lines.append(line)

            report_lines.append("━━━━━━━━━━━━━━━━━━━")
            report_lines.append("✨ *Система автоматического контроля VoidPulse*")

            if ch:
                embed = discord.Embed(
                    title="👑 Суточный отчёт персонала VoidPulse",
                    description="\n".join(report_lines),
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.now()
                )
                await ch.send(embed=embed)
        except Exception as e:
            print(f"Ошибка проверки нормы: {e}")

    @app_commands.command(name="norm", description="Посмотреть статус своей нормы")
    async def norm(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        member_roles = [r.name for r in target.roles]

        if "Тех. администратор" in member_roles:
            embed = discord.Embed(title="🛡️ Статус: Тех. администратор", color=discord.Color.dark_theme())
            embed.add_field(name="Сотрудник", value=target.mention, inline=False)
            embed.add_field(name="Информация", value="Вы являетесь Тех. администратором.\nНорма для данной должности **не учитывается** и не требуется.", inline=False)
            embed.set_footer(text="VoidPulse Staff System")
            return await interaction.response.send_message(embed=embed)

        is_staff = any(role in STAFF_ROLES_ORDER for role in member_roles) or "Владелец проекта" in member_roles
        if not is_staff and not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(title="⛔ Ошибка доступа", description="Вас нет в списке официального персонала.", color=discord.Color.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        played_hours = "0"
        try:
            ws = await asyncio.to_thread(self.get_lists_sheet)
            rows = await asyncio.to_thread(ws.get_all_values)
            for row in rows[1:]:
                if len(row) >= 1 and row[0].strip().lower() == target.display_name.lower():
                    if len(row) > 5 and row[5].strip():
                        played_hours = row[5].strip()
                    break
        except:
            pass

        is_exempt = target.id in self.exempted_users
        
        embed = discord.Embed(
            title="📊 Статус суточной нормы",
            color=discord.Color.green() if is_exempt else discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Сотрудник", value=f"{target.mention} (`{target.display_name}`)", inline=False)
        embed.add_field(name="Текущий статус", value="🟢 Освобожден" if is_exempt else "🟡 В процессе выполнения", inline=False)
        
        if is_exempt:
            embed.add_field(name="Отыграно на сервере", value="`--` / `--`", inline=False)
            embed.add_field(name="За всё время", value="`-- ч . -- м`", inline=False)
            embed.add_field(name="Прогресс", value="`[██████████] 100%` (Освобожден)", inline=False)
        else:
            embed.add_field(name="Отыграно на сервере", value=f"`{played_hours} ч.` / `1 ч.`", inline=False)
            embed.add_field(name="За всё время", value=f"`{played_hours} ч.`", inline=False)
            embed.add_field(name="Прогресс", value=f"`[░░░░░░░░░░]`", inline=False)
            
        embed.set_footer(text="VoidPulse Time Tracker")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="norm_exempt", description="Освободить сотрудника от нормы")
    @app_commands.default_permissions(administrator=True)
    async def norm_exempt(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(ephemeral=True)
        allowed_roles = ["Владелец", "Владелец проекта", "Со-Владелец", "Куратор"]
        if not any(r.name in allowed_roles for r in interaction.user.roles):
            return await interaction.followup.send("❌ Команда доступна только Куратору и выше.", ephemeral=True)

        self.exempted_users.add(member.id)
        embed = discord.Embed(
            title="🛡️ Освобождение от нормы (Norm Exempt)",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="👤 Сотрудник", value=member.mention, inline=True)
        embed.add_field(name="🛡️ Выдал", value=interaction.user.mention, inline=True)
        embed.add_field(name="Статус", value="🟢 Полностью освобожден от суточной нормы", inline=False)
        embed.set_footer(text="VoidPulse Staff Management")

        ch = self.bot.get_channel(self.personnel_channel_id)
        if ch:
            await ch.send(embed=embed)
        await interaction.followup.send(f"✅ Сотрудник {member.mention} освобожден от суточной нормы.", ephemeral=True)

    @app_commands.command(name="appoint", description="Назначить / Повысить сотрудника (с записью в таблицу)")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(member="Кого назначаем", role="Должность из списка", mc_group="Группа в Minecraft", comment="Комментарий к назначению")
    @app_commands.choices(role=[app_commands.Choice(name=r, value=r) for r in STAFF_ROLES_ORDER])
    async def appoint_member(self, interaction: discord.Interaction, member: discord.Member, role: str, mc_group: str, comment: str = "Нет комментариев"):
        if member.id == interaction.user.id:
            embed = discord.Embed(title="⛔ Системная ошибка", description="Вы не можете назначить самого себя.", color=discord.Color.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        
        try:
            # Записываем или обновляем в Google Таблице
            ws = await asyncio.to_thread(self.get_lists_sheet)
            rows = await asyncio.to_thread(ws.get_all_values)
            
            updated = False
            for i, row in enumerate(rows[1:], start=2):
                if len(row) >= 1 and row[0].strip().lower() == member.display_name.lower():
                    # Обновляем должность, группу и комментарий
                    await asyncio.to_thread(ws.update_cell, i, 2, role) # Должность
                    await asyncio.to_thread(ws.update_cell, i, 5, comment) # Комментарий
                    updated = True
                    break
            
            if not updated:
                # Если игрока не было в таблице, добавляем новую строку: [Ник, Должность, Discord, TG/VK, Комментарий, Часы]
                new_row = [member.display_name, role, str(member.id), f"@{member.name}", comment, "0"]
                await asyncio.to_thread(ws.append_row, new_row)

            embed = discord.Embed(
                title="🟢 Официальное обновление персонала",
                color=discord.Color.brand_green(),
                timestamp=datetime.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="👤 Игрок", value=f"`{member.display_name}`\n{member.mention}", inline=True)
            embed.add_field(name="💼 Должность", value=f"**{role}**", inline=True)
            embed.add_field(name="🎮 Группа (Minecraft)", value=f"`{mc_group}`", inline=True)
            embed.add_field(name="📝 Комментарий", value=f"*{comment}*", inline=False)
            embed.add_field(name="🛡️ Назначил", value=f"{interaction.user.mention} (`{interaction.user.display_name}`)", inline=False)
            embed.set_footer(text="База данных Google Sheets обновлена")

            ch = self.bot.get_channel(self.personnel_channel_id)
            if ch:
                await ch.send(embed=embed)
            await interaction.followup.send(f"✅ Игрок {member.mention} назначен на должность **{role}** и внесен в таблицу.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка записи в таблицу: {e}", ephemeral=True)

    @app_commands.command(name="unstaff", description="Снять сотрудника (удаление из таблицы)")
    @app_commands.default_permissions(administrator=True)
    async def unstaff_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "По решению руководства"):
        if member.id == interaction.user.id:
            embed = discord.Embed(title="⛔ Системная ошибка", description="Вы не можете снять самого себя.", color=discord.Color.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        
        try:
            ws = await asyncio.to_thread(self.get_lists_sheet)
            rows = await asyncio.to_thread(ws.get_all_values)
            
            deleted = False
            for i in range(len(rows) - 1, 0, -1):
                if rows[i] and rows[i][0].strip().lower() == member.display_name.lower():
                    await asyncio.to_thread(ws.delete_rows, i + 1)
                    deleted = True

            embed = discord.Embed(
                title="📉 Снятие / Понижение с должности",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="👤 Сотрудник", value=f"{member.mention} (`{member.display_name}`)", inline=True)
            embed.add_field(name="🛡️ Снял", value=interaction.user.mention, inline=True)
            embed.add_field(name="📋 Причина", value=f"```{reason}```", inline=False)
            embed.set_footer(text="Удалено из таблицы Google Sheets")

            ch = self.bot.get_channel(self.personnel_channel_id)
            if ch:
                await ch.send(embed=embed)
            await interaction.followup.send(f"✅ Сотрудник {member.mention} снят с должности и удален из таблицы.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка при удалении из таблицы: {e}", ephemeral=True)

    @app_commands.command(name="staff", description="Показать актуальный состав без дубликатов")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.user.id)
    async def staff_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            ws = await asyncio.to_thread(self.get_lists_sheet)
            rows = await asyncio.to_thread(ws.get_all_values)

            staff_by_role = {role: [] for role in STAFF_ROLES_ORDER}
            seen_nicks = set()

            if len(rows) > 1:
                for row in rows[1:]:
                    if len(row) >= 2 and row[0].strip() and row[1].strip():
                        nick = row[0].strip()
                        if nick in seen_nicks:
                            continue # Пропускаем дубликаты
                        seen_nicks.add(nick)
                        
                        role = row[1].strip()
                        matched_role = self.parse_role(role)
                        if matched_role:
                            staff_by_role[matched_role].append(nick)

            description_lines = []
            for role in STAFF_ROLES_ORDER:
                members = staff_by_role[role]
                if members:
                    members_str = "\n".join([f"➥ `{m}`" for m in members])
                else:
                    members_str = "*Вакантно*"
                description_lines.append(f"**🔹 {role}**\n{members_str}\n")

            embed = discord.Embed(
                title="👑 АКТУАЛЬНЫЙ СОСТАВ VOIDPULSE",
                description="\n".join(description_lines),
                color=discord.Color.gold(),
                timestamp=datetime.datetime.now()
            )
            embed.set_footer(text="Синхронизировано с Google Таблицей")
            
            ch = self.bot.get_channel(self.personnel_channel_id)
            if ch:
                await ch.send(embed=embed)
            await interaction.followup.send("✅ Актуальный состав выведен.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка таблицы: {e}", ephemeral=True)

    @app_commands.command(name="list", description="Показать актуальный список персонала")
    async def list_alias(self, interaction: discord.Interaction):
        await self.staff_list.callback(self, interaction)

    @app_commands.command(name="check_norm", description="Принудительная проверка нормы состава")
    @app_commands.default_permissions(administrator=True)
    async def check_norm(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.execute_norm_check()
        await interaction.followup.send("✅ Отчет по норме отправлен.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(StaffCog(bot))
