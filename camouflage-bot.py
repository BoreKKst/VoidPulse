import discord
from discord.ext import commands
import os
import asyncio

# Настройки твоего главного ID (твой аккаунт Discord) и токена
OWNER_ID = 1324350693292773438 # Твой ID из контекста
TOKEN = os.getenv("TOKEN") or os.getenv("DISCORD_TOKEN")

class CamouflageBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True # Обязательно для отслеживания онлайн-статуса
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print("🔗 Модуль брата-камуфляжа инициализирован.")

bot = CamouflageBot()

@bot.event
async def on_ready():
    print(f"🤖 Бот-брат запущен как {bot.user}")
    bot.loop.create_task(sync_status_with_brother())

async def sync_status_with_brother():
    await bot.wait_until_ready()
    while not bot.is_closed():
        for guild in bot.guilds:
            owner = guild.get_member(OWNER_ID)
            if owner:
                # Проверяем статус владельца (брата)
                if owner.status == discord.Status.offline or owner.status == discord.Status.invisible:
                    # Если ты вышел / оффлайн — бот тоже ставит статус "Невидимый / Оффлайн"
                    await bot.change_presence(status=discord.Status.invisible, activity=None)
                else:
                    # Если ты в сети — бот активен и показывает статусный вид
                    activity = discord.Game(name="VoidPulse Security | С братом в сети 🟢")
                    await bot.change_presence(status=discord.Status.online, activity=activity)
        await asyncio.sleep(10) # Проверка каждые 10 секунд

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ Ошибка: Не найден токен бота в переменных окружения!")
