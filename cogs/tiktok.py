import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import datetime

TIKTOK_FILE = "tiktok_creators.json"

class TikTokCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chat_channel_id = 1554536535247032401
        self.creators = self.load_creators()
        self.check_tiktok.start()

    def cog_unload(self):
        self.check_tiktok.cancel()

    def load_creators(self):
        if os.path.exists(TIKTOK_FILE):
            try:
                with open(TIKTOK_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_creators(self):
        with open(TIKTOK_FILE, "w", encoding="utf-8") as f:
            json.dump(self.creators, f, ensure_ascii=False, indent=4)

    tiktok = app_commands.Group(name="tiktok", description="Отслеживание контент-мейкеров TikTok")

    @tiktok.command(name="add", description="Привязать TikTok аккаунт к пользователю Discord")
    @app_commands.default_permissions(administrator=True)
    async def tiktok_add(self, interaction: discord.Interaction, tiktok_username: str, discord_user: discord.Member):
        username = tiktok_username.strip("@").lower()
        self.creators[username] = discord_user.id
        self.save_creators()
        
        embed = discord.Embed(
            title="🎵 TikTok Аккаунт Привязан",
            color=discord.Color.brand_green(),
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="TikTok", value=f"`@{username}`", inline=True)
        embed.add_field(name="Discord", value=discord_user.mention, inline=True)
        embed.set_footer(text="VoidPulse Media System")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tiktok.command(name="remove", description="Отвязать TikTok аккаунт из системы отслеживания")
    @app_commands.default_permissions(administrator=True)
    async def tiktok_remove(self, interaction: discord.Interaction, tiktok_username: str):
        username = tiktok_username.strip("@").lower()
        if username in self.creators:
            del self.creators[username]
            self.save_creators()
            
            embed = discord.Embed(
                title="🗑️ TikTok Аккаунт Удален",
                description=f"Аккаунт **@{username}** больше не отслеживается.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Данный аккаунт не найден в базе.", ephemeral=True)

    @tasks.loop(minutes=5)
    async def check_tiktok(self):
        if not self.creators:
            return
        # Здесь будет логика проверки новых видео

    @check_tiktok.before_loop
    async def before_tiktok_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(TikTokCog(bot))
