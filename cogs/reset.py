import discord
from discord.ext import commands
from discord import app_commands
import os

class ResetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reset", description="Перезапустить бота прямо из Discord")
    @app_commands.default_permissions(administrator=True)
    async def reset_bot(self, interaction: discord.Interaction):
        # Создаем файл-метку для уведомления после перезапуска
        with open("restart_queue.txt", "w") as f:
            f.write("restart")

        embed = discord.Embed(
            title="🔄 Перезапуск",
            description="⏳ Бот уходит на перезагрузку. Секунду...",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Мгновенно выключаем процесс, Render тут же включит его обратно
        os._exit(0)

async def setup(bot):
    await bot.add_cog(ResetCog(bot))
