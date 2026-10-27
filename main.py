import discord
from discord.ext import commands
import gspread
import os
import config
from web import keep_alive

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class VoidPulseBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="/", intents=intents, help_command=None)
        self.sheet_staff = None
        self.sheet_warns = None
        self.init_google_sheets()

    def init_google_sheets(self):
        try:
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            if os.path.exists("credentials.json"):
                gc = gspread.service_account(filename="credentials.json", scopes=scopes)
                sh = gc.open_by_key(config.SPREADSHEET_ID)
                self.sheet_staff = sh.worksheet("Списки")
                self.sheet_warns = sh.worksheet("Учет предупреждений")
                print("✅ Google Таблицы успешно подключены!")
            else:
                print("⚠️ credentials.json не найден в папке.")
        except Exception as e:
            print(f"❌ Ошибка подключения к Google Таблицам: {e}")

    async def setup_hook(self):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f"📦 Модуль cogs.{filename[:-3]} загружен.")
                except Exception as e:
                    print(f"❌ Ошибка загрузки cogs.{filename[:-3]}: {e}")

        await self.tree.sync()
        print("⚡ Все слеш-команды синхронизированы!")

bot = VoidPulseBot()

@bot.event
async def on_ready():
    print(f"🌌 Бот {bot.user} запущен и готов к работе!")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="за составом VoidPulse"))

if __name__ == "__main__":
    keep_alive()
    bot.run(config.TOKEN)
