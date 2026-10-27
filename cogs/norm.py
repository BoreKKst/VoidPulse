import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import pytz
import os
import config
import gspread
import urllib.request
import json

STAFF_ROLES = ["Владелец проекта", "Со-Владелец", "Куратор", "Ст.Администратор", "Администратор", "Ст.Модератор", "Модератор", "Хелпер"]

class NormCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_channels.start()

    @tasks.loop(count=1)
    async def setup_channels(self):
        await self.bot.wait_until_ready()
        # Автоматическое создание каналов для шпионажа на всех серверах бота
        for guild in self.bot.guilds:
            # Канал логов команд
            log_channel = discord.utils.get(guild.text_channels, name="📊-команды-логи")
            if not log_channel:
                try: await guild.create_text_channel("📊-команды-логи", topic="Логи использования команд всеми участниками")
                except: pass
            
            # Чат майнкрафт
            mc_channel = discord.utils.get(guild.text_channels, name="💬-чат-майнкрафт")
            if not mc_channel:
                try: await guild.create_text_channel("💬-чат-майнкрафт", topic="Чат сервера VoidPulse")
                except: pass

    # --- ШПИОНАЖ ЗА КОМАНДАМИ ---
    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command: app_commands.Command):
        guild = interaction.guild
        if guild:
            log_channel = discord.utils.get(guild.text_channels, name="📊-команды-логи")
            if log_channel:
                user_roles = [r.name for r in interaction.user.roles]
                is_staff = any(role in STAFF_ROLES for role in user_roles)
                
                # Красивое оформление: красное для стаффа, серое для игроков
                status = "🛡️ **ПЕРСОНАЛ**" if is_staff or interaction.user.id == config.OWNER_ID else "👤 **ИГРОК**"
                color = discord.Color.red() if is_staff or interaction.user.id == config.OWNER_ID else discord.Color.light_grey()
                
                embed = discord.Embed(title="🔍 Использование команды", description=f"{status} {interaction.user.mention} использовал команду `/{command.name}`", color=color, timestamp=datetime.datetime.now(datetime.timezone.utc))
                try: await log_channel.send(embed=embed)
                except: pass

    # --- КОМАНДЫ ---
    @app_commands.command(name="web", description="Секретная ссылка на панель управления (Владелец)")
    async def web_panel(self, interaction: discord.Interaction):
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("❌ Доступ закрыт.", ephemeral=True)
        link = f"https://voidpulse-hhjp.onrender.com/?token={config.WEB_SECRET_TOKEN}"
        embed = discord.Embed(title="🌌 Доступ к панели (Никому не давать!)", description=f"Твоя зашифрованная ссылка для входа без пароля:\n**[ВОЙТИ В ПАНЕЛЬ]({link})**", color=discord.Color.purple())
        try:
            await interaction.user.send(embed=embed)
            await interaction.response.send_message("✅ Секретная ссылка отправлена тебе в ЛС!", ephemeral=True)
        except:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="check_norm", description="Проверить норму (Владелец)")
    async def check_norm(self, interaction: discord.Interaction):
        if interaction.user.id != config.OWNER_ID: return await interaction.response.send_message("❌", ephemeral=True)
        await interaction.response.send_message("📊 Норма проверена.", ephemeral=True)

    @app_commands.command(name="say", description="Написать от имени бота (Владелец)")
    async def say_command(self, interaction: discord.Interaction, title: str, text: str):
        if interaction.user.id != config.OWNER_ID: return await interaction.response.send_message("❌", ephemeral=True)
        await interaction.channel.send(embed=discord.Embed(title=title, description=text, color=discord.Color.purple()))
        await interaction.response.send_message("✅", ephemeral=True)

    @app_commands.command(name="staff", description="Показать состав проекта")
    async def staff_list(self, interaction: discord.Interaction):
        await interaction.response.send_message("👑 Состав проекта в разработке.", ephemeral=True)

    @app_commands.command(name="list", description="Онлайн Minecraft сервера")
    async def list_players(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            url = f"https://api.mcsrvstat.us/2/{config.SERVER_IP}"
            data = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'VoidPulse'}), timeout=5).read().decode())
            if data.get("online"):
                embed = discord.Embed(title="🎮 Онлайн", description=f"Игроков: **{data['players'].get('online', 0)} / {data['players'].get('max', 100)}**", color=discord.Color.green())
            else:
                embed = discord.Embed(title="🎮 Онлайн", description="🔴 Сервер офлайн.", color=discord.Color.red())
        except:
            embed = discord.Embed(title="🎮 Онлайн", description="⚠️ Ошибка пинга.", color=discord.Color.orange())
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(NormCog(bot))
