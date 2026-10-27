import discord
from discord.ext import commands
import os
import asyncio
from aiohttp import web
import psutil
import time

token = os.getenv("TOKEN") or os.getenv("DISCORD_TOKEN")
start_time = time.time()

class VoidPulseBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
        self.allowed_channels = [
            1564335765054300322, 1554536535247032401, 1564608886974058528, 
            1564335766195404910, 1564608889398231124, 1564335766300004433, 
            1564335766300004434, 1564335766195404909
        ]

    async def setup_hook(self):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
        await self.tree.sync()

    async def on_guild_join(self, guild):
        channel_ids = [c.id for c in guild.channels]
        if not any(cid in self.allowed_channels for cid in channel_ids):
            await guild.leave()

async def handle(request):
    ram = psutil.virtual_memory()
    cpu = psutil.cpu_percent()
    uptime_sec = int(time.time() - start_time)
    mins, secs = divmod(uptime_sec, 60)
    hours, mins = divmod(mins, 60)
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VoidPulse Web Console</title>
        <style>
            body {{ background-color: #0b0c10; color: #66fcf1; font-family: 'Segoe UI', monospace; padding: 20px; text-align: center; }}
            .container {{ max-width: 650px; margin: 40px auto; background: #1f2833; padding: 30px; border-radius: 12px; box-shadow: 0 0 20px rgba(102, 252, 241, 0.2); border: 1px solid #45a29e; }}
            h1 {{ color: #ffffff; text-shadow: 0 0 10px #66fcf1; margin-bottom: 25px; }}
            .card {{ background: #0b0c10; margin: 12px 0; padding: 15px; border-radius: 8px; text-align: left; font-size: 1.1em; border-left: 4px solid #66fcf1; }}
            .status {{ color: #45a29e; font-weight: bold; }}
            .highlight {{ color: #ffffff; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⚡ VOIDPULSE WEB CONSOLE</h1>
            <div class="card">СТАТУС СЕРВЕРА: <span class="status">● ONLINE (ACTIVE 24/7)</span></div>
            <div class="card">НАГРУЗКА ЦП: <span class="highlight">{cpu}%</span></div>
            <div class="card">ОЗУ: <span class="highlight">{ram.percent}%</span> ({round(ram.used / 1024 / 1024)} MB / {round(ram.total / 1024 / 1024)} MB)</div>
            <div class="card">ОПЕРАЦИОННАЯ СИСТЕМА: <span class="highlight">Linux / Render Cloud Container</span></div>
            <div class="card">АПТАЙМ НЕПРЕРЫВНО: <span class="highlight">{hours}ч {mins}м {secs}с</span></div>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Веб-консоль запущена на порту {port}")

async def main():
    bot = VoidPulseBot()
    if token:
        await start_web_server()
        await bot.start(token)
    else:
        print("❌ ОШИБКА: Токен не найден!")

if __name__ == "__main__":
    asyncio.run(main())
