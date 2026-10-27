import discord
from discord.ext import commands
from discord import app_commands

class SystemsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.staff_chat_id = 1564335766195404909

    @app_commands.command(name="music", description="Воспроизвести аудио по ссылке")
    async def music(self, interaction: discord.Interaction, ссылка: str):
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ Зайдите в любой голосовой канал и повторите команду.", ephemeral=True)
        
        embed = discord.Embed(
            title="🎵 Музыкальный плеер",
            description=f"**Источник:** {ссылка}\n**Статус:** Готов к трансляции",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="связаться", description="Открыть тикет обращения к администрации")
    async def ticket(self, interaction: discord.Interaction, сообщение: str):
        ch = self.bot.get_channel(self.staff_chat_id)
        embed = discord.Embed(
            title="📩 Новое обращение (Тикет)",
            description=f"**Отправлено:** {interaction.user.mention}\n**Содержание:** {сообщение}",
            color=discord.Color.gold()
        )
        if ch:
            await ch.send(embed=embed)
        try:
            await interaction.user.send("✅ Ваше обращение передано руководству. Ответ поступит в ЛС.")
            await interaction.response.send_message("✅ Тикет создан. Проверьте личные сообщения.", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Откройте ЛС для получения ответа от администрации.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SystemsCog(bot))
