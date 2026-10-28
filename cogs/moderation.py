import discord
from discord.ext import commands
from discord import app_commands
import datetime

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.violations_channel_id = 1564335766300004434
        self.owner_discord_id = 1374053953301385308 # Твой ID для уведомлений в ЛС

    @app_commands.command(name="mclog", description="Автоматическая фиксация нарушений и действий из Minecraft")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(action=[
        app_commands.Choice(name="Бан", value="Бан"),
        app_commands.Choice(name="Пермбан", value="Пермбан"),
        app_commands.Choice(name="Темп-бан", value="Темп-бан"),
        app_commands.Choice(name="Варн", value="Варн"),
        app_commands.Choice(name="Анварн", value="Анварн"),
        app_commands.Choice(name="Кик", value="Кик"),
        app_commands.Choice(name="Мут", value="Мут"),
        app_commands.Choice(name="Анмут", value="Анмут"),
        app_commands.Choice(name="Темп-мут", value="Темп-мут"),
        app_commands.Choice(name="GM 1 (Креатив)", value="GM 1"),
        app_commands.Choice(name="Выдача OP", value="Выдача OP"),
        app_commands.Choice(name="Снятие OP (Deop)", value="Снятие OP")
    ])
    async def mclog(self, interaction: discord.Interaction, action: str, player: str, admin: str, reason: str = "Причина не указана"):
        await interaction.response.defer(ephemeral=True)
        
        embed = discord.Embed(
            title=f"⛏️ [Minecraft Log] {action.upper()}",
            color=discord.Color.dark_purple() if "GM" not in action and "OP" not in action else discord.Color.gold(),
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="👤 Игрок / Нарушитель", value=f"`{player}`", inline=True)
        embed.add_field(name="🛡️ Исполнитель (Админ)", value=f"`{admin}`", inline=True)
        embed.add_field(name="📋 Детали / Причина", value=f"```{reason}```", inline=False)
        embed.set_footer(text="Автоматическая система контроля VoidPulse")

        # 1. Отправляем в общий канал нарушений
        ch = self.bot.get_channel(self.violations_channel_id)
        if ch:
            await ch.send(embed=embed)

        # 2. ЕСЛИ ВЫДАЛИ GM ИЛИ OP — ОТПРАВЛЯЕМ СРОЧНОЕ УВЕДОМЛЕНИЕ ТЕБЕ В ЛС ПО ТВОЕМУ ID!
        if "GM" in action or "OP" in action:
            try:
                owner_user = await self.bot.fetch_user(self.owner_discord_id)
                if owner_user:
                    dm_embed = discord.Embed(
                        title="🚨 СРОЧНОЕ УВЕДОМЛЕНИЕ ИЗ МАЙНКРАФТА",
                        description=f"Администратор `{admin}` выдал **{action}`** игроку `{player}`!",
                        color=discord.Color.red(),
                        timestamp=datetime.datetime.now()
                    )
                    dm_embed.add_field(name="Причина", value=reason, inline=False)
                    await owner_user.send(embed=dm_embed)
            except Exception as e:
                print(f"Не удалось отправить ЛС владельцу: {e}")

        await interaction.followup.send(f"✅ Действие **{action}** залогировано. Уведомления отправлены.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
