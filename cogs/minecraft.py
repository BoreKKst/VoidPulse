import discord
from discord.ext import commands
import aiohttp

PTERODACTYL_URL = "https://mgr.nexuz.ru"
PTERODACTYL_API_KEY = "ptlc_QtgAFmPZIJkzphp2zCRO4NXGeUklm2vE2t9UrFb64lS"
SERVER_UUID = "83bed7ed-4ec5-4a51-ba0a-ed705961a66a"

class MinecraftCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
