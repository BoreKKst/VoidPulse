import discord
from discord.ext import commands
from discord import app_commands
import random
import string
import asyncio

class AuthVerificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verify_channel_id = 1564693207869038632
        self.verified_role_id = 1564692728996958269
        self.active_codes = {}  # {user_id: "code"}

    @app_commands.command(name="verify", description="Получить код верификации в ЛС")
    async def get_verify_code(self, interaction: discord.Interaction):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        self.active_codes[interaction.user.id] = code
        try:
            await interaction.user.send(f"🔐 Твой код подтверждения: `{code}`\nВведи его в канале <#{self.verify_channel_id}>!")
            await interaction.response.send_message("✅ Код отправлен тебе в ЛС!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Открой личные сообщения!", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.channel.id != self.verify_channel_id:
            return

        user_code = message.content.strip()
        user_id = message.author.id

        # Мгновенно удаляем введенный код, чтобы его никто не видел
        try:
            await message.delete()
        except Exception:
            pass

        if user_id in self.active_codes and user_code == self.active_codes[user_id]:
            del self.active_codes[user_id]
            role = message.guild.get_role(self.verified_role_id)
            if role:
                await message.author.add_roles(role)
                msg = await message.channel.send(f"✅ {message.author.mention}, верификация успешна! Роль выдана.")
            else:
                msg = await message.channel.send(f"⚠️ {message.author.mention}, код верный, но роль не найдена.")
            await asyncio.sleep(4)
            await msg.delete()
        else:
            msg = await message.channel.send(f"❌ {message.author.mention}, неверный код или вы не получали код через `/verify`!", delete_after=4)

async def setup(bot):
    await bot.add_cog(AuthVerificationCog(bot))
