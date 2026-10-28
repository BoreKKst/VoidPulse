import discord
from discord.ext import commands
import aiohttp

PTERODACTYL_URL = "https://mgr.nexuz.ru"
PTERODACTYL_API_KEY "ptlc_QtgAFmPZIJkzphp2zCRO4NXGeUklm2vE2t9UrFb64lS"
SERVER_UUID = "83bed7ed-4ec5-4a51-ba0a-ed705961a66a"

SECRET_PLUGIN_KEY = "VP_SECURE_KEY_7749_BETA_SECURE"
LOG_CHANNEL_ID_1 = 1561109325471293494
LOG_CHANNEL_ID_2 = 1564882228838793338

class MinecraftCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.start_log_server())

    async def start_log_server(self):
        app = aiohttp.web.Application()
        
        async def handle_log(request):
            try:
                data = await request.json()
                if data.get("secret_key") != SECRET_PLUGIN_KEY:
                    return aiohttp.web.json_response({"status": "error", "message": "Unauthorized"}, status=401)
                
                event = data.get("event")
                player = data.get("player")
                details = data.get("details")
                
                embed = discord.Embed(
                    title=f"🛡️ VoidPulse Security Log [{event}]",
                    description=f"**Игрок:** `{player}`\n**Действие:** {details}",
                    color=0x00FFCC
                )
                
                # Отправляем в оба твоих канала
                for cid in [LOG_CHANNEL_ID_1, LOG_CHANNEL_ID_2]:
                    channel = self.bot.get_channel(cid)
                    if channel:
                        await channel.send(embed=embed)
                        
                return aiohttp.web.json_response({"status": "success"})
            except Exception as e:
                return aiohttp.web.json_response({"status": "error", "message": str(e)}, status=500)

        app.router.add_post('/api/log', handle_log)
        
        port = int(os.environ.get("PORT", 8080)) if 'os' in globals() else 8080
        # Запуск веб-сервера для логов бота
        runner = aiohttp.web.AppRunner(app)
        await runner.setup()
        site = aiohttp.web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        print(f"✅ [LOG API] Бот слушает серверные логи на порту {port}")

    async def fetch_server_ptero_stats(self):
        url = f"{PTERODACTYL_URL}/api/client/servers/{SERVER_UUID}/resources"
        headers = {
            "Authorization": f"Bearer {PTERODACTYL_API_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        attr = data.get("attributes", {})
                        state = attr.get("current_state", "offline")
                        res = attr.get("resources", {})
                        
                        cpu_usage = res.get("cpu_absolute", 0.0)
                        mem_bytes = res.get("memory_bytes", 0)
                        mem_mb = round(mem_bytes / (1024 * 1024), 1)
                        
                        return {
                            "online": True,
                            "state": state,
                            "cpu": round(cpu_usage, 1),
                            "memory": mem_mb
                        }
                    else:
                        return {"online": False, "error": f"API Error: {response.status}"}
            except Exception as e:
                return {"online": False, "error": str(e)}

    @commands.command(name="status")
    async def server_status(self, ctx):
        stats = await self.fetch_server_ptero_stats()
        if not stats.get("online"):
            await ctx.send(f"❌ Failed to fetch panel data: {stats.get('error')}")
            return

        state_emoji = "🟢" if stats["state"] == "running" else "🔴"
        
        embed = discord.Embed(
            title="📊 VoidPulse Server Status",
            color=0x00FFCC
        )
        embed.add_field(name="State", value=f"{state_emoji} {stats['state'].upper()}", inline=True)
        embed.add_field(name="CPU", value=f"`{stats['cpu']}%`", inline=True)
        embed.add_field(name="RAM", value=f"`{stats['memory']} MB`", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MinecraftCog(bot))
