import discord
from discord.ext import commands
import time
import asyncio

SECRET_PLUGIN_KEY = "VP_SECURE_KEY_9921_X"

class AuthVerificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verify_channel_id = 1564693207869038632
        self.verified_role_id = 1564692728996958269
        self.pending_mc_codes = {}
        self.verified_players = set()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.channel.id != self.verify_channel_id:
            return

        user_code = message.content.strip().upper()
        try:
            await message.delete()
        except Exception:
            pass

        now = time.time()
        if user_code in self.pending_mc_codes:
            data = self.pending_mc_codes[user_code]
            if now <= data["expires"]:
                mc_nick = data["mc_nick"]
                self.verified_players.add(mc_nick.lower())
                del self.pending_mc_codes[user_code]

                role = message.guild.get_role(self.verified_role_id)
                if role:
                    await message.author.add_roles(role)

                msg = await message.channel.send(
                    f"✅ {message.author.mention}, код верный! Игрок `{mc_nick}` верифицирован.",
                    delete_after=7
                )
            else:
                del self.pending_mc_codes[user_code]
                await message.channel.send(f"❌ {message.author.mention}, код истек!", delete_after=5)
        else:
            await message.channel.send(f"❌ {message.author.mention}, неверный код!", delete_after=5)

    async def register_mc_code(self, secret_key: str, mc_nick: str, code: str):
        if secret_key != SECRET_PLUGIN_KEY:
            return False, "Invalid Secret Key"
        self.pending_mc_codes[code.upper()] = {
            "mc_nick": mc_nick,
            "expires": time.time() + 300
        }
        return True, "Code registered"

    def check_player_verified(self, secret_key: str, mc_nick: str):
        if secret_key != SECRET_PLUGIN_KEY or not mc_nick:
            return False
        return mc_nick.lower() in self.verified_players

async def setup(bot):
    await bot.add_cog(AuthVerificationCog(bot))
