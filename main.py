import discord
from discord.ext import commands
import os
import config
import web  # Импортируем наш веб-сервер для открытия порта на Render

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class VoidPulseBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        try:
            await self.load_extension("cogs.norm")
            print("✅ Ког norm успешно загружен.")
            await self.tree.sync()
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")

bot = VoidPulseBot()

@bot.event
async def on_ready():
    print(f"🚀 Бот {bot.user} запущен и готов к работе!")
    
    if os.path.exists("restart_queue.txt"):
        os.remove("restart_queue.txt")
        try:
            owner = await bot.fetch_user(config.OWNER_ID)
            embed = discord.Embed(title="🔄 Перезапуск", description="✅ Бот успешно запущен в чистом режиме!", color=discord.Color.green())
            await owner.send(embed=embed)
        except:
            pass

if __name__ == "__main__":
    # Запускаем веб-сервер в фоне, чтобы Render обнаружил открытый порт
    web.keep_alive()
    
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token, log_handler=None)
    else:
        print("❌ ОШИБКА: Токен не найден!")
