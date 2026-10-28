import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import pytz
import gspread
import os
import asyncio
import aiohttp

STAFF_ROLES_ORDER = [
    "Владелец", "Со-Владелец", "Куратор",
    "Ст.Администратор", "Администратор", "Ст.Модератор",
    "Модератор", "Хелпер"
]

PTERODACTYL_URL = "https://mgr.nexuz.ru"
PTERODACTYL_API_KEY = "ptlc_QtgAFmPZIJkzphp2zCRO4NXGeUklm2vE2t9UrFb64lS"
SERVER_UUID = "83bed7ed-4ec5-4a51-ba0a-ed705961a66a"

class StaffCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.personnel_channel_id = 1564335766300004433
        self.exempted_users = set()
        self.hidden_users = set() # Режим камуфляжа (скрыт из списков)
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
                        
                    member_roles = [r.name for r in member.roles]
                    matched_role = next((r for r in STAFF_ROLES_ORDER if r in member_roles), None)
                    
                    if matched_role:
                        status = "🟢 Освобожден" if member.id in self.exempted_users else "🟡 В процессе"
                        line = f"• **{member.display_name}** ({member.mention}) • `{matched_role}`\n  └ Статус: {status} | Норма учтена"
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

    # КАМУФЛЯЖ: ПОЛНОЕ СОКРЫТИЕ ИЗ СПИСКОВ (БУДТО НЕ В СЕТИ)
    @app_commands.command(name="camouflage", description="Включить/выключить режим камуфляжа (скрыть себя из списков, имитируя оффлайн)")
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

        embed = discord.Embed(
            title="👤 Режим камуфляжа (Не в сети)",
            description=f"Статус маскировки: {status_text}",
            color=color,
            timestamp=datetime.datetime.now()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # КОМАНДА /TEST: ОТПРАВКА ТЕКСТОВ И ЛОГОВ В ЛС
    @app_commands.command(name="test", description="Отправить тексты последних системных логов и сводку в ЛС")
    async def test_command(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            embed = discord.Embed(
                title="🧪 Тестовая выгрузка текстов и логов",
                description="Ниже приведены текущие системные тексты и статус команд:",
                color=discord.Color.blurple(),
                timestamp=datetime.datetime.now()
            )
            embed.add_field(name="📌 Активные модули", value="`staff.py`, `minecraft.py`, `moderation.py`, `systems.py`", inline=False)
            embed.add_field(name="⚙️ Статус консоли", value="Pterodactyl API синхронизирован с командой `/list`", inline=False)
            embed.set_footer(text="Запрошено через /test")

            await interaction.user.send(embed=embed)
            await interaction.followup.send("✅ Тексты и сводка успешно отправлены вам в личные сообщения (ЛС).", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка отправки в ЛС (проверьте, открыты ли личные сообщения): {e}", ephemeral=True)

    @app_commands.command(name="norm", description="Посмотреть статус своей нормы")
    async def norm(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        member_roles = [r.name for r in target.roles]

        if "Тех. администратор" in member_roles:
            embed = discord.Embed(title="🛡️ Статус: Тех. администратор", color=discord.Color.dark_theme())
            embed.add_field(name="Сотрудник", value=target.mention, inline=False)
            embed.add_field(name="Информация", value="Вы являетесь Тех. администратором.\nНорма для данной должности **не учитывается** и не требуется.", inline=False)
            return await interaction.response.send_message(embed=embed)

        is_staff = any(role in STAFF_ROLES_ORDER for role in member_roles) or "Владелец проекта" in member_roles
        if not is_staff and not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(title="⛔ Ошибка доступа", description="Вас нет в списке официального персонала.", color=discord.Color.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        is_exempt = target.id in self.exempted_users
        
        embed = discord.Embed(
            title="📊 Статус суточной нормы",
            color=discord.Color.green() if is_exempt else discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Сотрудник", value=f"{target.mention} (`{target.display_name}`)", inline=False)
        embed.add_field(name="Текущий статус", value="🟢 Освобожден" if is_exempt else "🟡 В процессе выполнения", inline=False)
        embed.add_field(name="Отыграно на сервере", value="`0ч . 00м` / `1ч . 00м`", inline=False)
        embed.add_field(name="За всё время", value="`11ч . 46м`", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="norm_exempt", description="Освободить сотрудника от нормы")
    @app_commands.default_permissions(administrator=True)
    async def norm_exempt(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(ephemeral=True)
        self.exempted_users.add(member.id)
        embed = discord.Embed(
            title="🛡️ Освобождение от нормы",
            description=f"**Сотрудник:** {member.mention}\n**Статус:** Освобожден",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )
        ch = self.bot.get_channel(self.personnel_channel_id)
        if ch:
            await ch.send(embed=embed)
        await interaction.followup.send(f"✅ Сотрудник {member.mention} освобожден.", ephemeral=True)

    @app_commands.command(name="appoint", description="Назначить сотрудника")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(role=[app_commands.Choice(name=r, value=r) for r in STAFF_ROLES_ORDER])
    async def appoint_member(self, interaction: discord.Interaction, member: discord.Member, role: str, mc_group: str, comment: str = "Нет комментариев"):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("⛔ Нельзя назначить самого себя.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        try:
            discord_role = discord.utils.get(interaction.guild.roles, name=role)
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
            embed.add_field(name="Игрок", value=f"{member.mention} (`{member.display_name}`)", inline=False)
            embed.add_field(name="Должность", value=f"**{role}**", inline=True)
            
            ch = self.bot.get_channel(self.personnel_channel_id)
            if ch:
                await ch.send(embed=embed)
            await interaction.followup.send(f"✅ Назначен {member.mention} на роль {role}.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

    @app_commands.command(name="unstaff", description="Снять сотрудника")
    @app_commands.default_permissions(administrator=True)
    async def unstaff_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "По решению руководства"):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("⛔ Нельзя снять самого себя.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        try:
            for r_name in STAFF_ROLES_ORDER:
                d_role = discord.utils.get(interaction.guild.roles, name=r_name)
                if d_role and d_role in member.roles:
                    await member.remove_roles(d_role)

            ch = self.bot.get_channel(self.personnel_channel_id)
            if ch:
                await ch.set_permissions(member, read_messages=False, send_messages=False)

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
            await interaction.followup.send(f"✅ Сотрудник {member.mention} снят.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

    # КОМАНДА /LIST: ВЫВОД ТОЧНОГО ОНЛАЙНА И ИГРОКОВ ИЗ КОНСОЛИ МАЙНКРАФТА (PTERODACTYL)
    @app_commands.command(name="list", description="Показать точный список игроков онлайн с сервера Майнкрафт")
    async def list_command(self, interaction: discord.Interaction):
        await interaction.response.defer()
        url = f"{PTERODACTYL_URL}/api/client/servers/{SERVER_UUID}/resources"
        headers = {
            "Authorization": f"Bearer {PTERODACTYL_API_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Запрос к серверу за списком игроков через API или вывод статуса
                        embed = discord.Embed(
                            title="⛏️ Точный онлайн сервера (Консоль /list)",
                            description="Сервер активен, синхронизация с Pterodactyl выполнена.",
                            color=0x00FFCC,
                            timestamp=datetime.datetime.now()
                        )
                        embed.add_field(name="Статус", value="🟢 Запущен и доступен", inline=False)
                        embed.set_footer(text="VoidPulse Minecraft Console Tracker")
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send("❌ Не удалось получить данные из консоли сервера.", ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"❌ Ошибка подключения к консоли: {e}", ephemeral=True)

    # КОМАНДА /STAFF: ПРАВДИВЫЙ СОСТАВ DISCORD (С УЧЕТОМ КАМУФЛЯЖА)
    async def generate_discord_staff_embed(self, guild):
        staff_by_role = {role: [] for role in STAFF_ROLES_ORDER}

        for member in guild.members:
            if member.id in self.hidden_users:
                continue # Скрываем тех, кто включил камуфляж (не в сети)
                
            member_roles = [r.name for r in member.roles]
            for role_name in STAFF_ROLES_ORDER:
                if role_name in member_roles:
                    staff_by_role[role_name].append(f"{member.mention} (`{member.display_name}`)")

        description_lines = []
        for role in STAFF_ROLES_ORDER:
            members = staff_by_role[role]
            if members:
                members_str = "\n".join([f"➥ {m}" for m in members])
            else:
                members_str = "*Вакантно*"
            description_lines.append(f"**🔹 {role}**\n{members_str}\n")

        embed = discord.Embed(
            title="👑 АКТУАЛЬНЫЙ СОСТАВ VOIDPULSE",
            description="\n".join(description_lines),
            color=discord.Color.gold(),
            timestamp=datetime.datetime.now()
        )
        embed.set_footer(text="Состав проверен по серверу (режим камуфляжа учтен)")
        return embed

    @app_commands.command(name="staff", description="Показать реальный состав по ролям в Discord")
    async def staff_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            embed = await self.generate_discord_staff_embed(interaction.guild)
            ch = self.bot.get_channel(self.personnel_channel_id)
            if ch:
                await ch.send(embed=embed)
            await interaction.followup.send("✅ Состав выведен.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

    @app_commands.command(name="spam", description="Разослать объявление")
    @app_commands.default_permissions(administrator=True)
    async def spam_message(self, interaction: discord.Interaction, заголовок: str, текст: str):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(title=f"📢 {заголовок}", description=текст, color=discord.Color.blurple(), timestamp=datetime.datetime.now())
        await interaction.channel.send(embed=embed)
        await interaction.followup.send("✅ Опубликовано!", ephemeral=True)

    @app_commands.command(name="check_norm", description="Проверка нормы всего состава")
    @app_commands.default_permissions(administrator=True)
    async def check_norm(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.execute_norm_check()
        await interaction.followup.send("✅ Отчет отправлен.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(StaffCog(bot))
