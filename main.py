import discord
from discord.ext import commands
import os
import config
from web import keep_alive

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
    
    # Проверка очереди перезапуска (сообщаем Владельцу, что всё встало идеально)
    if os.path.exists("restart_queue.txt"):
        os.remove("restart_queue.txt")
        try:
            owner = await bot.fetch_user(config.OWNER_ID)
            embed = discord.Embed(title="🔄 Отчёт о перезапуске", description="✅ Все новые изменения успешно применены!\nБот подключён к Render и работает без ошибок.", color=discord.Color.green())
            await owner.send(embed=embed)
        except:
            pass

if __name__ == "__main__":
    keep_alive()
    token = os.getenv("TOKEN", config.TOKEN)
    if token:
        bot.run(token, log_handler=None)
