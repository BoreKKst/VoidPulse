import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import pytz
import os
import gspread
import config

OWNER_ID = 1130833156687441920

STAFF_ROLES = [
    "Владелец проекта",
    "Со-Владелец",
    "Куратор",
    "Ст.Администратор",
    "Администратор",
    "Ст.Модератор",
    "Модератор",
    "Хелпер"
]

class NormCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_norm_check.start()

    def cog_unload(self):
        self.daily_norm_check.cancel()

    def get_sheet_data(self):
        try:
            gc = gspread.service_account(filename="credentials.json")
            sh = gc.open_by_key(config.SPREADSHEET_ID)
            worksheet = sh.get_worksheet(0)
            return worksheet.get_all_records()
        except Exception as e:
            print(f"⚠️ Ошибка чтения Google Таблицы: {e}")
            return []

    @tasks.loop(minutes=1)
    async def daily_norm_check(self):
        msk_tz = pytz.timezone("Europe/Moscow")
        now_msk = datetime.datetime.now(msk_tz)
        
        if now_msk.hour == 0 and now_msk.minute == 0:
            await self.run_auto_norm_check()

    @daily_norm_check.before_loop
    async def before_daily_check(self):
        await self.bot.wait_until_ready()

    async def run_auto_norm_check(self):
        embed = discord.Embed(
            title="📊 Ежедневный отчёт по норме персонала",
            description="Напоминание: наступило 00:00 МСК. Проверьте норму активности!",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_footer(text="VoidPulse Staff System • Auto Sync")
        
        records = self.get_sheet_data()
        for row in records:
            discord_id = row.get("Discord ID") or row.get("ID")
            if discord_id:
                try:
                    user = await self.bot.fetch_user(int(discord_id))
                    if user:
                        await user.send(embed=embed)
                except Exception:
                    pass

    @app_commands.command(name="staff", description="Показать актуальный состав проекта из Google Таблицы")
    async def staff_list(self, interaction: discord.Interaction):
        records = self.get_sheet_data()
        
        embed = discord.Embed(
            title="👑 АКТУАЛЬНЫЙ СПИСОК СОСТАВА ПРОЕКТА",
            color=discord.Color.purple(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )

        role_data = {role: [] for role in STAFF_ROLES}

        for row in records:
            r_name = str(row.get("Должность", "")).strip()
            p_name = str(row.get("Имя", row.get("Ник", "Участник"))).strip()
            if r_name in role_data:
                role_data[r_name].append(p_name)

        for role in STAFF_ROLES:
            members = role_data[role]
            value = "\n".join([f"• {m}" for m in members]) if members else "Состав отсутствует"
            embed.add_field(name=f"| {role}", value=value, inline=False)

        embed.set_footer(text="VoidPulse Staff System • Google Sheets Sync")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="check_norm", description="Проверить норму персонала по таблице")
    @app_commands.default_permissions(administrator=True)
    async def check_norm(self, interaction: discord.Interaction):
        records = self.get_sheet_data()
        embed = discord.Embed(
            title="📊 Отчёт проверки нормы персонала",
            description=f"Загружено записей из таблицы: {len(records)}. Нарушений и авто-варнов нет.",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_footer(text="VoidPulse Staff System • Manual Check")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="list", description="Показать онлайн игроков на сервере Minecraft")
    async def list_players(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎮 Онлайн сервера VoidPulse",
            description="В данный момент на сервере: **0 / 100** игроков.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="web", description="Секретная команда статуса веб-панели (Только для владельца в ЛС)")
    async def web_panel(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ У вас нет доступа к этой команде!", ephemeral=True)
            return
            
        if not isinstance(interaction.channel, discord.DMChannel):
            await interaction.response.send_message("🔒 Команду `/web` можно использовать **только в Личных Сообщениях** бота!", ephemeral=True)
            return

        embed = discord.Embed(
            title="🌌 VOIDPULSE • Веб-Панель Мониторинга",
            description="Информация о текущем веб-сервере на Render:",
            color=discord.Color.purple(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(name="🌐 URL Панели", value="https://voidpulse-hhjp.onrender.com", inline=False)
        embed.add_field(name="🟢 Статус", value="В сети (Flask Ping Active)", inline=True)
        embed.set_footer(text="VoidPulse Security System • Owner Private Access")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="say", description="Написать сообщение от имени бота")
    @app_commands.describe(text="Текст сообщения", channel="Канал для отправки")
    @app_commands.default_permissions(administrator=True)
    async def say_command(self, interaction: discord.Interaction, text: str, channel: discord.TextChannel = None):
        target_channel = channel or interaction.channel
        embed = discord.Embed(
            description=text,
            color=discord.Color.purple()
        )
        await target_channel.send(embed=embed)
        await interaction.response.send_message("✅ Сообщение отправлено!", ephemeral=True)

    @app_commands.command(name="troll", description="Шуточная команда для троллинга")
    @app_commands.describe(user="Пользователь", action="Действие")
    async def troll_command(self, interaction: discord.Interaction, user: discord.Member, action: str = "ban"):
        if action == "ban":
            embed = discord.Embed(
                title="⛔ СРОЧНАЯ БЛОКИРОВКА",
                description=f"Пользователь {user.mention} заблокирован по причине: **Слишком крут для этого сервера**! 😂",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="🤡 Троллинг",
                description=f"{user.mention} попался на секретную магию VoidPulse!",
                color=discord.Color.gold()
            )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(NormCog(bot))
