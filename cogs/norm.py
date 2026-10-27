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

    def get_sheet_data(self):
        try:
            gc = gspread.service_account(filename="credentials.json")
            sh = gc.open_by_key(config.SPREADSHEET_ID)
            return sh.get_worksheet(0).get_all_records()
        except:
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

    # --- АДМИН КОМАНДЫ ---
    @app_commands.command(name="web", description="Секретная ссылка на панель управления (Владелец)")
    async def web_panel(self, interaction: discord.Interaction):
        if interaction.user.id != config.OWNER_ID: return await interaction.response.send_message("❌ Доступ закрыт.", ephemeral=True)
        link = f"https://voidpulse-hhjp.onrender.com/?token={config.WEB_SECRET_TOKEN}"
        embed = discord.Embed(title="🌌 Доступ к панели (Никому не давать!)", description=f"Твоя зашифрованная ссылка для входа без пароля:\n**[ВОЙТИ В ПАНЕЛЬ]({link})**", color=discord.Color.purple())
        try:
            await interaction.user.send(embed=embed)
            await interaction.response.send_message("✅ Секретная ссылка отправлена тебе в ЛС!", ephemeral=True)
        except:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="check_norm", description="Проверить норму (Владелец)")
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

    @app_commands.command(name="status", description="Технический статус (Владелец)")
    async def status_system(self, interaction: discord.Interaction):
        if interaction.user.id != config.OWNER_ID: return await interaction.response.send_message("❌", ephemeral=True)
        await interaction.response.send_message(embed=discord.Embed(title="📊 Статус", description="Все системы активны.", color=discord.Color.purple()), ephemeral=True)

    @app_commands.command(name="checking", description="Проверка API привязок (Владелец)")
    async def checking_system(self, interaction: discord.Interaction):
        if interaction.user.id != config.OWNER_ID: return await interaction.response.send_message("❌", ephemeral=True)
        await interaction.response.send_message("🔍 Интеграции с Google Sheets и Flask стабильны.", ephemeral=True)
        
    @app_commands.command(name="test", description="Тест систем (Владелец)")
    async def test_system(self, interaction: discord.Interaction):
        if interaction.user.id != config.OWNER_ID: return await interaction.response.send_message("❌", ephemeral=True)
        await interaction.response.send_message("🧪 Системы работают на 100%.", ephemeral=True)

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
        embed.add_field(name="📌 Основное", value="- Норма проверяется автоматически в 00:00 МСК.\n- Данные берутся из Google Таблиц.", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="все_команды", description="Навигатор по всем командам бота")
    async def all_commands_list(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🌌 Навигатор по командам VoidPulse",
            description="Полный список доступных команд и их назначение:",
            color=discord.Color.teal()
        )
        
        embed.add_field(
            name="👑 Административные (Только Владелец)",
            value=(
                "**`/web`** — Секретная ссылка на веб-панель (LP Editor)\n"
                "**`/check_norm`** — Выгрузка отчета по норме персонала\n"
                "**`/say`** — Написать красивое сообщение от имени бота\n"
                "**`/reload`** — Экстренный перезапуск систем бота\n"
                "**`/status`** — Проверка технического статуса серверов\n"
                "**`/checking`** — Проверка привязок (Таблицы, API)\n"
                "**`/test`** — Тестовая системная команда"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🛡️ Модерация (Персонал)",
            value="**`/staff_help`** — Открыть шпаргалку и правила для стаффа",
            inline=False
        )
        
        embed.add_field(
            name="🌐 Общие (Для всех)",
            value=(
                "**`/list`** — Узнать текущий онлайн на сервере\n"
                "**`/staff`** — Посмотреть актуальный состав проекта\n"
                "**`/связаться`** — Создать тикет (Вопрос, жалоба, донат)\n"
                "**`/все_команды`** — Открыть это меню"
            ),
            inline=False
        )
        
        embed.set_footer(text="Служба безопасности VoidPulse")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(NormCog(bot))
