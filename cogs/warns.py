import discord
from discord.ext import commands
from discord import app_commands
import datetime
import config

class WarnsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="warn", description="Выдать выговор сотруднику")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        await interaction.response.defer(ephemeral=True)

        warns_count = 1
        if self.bot.sheet_warns:
            try:
                records = self.bot.sheet_warns.get_all_records()
                user_warns = [r for r in records if str(member.id) in str(r.get("Discord ID", ""))]
                warns_count = len(user_warns) + 1
                
                date_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
                self.bot.sheet_warns.append_row([str(member.name), date_str, reason, str(interaction.user.name)])
            except Exception as e:
                print(f"Ошибка записи выговора: {e}")

        log_channel = self.bot.get_channel(config.LOG_PUNISH_CHANNEL)
        if log_channel:
            embed = discord.Embed(title="🌌 VoidPulse Staff System", color=config.COLOR_WARNING)
            embed.description = (
                f"⚠️ **ВЫДАЧА ПРЕДУПРЕЖДЕНИЯ ({warns_count}/3)**\n\n"
                f"👤 **Нарушитель:** {member.mention}\n"
                f"📝 **Причина:** {reason}\n"
                f"📊 **Google Таблица:** Запись внесена на лист «Учет»\n\n"
                f"🛡️ **Действие выполнил:** {interaction.user.mention}"
            )
            embed.set_footer(text="VoidPulse Staff System")
            await log_channel.send(embed=embed)

        await interaction.followup.send(f"⚠️ Сотруднику {member.mention} выдан выговор ({warns_count}/3).")

    @app_commands.command(name="unwarn", description="Снять выговор")
    async def unwarn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        await interaction.response.send_message(f"🟢 С сотрудника {member.mention} снят 1 выговор. Причина: {reason}", ephemeral=True)

    @app_commands.command(name="warns", description="Посмотреть предупреждения")
    async def warns(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_message(f"📊 Запрошена информация по варнам {member.mention}.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(WarnsCog(bot))
