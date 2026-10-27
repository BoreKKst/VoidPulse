import discord
from discord.ext import commands
from discord import app_commands

class MinecraftCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mc_channel_id = 1564608889398231124

    @app_commands.command(name="list", description="Показать игроков онлайн на сервере Minecraft")
    async def mc_list(self, interaction: discord.Interaction):
        players = ["EGxRUlEx", "FeksMine", "fenry_xvv", "Lattexfifka"]
        desc = "\n".join([f"• `{p}`" for p in players]) if players else "На сервере нет игроков."
        embed = discord.Embed(
            title="🟢 Онлайн сервера VoidPulse",
            description=desc,
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(MinecraftCog(bot))
