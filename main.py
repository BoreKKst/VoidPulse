import discord
from discord.ext import commands
import os
import asyncio
import config
from web import keep_alive

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 Бот {bot.user} запущен и готов к работе!")
    
    # Загружаем коги
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"📦 Модуль cogs/{filename} загружен.")
            except Exception as e:
                print(f"❌ Ошибка загрузки cogs/{filename}: {e}")

    # Мгновенная синхронизация слэш-команд на всех серверах
    try:
        synced = await bot.tree.sync()
        print(f"✅ Синхронизированно слэш-команд: {len(synced)}")
    except Exception as e:
        print(f"⚠️ Ошибка синхронизации команд: {e}")

# Запуск Flask сервера для 24/7
keep_alive()

token = os.getenv("DISCORD_TOKEN", config.TOKEN)
bot.run(token)
