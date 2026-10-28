import discord
from discord.ext import commands
import os
import asyncio

OWNER_ID = 1374053953301385308
TOKEN = os.getenv("TOKEN") or os.getenv("DISCORD_TOKEN")

class CamouflageBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True
        super().__init__(command_prefix="!", intents=intents)

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
                # Если ты оффлайн или невидимый — бот тоже невидимка
                if owner.status in [discord.Status.offline, discord.Status.invisible]:
                    await bot.change_presence(status=discord.Status.invisible, activity=None)
                else:
                    # Если ты в сети, активен или не беспокоить — бот зеленый и "играет в VoidPulse"
                    activity = discord.Game(name="VoidPulse")
                    await bot.change_presence(status=discord.Status.online, activity=activity)
        await asyncio.sleep(5) # Проверка каждые 5 секунд для мгновенной реакции

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ Ошибка: Токен не найден!")
