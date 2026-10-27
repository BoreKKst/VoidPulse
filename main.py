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
    return web.Response(text="VoidPulse Auth API: ONLINE", content_type='text/html')

async def handle_register_mc(request):
    try:
        data = await request.json()
        auth_cog = bot_instance.get_cog("AuthVerificationCog")
        if auth_cog:
            success, msg = await auth_cog.register_mc_session(
                data.get("secret_key"),
                data.get("mc_nick"),
                data.get("code"),
                data.get("session_id")
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
    code = request.query.get("code")
    session_id = request.query.get("session_id")
    
    auth_cog = bot_instance.get_cog("AuthVerificationCog")
    if auth_cog:
        verified, status = auth_cog.atomic_consume_session(secret_key, mc_nick, code, session_id)
        return web.json_response({"verified": verified, "status": status})
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
