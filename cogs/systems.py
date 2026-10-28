import discord
from discord.ext import commands
from discord import app_commands
import datetime

class SystemsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.staff_chat_id = 1564335766195404909

    @app_commands.command(name="music", description="Воспроизвести аудио по ссылке")
    async def music(self, interaction: discord.Interaction, ссылка: str):
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ Ошибка: Зайдите в любой голосовой канал.", ephemeral=True)

        embed = discord.Embed(
            title="🎵 Музыкальный плеер VoidPulse",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="Статус", value="🟢 Инициализация потока", inline=False)
        embed.add_field(name="Источник", value=f"`{ссылка}`", inline=False)
        embed.set_footer(text=f"Запросил: {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="связаться", description="Открыть тикет обращения к администрации")
    async def ticket(self, interaction: discord.Interaction, сообщение: str):
        ch = self.bot.get_channel(self.staff_chat_id)
        
        embed = discord.Embed(
            title="📩 Входящее обращение",
            description=f"```{сообщение}```",
            color=discord.Color.gold(),
            timestamp=datetime.datetime.now()
        )
        embed.set_author(name=f"От: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="Профиль", value=interaction.user.mention, inline=True)
        embed.add_field(name="ID пользователя", value=f"`{interaction.user.id}`", inline=True)
        embed.set_footer(text="VoidPulse Ticket System")

        if ch:
            await ch.send(embed=embed)
            
        try:
            user_embed = discord.Embed(
                title="✅ Обращение доставлено", 
                description="Ваш тикет передан руководству проекта. Ожидайте ответа в личных сообщениях.",
                color=discord.Color.green()
            )
            await interaction.user.send(embed=user_embed)
            await interaction.response.send_message("✅ Тикет успешно создан и отправлен.", ephemeral=True)
        except:
            await interaction.response.send_message("⚠️ Тикет отправлен, но мы не смогли прислать уведомление в ЛС (Личные сообщения закрыты).", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SystemsCog(bot))
