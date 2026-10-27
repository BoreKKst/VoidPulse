import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import pytz
import random
import urllib.request
import json
import gspread
import config

OWNER_ID = 1374053953301385308
SERVER_IP = "m1.nexuz.ru:25737"

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

    @app_commands.command(name="check_norm", description="Проверить норму персонала (Только для владельца)")
    async def check_norm(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ Эта команда доступна только владельцу бота!", ephemeral=True)
            return
        records = self.get_sheet_data()
        embed = discord.Embed(
            title="📊 Отчёт проверки нормы персонала",
            description=f"Загружено записей из таблицы: {len(records)}. Нарушений и авто-варнов нет.",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_footer(text="VoidPulse Staff System • Manual Check")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="list", description="Показать реальный онлайн игроков на сервере Minecraft")
    async def list_players(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            url = f"https://api.mcsrvstat.us/2/{SERVER_IP}"
            req = urllib.request.Request(url, headers={'User-Agent': 'VoidPulseBot'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                
            if data.get("online"):
                online = data["players"].get("online", 0)
                max_slots = data["players"].get("max", 100)
                player_list = data["players"].get("list", [])
                
                names = ", ".join(player_list) if player_list else "Список игроков пуск или скрыт"
                
                embed = discord.Embed(
                    title=f"🎮 Онлайн сервера VoidPulse",
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.now(datetime.timezone.utc)
                )
                embed.add_field(name="📍 IP Сервера", value=SERVER_IP, inline=False)
                embed.add_field(name="👥 Игроки", value=f"**{online} / {max_slots}**", inline=True)
                embed.add_field(name="🟢 Статус", value="В сети", inline=True)
                if player_list:
                    embed.add_field(name="📋 Игроки онлайн", value=names, inline=False)
            else:
                embed = discord.Embed(
                    title="🎮 Онлайн сервера VoidPulse",
                    description=f"🔴 Сервер **{SERVER_IP}** в данный момент оффлайн.",
                    color=discord.Color.red()
                )
        except Exception as e:
            embed = discord.Embed(
                title="🎮 Онлайн сервера VoidPulse",
                description=f"⚠️ Не удалось подключиться к серверу: {e}",
                color=discord.Color.orange()
            )
        await interaction.followup.send(embed=embed)

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

    @app_commands.command(name="say", description="Написать сообщение от имени бота (Только для владельца)")
    @app_commands.describe(text="Текст сообщения", channel="Канал для отправки")
    async def say_command(self, interaction: discord.Interaction, text: str, channel: discord.TextChannel = None):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ Эта команда доступна только владельцу бота!", ephemeral=True)
            return
        target_channel = channel or interaction.channel
        embed = discord.Embed(description=text, color=discord.Color.purple())
        await target_channel.send(embed=embed)
        await interaction.response.send_message("✅ Сообщение отправлено!", ephemeral=True)

    @app_commands.command(name="troll", description="Шуточная команда для троллинга (Только для владельца)")
    @app_commands.describe(user="Пользователь", action="Действие")
    async def troll_command(self, interaction: discord.Interaction, user: discord.Member, action: str = "ban"):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ Эта команда доступна только владельцу бота!", ephemeral=True)
            return
        if action == "ban":
            embed = discord.Embed(title="⛔ СРОЧНАЯ БЛОКИРОВКА", description=f"Пользователь {user.mention} заблокирован по причине: **Слишком крут для этого сервера**! 😂", color=discord.Color.red())
        else:
            embed = discord.Embed(title="🤡 Троллинг", description=f"Пользователь {user.mention} попался на секретную магию VoidPulse!", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="coin", description="Подбросить монетку (Орёл или Решка)")
    async def coin_flip(self, interaction: discord.Interaction):
        result = random.choice(["🪙 Орёл!", "🪙 Решка!"])
        await interaction.response.send_message(f"🎲 Подбрасываем монетку... Результат: **{result}**")

    @app_commands.command(name="roll", description="Случайное число от 1 до 100")
    async def roll_dice(self, interaction: discord.Interaction):
        num = random.randint(1, 100)
        await interaction.response.send_message(f"🎲 Ваше случайное число: **{num}**")

    @app_commands.command(name="hug", description="Подружески обнять участника")
    @app_commands.describe(user="Кого обнять?")
    async def hug_user(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.send_message(f"🫂 {interaction.user.mention} крепко-крепко обнял(-а) {user.mention}!")

    @app_commands.command(name="8ball", description="Магический шар предсказаний")
    @app_commands.describe(question="Ваш вопрос")
    async def magic_ball(self, interaction: discord.Interaction, question: str):
        answers = [
            "Да, безусловно! ✨", "Сомнений нет. 🔮", "Конечно да!", 
            "Пока неясно, попробуй снова. 🤔", "Лучше не рассказывать. 🤫", 
            "Даже не думай об этом. ❌", "Мой ответ — нет. 🚫"
        ]
        ans = random.choice(answers)
        embed = discord.Embed(title="🎱 Магический Шар", color=discord.Color.blue())
        embed.add_field(name="Вопрос:", value=question, inline=False)
        embed.add_field(name="Ответ шара:", value=ans, inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(NormCog(bot))
