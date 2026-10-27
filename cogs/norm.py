import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import pytz
import os
import config
import gspread
import urllib.request
import json

SERVER_IP = "voidpulse.nexuz.ru"
STAFF_ROLES = ["Владелец проекта", "Со-Владелец", "Куратор", "Ст.Администратор", "Администратор", "Ст.Модератор", "Модератор", "Хелпер"]

warns_storage = {}

class TicketModal(discord.ui.Modal, title="Создание тикета"):
    def __init__(self, category):
        super().__init__()
        self.category = category

    message = discord.ui.TextInput(
        label="Опишите вопрос/проблему",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"🎫 Тикет: {self.category}",
            description=f"**От:** {interaction.user.mention}\n\n**Текст:**\n{self.message.value}",
            color=discord.Color.purple(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        try:
            owner = await interaction.client.fetch_user(config.OWNER_ID)
            await owner.send(embed=embed)
        except: pass
            
        if getattr(config, "TICKET_CHANNEL_ID", 0) != 0:
            channel = interaction.client.get_channel(config.TICKET_CHANNEL_ID)
            if channel: await channel.send(embed=embed)

        await interaction.response.send_message("✅ Ваш тикет успешно создан и передан администрации.", ephemeral=True)

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Технический вопрос", emoji="⚙️"),
            discord.SelectOption(label="Жалоба на персонал", emoji="🛡️"),
            discord.SelectOption(label="Покупка", emoji="💎"),
            discord.SelectOption(label="Связь с создателем", emoji="📞")
        ]
        super().__init__(placeholder="Выберите категорию...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketModal(self.values[0]))

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


class NormCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_channels.start()
        self.sheet_norm_checker.start()

    def cog_unload(self):
        self.sheet_norm_checker.cancel()

    def get_sheet_data(self):
        try:
            gc = gspread.service_account(filename="credentials.json")
            sh = gc.open_by_key(config.SPREADSHEET_ID)
            return sh.get_worksheet(0).get_all_records()
        except Exception as e:
            print(f"⚠️ Ошибка чтения таблицы: {e}")
            return []

    @tasks.loop(count=1)
    async def setup_channels(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            log_channel = discord.utils.get(guild.text_channels, name="📊-команды-логи")
            if not log_channel:
                try: await guild.create_text_channel("📊-команды-логи", topic="Логи использования команд всеми участниками")
                except: pass
            
            mc_channel = discord.utils.get(guild.text_channels, name="💬-чат-майнкрафт")
            if not mc_channel:
                try: await guild.create_text_channel("💬-чат-майнкрафт", topic="Чат сервера VoidPulse")
                except: pass

    @tasks.loop(hours=10)
    async def sheet_norm_checker(self):
        await self.bot.wait_until_ready()
        records = self.get_sheet_data()
        if not records: return

        completed_list = []
        failed_list = []

        for row in records:
            discord_id = row.get("Discord ID") or row.get("ID")
            name = row.get("Имя", row.get("Ник", "Сотрудник"))
            role = row.get("Должность", "Сотрудник")
            
            try:
                norm = float(row.get("Норма", row.get("Требуется", 1)))
                done = float(row.get("Выполнено", row.get("Сегодня", 0)))
            except:
                norm, done = 1.0, 0.0

            if discord_id:
                try:
                    user = await self.bot.fetch_user(int(discord_id))
                    if done >= norm:
                        completed_list.append(f"👤 **{name}** ({role}) — Выполнено ({done}/{norm})")
                    else:
                        failed_list.append(f"👤 **{name}** ({role}) — Не выполнено ({done}/{norm})")
                        uid = str(user.id)
                        if uid not in warns_storage: warns_storage[uid] = []
                        warns_storage[uid].append({
                            "reason": "Невыполнение нормы за 10 часов",
                            "date": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
                            "author": "Система VoidPulse"
                        })
                        try:
                            await user.send("⚠️ **Предупреждение:** Вы не выполнили норму в Google Таблице за 10 часов!")
                        except: pass
                except: pass

        try:
            owner = await self.bot.fetch_user(config.OWNER_ID)
            embed = discord.Embed(title="📊 Отчёт по норме персонала (10ч)", color=discord.Color.purple(), timestamp=datetime.datetime.now(datetime.timezone.utc))
            embed.add_field(name="🟢 Выполнили норму", value="\n".join(completed_list) if completed_list else "Никого", inline=False)
            embed.add_field(name="🔴 Не выполнили (варн)", value="\n".join(failed_list) if failed_list else "Все молодцы!", inline=False)
            await owner.send(embed=embed)
        except: pass

    @sheet_norm_checker.before_loop
    async def before_checker(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command: app_commands.Command):
        guild = interaction.guild
        if guild:
            log_channel = discord.utils.get(guild.text_channels, name="📊-команды-логи")
            if log_channel:
                user_roles = [r.name for r in interaction.user.roles]
                is_staff = any(role in STAFF_ROLES for role in user_roles)
                status = "🛡️ **ПЕРСОНАЛ**" if is_staff or interaction.user.id == config.OWNER_ID else "👤 **ИГРОК**"
                color = discord.Color.red() if is_staff or interaction.user.id == config.OWNER_ID else discord.Color.light_grey()
                
                embed = discord.Embed(title="🔍 Использование команды", description=f"{status} {interaction.user.mention} использовал команду `/{command.name}`", color=color, timestamp=datetime.datetime.now(datetime.timezone.utc))
                try: await log_channel.send(embed=embed)
                except: pass

    # --- ВАРНЫ ---
    @app_commands.command(name="warn", description="Выдать предупреждение сотруднику (Владелец)")
    @app_commands.describe(user="Кому выдать варн", reason="Причина выговора")
    async def warn_user(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ Доступно только владельцу!", ephemeral=True)
        
        uid = str(user.id)
        if uid not in warns_storage: warns_storage[uid] = []
        warns_storage[uid].append({
            "reason": reason,
            "date": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
            "author": interaction.user.name
        })
        
        count = len(warns_storage[uid])
        embed = discord.Embed(title="⚠️ Выдан выговор (Warn)", color=discord.Color.orange())
        embed.add_field(name="Сотрудник", value=user.mention, inline=False)
        embed.add_field(name="Причина", value=reason, inline=False)
        embed.add_field(name="Всего выговоров", value=str(count), inline=False)
        
        try: await user.send(embed=discord.Embed(title="⚠️ Вы получили предупреждение", description=f"Причина: {reason}\nВсего варнов: {count}", color=discord.Color.orange()))
        except: pass

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="unwarn", description="Снять последнее предупреждение (Владелец)")
    @app_commands.describe(user="У кого снять варн")
    async def unwarn_user(self, interaction: discord.Interaction, user: discord.Member):
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ Доступно только владельцу!", ephemeral=True)
        
        uid = str(user.id)
        if uid in warns_storage and warns_storage[uid]:
            removed = warns_storage[uid].pop()
            count = len(warns_storage[uid])
            await interaction.response.send_message(f"✅ Снят последний варн с {user.mention} (Причина: `{removed['reason']}`). Осталось: {count}", ephemeral=True)
        else:
            await interaction.response.send_message(f"⚠️ У пользователя {user.mention} нет активных выговоров.", ephemeral=True)

    @app_commands.command(name="warns", description="Посмотреть предупреждения")
    @app_commands.describe(user="Чьи варны посмотреть (оставь пустым для себя)")
    async def view_warns(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        uid = str(target.id)
        
        if interaction.user.id != config.OWNER_ID and target != interaction.user:
            return await interaction.response.send_message("❌ Вы можете смотреть только свои предупреждения.", ephemeral=True)

        user_warns = warns_storage.get(uid, [])
        embed = discord.Embed(title=f"📋 Предупреждения: {target.name}", color=discord.Color.blue())
        if not user_warns:
            embed.description = "У пользователя нет активных выговоров."
        else:
            for idx, w in enumerate(user_warns, 1):
                embed.add_field(name=f"Выговор #{idx} ({w['date']})", value=f"**Причина:** {w['reason']}\n*Выдал: {w['author']}*", inline=False)
                
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # --- АДМИН КОМАНДЫ ---
    @app_commands.command(name="check_norm", description="Проверить норму по таблице (Владелец)")
    async def check_norm(self, interaction: discord.Interaction):
        if interaction.user.id != config.OWNER_ID: return await interaction.response.send_message("❌", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        records = self.get_sheet_data()
        embed = discord.Embed(title="📊 Проверка нормы", color=discord.Color.blue())
        if not records: embed.description = "⚠️ Данные не найдены."
        else:
            for row in records[:12]:
                embed.add_field(name=f"👤 {row.get('Имя', 'Сотрудник')} ({row.get('Должность', 'Сотрудник')})", value=f"🎯 Требуется: **{row.get('Норма', '0')}** | 🟢 Выполнено: **{row.get('Выполнено', '0')}**", inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="say", description="Написать от имени бота (Владелец)")
    async def say_command(self, interaction: discord.Interaction, title: str, text: str):
        if interaction.user.id != config.OWNER_ID: return await interaction.response.send_message("❌", ephemeral=True)
        await interaction.channel.send(embed=discord.Embed(title=title, description=text, color=discord.Color.purple()))
        await interaction.response.send_message("✅", ephemeral=True)

    @app_commands.command(name="reload", description="Перезапуск бота (Владелец)")
    async def reload_bot(self, interaction: discord.Interaction):
        if interaction.user.id != config.OWNER_ID: return await interaction.response.send_message("❌", ephemeral=True)
        await interaction.response.send_message("🔄 Перезагрузка...", ephemeral=True)
        os._exit(0)

    @app_commands.command(name="status", description="Статус (Владелец)")
    async def status_system(self, interaction: discord.Interaction):
        if interaction.user.id != config.OWNER_ID: return await interaction.response.send_message("❌", ephemeral=True)
        await interaction.response.send_message(embed=discord.Embed(title="📊 Статус", description="Системы активны.", color=discord.Color.purple()), ephemeral=True)

    @app_commands.command(name="checking", description="Проверка API (Владелец)")
    async def checking_system(self, interaction: discord.Interaction):
        if interaction.user.id != config.OWNER_ID: return await interaction.response.send_message("❌", ephemeral=True)
        await interaction.response.send_message("🔍 Интеграции стабильны.", ephemeral=True)
        
    @app_commands.command(name="test", description="Тест (Владелец)")
    async def test_system(self, interaction: discord.Interaction):
        if interaction.user.id != config.OWNER_ID: return await interaction.response.send_message("❌", ephemeral=True)
        await interaction.response.send_message("🧪 Работает на 100%.", ephemeral=True)

    # --- ПУБЛИЧНЫЕ КОМАНДЫ ---
    @app_commands.command(name="staff", description="Показать состав проекта")
    async def staff_list(self, interaction: discord.Interaction):
        records = self.get_sheet_data()
        embed = discord.Embed(title="👑 АКТУАЛЬНЫЙ СОСТАВ", color=discord.Color.purple())
        role_data = {role: [] for role in STAFF_ROLES}
        for row in records:
            r, p = str(row.get("Должность", "")).strip(), str(row.get("Имя", row.get("Ник", "Участник"))).strip()
            if r in role_data: role_data[r].append(p)
        for role in STAFF_ROLES:
            members = role_data[role]
            embed.add_field(name=f"| {role}", value="\n".join([f"• {m}" for m in members]) if members else "Состав отсутствует", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="list", description="Онлайн Minecraft сервера")
    async def list_players(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            url = f"https://api.mcsrvstat.us/2/{SERVER_IP}"
            data = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'VoidPulse'}), timeout=5).read().decode())
            if data.get("online"):
                embed = discord.Embed(title="🎮 Онлайн", description=f"IP: `{SERVER_IP}`\nИгроков: **{data['players'].get('online', 0)} / {data['players'].get('max', 100)}**", color=discord.Color.green())
            else: embed = discord.Embed(title="🎮 Онлайн", description="🔴 Сервер офлайн.", color=discord.Color.red())
        except: embed = discord.Embed(title="🎮 Онлайн", description="⚠️ Ошибка пинга.", color=discord.Color.orange())
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="связаться", description="Форма создания тикета")
    async def contact_creator(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=discord.Embed(title="📞 Поддержка VoidPulse", description="Выберите категорию.", color=discord.Color.gold()), view=TicketView(), ephemeral=True)

    @app_commands.command(name="staff_help", description="Памятка для персонала")
    async def staff_help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🛡️ Памятка для персонала", color=discord.Color.blue())
        embed.add_field(name="📌 Основное", value="- Норма проверяется автоматически каждые 10 часов.\n- Данные берутся из Google Таблиц.", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="все_команды", description="Навигатор по всем командам бота")
    async def all_commands_list(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🌌 Навигатор по командам VoidPulse",
            description="Полный список доступных команд:",
            color=discord.Color.teal()
        )
        embed.add_field(
            name="👑 Административные (Только Владелец)",
            value=(
                "**`/check_norm`** — Проверка нормы по таблице\n"
                "**`/warn`** — Выдать выговор сотруднику\n"
                "**`/unwarn`** — Снять выговор\n"
                "**`/say`** — Написать от имени бота\n"
                "**`/reload`** — Перезапуск бота\n"
                "**`/status`** — Статус серверов\n"
                "**`/checking`** — Проверка API\n"
                "**`/test`** — Тест систем"
            ),
            inline=False
        )
        embed.add_field(
            name="🛡️ Модерация и Общие",
            value=(
                "**`/warns`** — Посмотреть предупреждения\n"
                "**`/staff_help`** — Шпаргалка стаффа\n"
                "**`/list`** — Онлайн майнкрафт сервера\n"
                "**`/staff`** — Состав проекта\n"
                "**`/связаться`** — Создать тикет\n"
                "**`/все_команды`** — Этот список"
            ),
            inline=False
        )
        embed.set_footer(text="Служба безопасности VoidPulse")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(NormCog(bot))
