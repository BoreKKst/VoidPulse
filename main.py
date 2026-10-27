import discord
from discord.ext import commands
import os
import asyncio
import config
from web import keep_alive

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Статус бота (Играет на сервере)
activity = discord.Game(name="VoidPulse | voidpulse.nexuz.ru")
bot = commands.Bot(command_prefix="!", intents=intents, activity=activity)

@bot.event
async def on_ready():
    print(f"🤖 Бот {bot.user} запущен и готов к работе!")
    
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
            except Exception as e:
                print(f"❌ Ошибка cogs/{filename}: {e}")

    try:
        synced = await bot.tree.sync()
        print(f"✅ Синхронизировано команд: {len(synced)}")
    except Exception as e:
        print(f"⚠️ Ошибка синхронизации: {e}")

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN", config.TOKEN))
