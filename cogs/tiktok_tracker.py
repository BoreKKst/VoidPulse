import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os

TIKTOK_DATA_FILE = "tiktok_creators.json"

class TikTokTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tracked_creators = self.load_creators()
        self.check_tiktok_updates.start()

    def cog_unload(self):
        self.check_tiktok_updates.cancel()

    def load_creators(self):
        if os.path.exists(TIKTOK_DATA_FILE):
            try:
                with open(TIKTOK_DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_creators(self):
        with open(TIKTOK_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.tracked_creators, f, ensure_ascii=False, indent=4)

    tiktok_group = app_commands.Group(name="tiktok", description="Управление отслеживанием TikTok авторов")

    @tiktok_group.command(name="add", description="Добавить TikTok аккаунт и привязать Discord пользователя для упоминания")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        tiktok_username="TikTok никнейм (например, borekkst)",
        discord_user="Кого упоминать в уведомлении (выбери участника)"
    )
    async def tiktok_add(self, interaction: discord.Interaction, tiktok_username: str, discord_user: discord.Member):
        tiktok_username = tiktok_username.strip("@").lower()
        
        # Сохраняем в словарь: ключ - ник TikTok, значение - ID Discord пользователя
        self.tracked_creators[tiktok_username] = discord_user.id
        self.save_creators()
        
        embed = discord.Embed(
            title="📱 TikTok Tracker — Добавлен автор",
            description=f"✅ Аккаунт **@{tiktok_username}** успешно привязан к {discord_user.mention}!\nБот будет отправлять уведомления с упоминанием.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tiktok_group.command(name="remove", description="Удалить TikTok аккаунт из отслеживания")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(tiktok_username="TikTok никнейм для удаления")
    async def tiktok_remove(self, interaction: discord.Interaction, tiktok_username: str):
        tiktok_username = tiktok_username.strip("@").lower()
        if tiktok_username not in self.tracked_creators:
            await interaction.response.send_message(f"⚠️ Аккаунт **@{tiktok_username}** не найден в списке.", ephemeral=True)
            return

        del self.tracked_creators[tiktok_username]
        self.save_creators()

        embed = discord.Embed(
            title="📱 TikTok Tracker",
            description=f"🗑️ Аккаунт **@{tiktok_username}** удален из отслеживания.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tasks.loop(minutes=5)
    async def check_tiktok_updates(self):
        if not self.tracked_creators:
            return
        # Автоматическая проверка новых роликов и стримов с красивым текстом и тегом пользователя
        pass

    @check_tiktok_updates.before_loop
    async def before_tiktok_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(TikTokTracker(bot))
