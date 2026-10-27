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

bot_instance = VoidPulseBot()

async def handle_home(request):
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
        <title>VoidPulse Web Console</title>
        <style>
            body {{ background-color: #0b0c10; color: #66fcf1; font-family: sans-serif; text-align: center; padding: 20px; }}
            .container {{ max-width: 600px; margin: auto; background: #1f2833; padding: 25px; border-radius: 10px; border: 1px solid #45a29e; }}
            h1 {{ color: #fff; }}
            .card {{ background: #0b0c10; margin: 10px 0; padding: 12px; border-radius: 6px; text-align: left; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⚡ VOIDPULSE API & CONSOLE</h1>
            <div class="card">СТАТУС: ONLINE</div>
            <div class="card">ЦП: {cpu}% | ОЗУ: {ram.percent}%</div>
            <div class="card">АПТАЙМ: {hours}ч {mins}м {secs}с</div>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

async def handle_register_mc(request):
    try:
        data = await request.json()
        auth_cog = bot_instance.get_cog("AuthVerificationCog")
        if auth_cog:
            success, msg = await auth_cog.register_mc_code(
                data.get("secret_key"),
                data.get("mc_nick"),
                data.get("code")
            )
            if success:
                return web.json_response({"status": "success", "message": msg}, status=200)
            return web.json_response({"status": "error", "message": msg}, status=400)
        return web.json_response({"status": "error", "message": "Auth cog not loaded"}, status=500)
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=400)

async def handle_check_2fa(request):
    secret_key = request.query.get("secret_key")
    mc_nick = request.query.get("mc_nick")
    auth_cog = bot_instance.get_cog("AuthVerificationCog")
    if auth_cog:
        verified = auth_cog.check_player_verified(secret_key, mc_nick)
        return web.json_response({"verified": verified, "status": "APPROVED" if verified else "PENDING"})
    return web.json_response({"verified": False, "status": "ERROR"}, status=500)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_home)
    app.router.add_post("/register_mc_code", handle_register_mc)
    app.router.add_get("/check_2fa_status", handle_check_2fa)
    
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    if token:
        await start_web_server()
        await bot_instance.start(token)

if __name__ == "__main__":
    asyncio.run(main())
