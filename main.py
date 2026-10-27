import discord
from discord.ext import commands
import os

# Подтягиваем токен: проверяем и TOKEN, и DISCORD_TOKEN
token = os.getenv("TOKEN") or os.getenv("DISCORD_TOKEN")

if not token:
    print("❌ ОШИБКА: Токен не найден в переменных окружения Render!")

class VoidPulseBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
        self.allowed_channels = [
            1564335765054300322, 1554536535247032401, 1564608886974058528, 
            1564335766195404910, 1564608889398231124, 1564335766300004433, 
            1564335766300004434, 1564335766195404909
        ]

    async def setup_hook(self):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
        await self.tree.sync()

    async def on_guild_join(self, guild):
        channel_ids = [c.id for c in guild.channels]
        if not any(cid in self.allowed_channels for cid in channel_ids):
            await guild.leave()

bot = VoidPulseBot()
if token:
    bot.run(token)
