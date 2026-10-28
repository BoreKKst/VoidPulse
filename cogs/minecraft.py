import discord
from discord.ext import commands
import aiohttp
import os
import datetime

PTERODACTYL_URL = "https://mgr.nexuz.ru"
PTERODACTYL_API_KEY = "ptlc_QtgAFmPZIJkzphp2zCRO4NXGeUklm2vE2t9UrFb64lS"
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

                if event == "join":
                    embed = discord.Embed(title="🔌 Вход на сервер", description=f"Игрок **{player}** успешно авторизовался.", color=discord.Color.green())
                elif event == "command":
                    embed = discord.Embed(title="⌨️ Использование команд", description=f"**{player}** ввел команду:\n```{details}```", color=discord.Color.orange())
                else:
                    embed = discord.Embed(title=f"🛡️ Лог безопасности: {event}", description=f"**Игрок:** `{player}`\n**Действие:**\n```{details}```", color=0x00FFCC)
                
                embed.timestamp = datetime.datetime.now()

                for cid in [LOG_CHANNEL_ID_1, LOG_CHANNEL_ID_2]:
                    channel = self.bot.get_channel(cid)
                    if channel:
                        await channel.send(embed=embed)

                return aiohttp.web.json_response({"status": "success"})
            except Exception as e:
                return aiohttp.web.json_response({"status": "error", "message": str(e)}, status=500)

        app.router.add_post('/api/log', handle_log)

        port = int(os.environ.get("LOG_PORT", 8081))
        runner = aiohttp.web.AppRunner(app)
        await runner.setup()
        site = aiohttp.web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        print(f"✅ [LOG API] Сервер логов запущен на порту {port}")

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
                        mem_mb = round(res.get("memory_bytes", 0) / (1024 * 1024), 1)
                        disk_mb = round(res.get("disk_bytes", 0) / (1024 * 1024), 1)
                        uptime_ms = res.get("uptime", 0)
                        uptime_min = round(uptime_ms / 60000)

                        return {
                            "online": True, "state": state, "cpu": round(cpu_usage, 1),
                            "memory": mem_mb, "disk": disk_mb, "uptime": uptime_min
                        }
                    else:
                        return {"online": False, "error": f"API Error {response.status}"}
            except Exception as e:
                return {"online": False, "error": str(e)}

    @commands.command(name="status")
    async def server_status(self, ctx):
        stats = await self.fetch_server_ptero_stats()
        if not stats.get("online"):
            embed = discord.Embed(title="❌ Ошибка статуса", description=f"Не удалось связаться с хостингом: `{stats.get('error')}`", color=discord.Color.red())
            return await ctx.send(embed=embed)

        state_emoji = "🟢 ЗАПУЩЕН" if stats["state"] == "running" else "🔴 ВЫКЛЮЧЕН"
        
        embed = discord.Embed(
            title="📊 Детальный статус сервера VoidPulse",
            color=0x00FFCC,
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="Состояние", value=f"**{state_emoji}**", inline=False)
        embed.add_field(name="Процессор (CPU)", value=f"`{stats['cpu']}%`", inline=True)
        embed.add_field(name="ОЗУ (RAM)", value=f"`{stats['memory']} MB`", inline=True)
        embed.add_field(name="Накопитель (Disk)", value=f"`{stats['disk']} MB`", inline=True)
        embed.add_field(name="Аптайм", value=f"`{stats['uptime']} минут`", inline=True)
        embed.set_footer(text="Pterodactyl API | NexuzHost")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MinecraftCog(bot))
