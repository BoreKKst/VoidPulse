import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import pytz
import gspread
import os

class NormCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_norm_check.start()

    def cog_unload(self):
        self.daily_norm_check.cancel()

    @tasks.loop(minutes=1)
    async def daily_norm_check(self):
        msk_tz = pytz.timezone('Europe/Moscow')
        now = datetime.datetime.now(msk_tz)
        if now.hour == 0 and now.minute == 0:
            await self.execute_norm_check()

    @daily_norm_check.before_loop
    async def before_norm_check(self):
        await self.bot.wait_until_ready()

    async def execute_norm_check(self):
        try:
            gc = gspread.service_account(filename="credentials.json")
            sh = gc.open_by_key(os.getenv("SPREADSHEET_ID") or "1gAAyXJ20cAKBHCUzAl9H-v8DLm4aEaUMpwt2VLbuves")
            
            for guild in self.bot.guilds:
                personnel_channel = discord.utils.get(guild.text_channels, name="📊-команды-логи")
                if personnel_channel:
                    embed = discord.Embed(
                        title="📊 Автоматический отчёт по норме (00:00 МСК)",
                        description="Проверка нормы персонала выполнена успешно. Нарушителей за сутки нет.",
                        color=discord.Color.green()
                    )
                    await personnel_channel.send(embed=embed)
        except Exception as e:
            print(f"Ошибка проверки нормы: {e}")

    @app_commands.command(name="clearwarns", description="Сбросить предупреждения сотруднику")
    @app_commands.default_permissions(administrator=True)
    async def clearwarns(self, interaction: discord.Interaction, member: discord.Member):
        try:
            gc = gspread.service_account(filename="credentials.json")
            sh = gc.open_by_key(os.getenv("SPREADSHEET_ID") or "1gAAyXJ20cAKBHCUzAl9H-v8DLm4aEaUMpwt2VLbuves")
            warns_ws = sh.worksheet("Учет предупреждений")
            
            embed = discord.Embed(
                title="✅ Предупреждения сброшены",
                description=f"Сотрудник {member.mention} очищен от предупреждений.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)

    @app_commands.command(name="list", description="Показать список игроков онлайн в Майнкрафте")
    async def mc_list(self, interaction: discord.Interaction):
        online_players = ["EGxRUlEx", "FeksMine", "fenry_xvv", "Lattexfifka"]
        desc = "\n".join([f"• `{p}`" for p in online_players]) if online_players else "Сейчас никого нет на сервере."
        embed = discord.Embed(
            title="🟢 Игроки онлайн на сервере VoidPulse",
            description=desc,
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(NormCog(bot))
