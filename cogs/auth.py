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
        # Структура: { "CODE123": {"mc_nick": "steve", "expires": timestamp, "verified": False} }
        self.active_sessions = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.channel.id != self.verify_channel_id:
            return

        user_code = message.content.strip().upper()
        
        # Мгновенно удаляем сообщение с кодом
        try:
            await message.delete()
        except Exception:
            pass

        now = time.time()
        
        if user_code in self.active_sessions:
            session = self.active_sessions[user_code]
            if now <= session["expires"]:
                mc_nick = session["mc_nick"]
                session["verified"] = True  # Метим как подтвержденный для данного кода

                role = message.guild.get_role(self.verified_role_id)
                if role:
                    await message.author.add_roles(role)

                await message.channel.send(
                    f"✅ {message.author.mention}, код `{user_code}` подтвержден! Игрок `{mc_nick}` авторизован в игре.",
                    delete_after=7
                )
            else:
                del self.active_sessions[user_code]
                await message.channel.send(f"❌ {message.author.mention}, время действия кода (5 мин) истекло!", delete_after=5)
        else:
            await message.channel.send(f"❌ {message.author.mention}, неверный или устаревший код!", delete_after=5)

    async def register_mc_code(self, secret_key: str, mc_nick: str, code: str):
        if secret_key != SECRET_PLUGIN_KEY or not mc_nick or not code:
            return False, "Invalid parameters or secret key"
        
        # Регистрируем одноразовый сессионный код на 5 минут
        self.active_sessions[code.upper()] = {
            "mc_nick": mc_nick.lower(),
            "expires": time.time() + 300,
            "verified": False
        }
        return True, "Code registered"

    def check_and_consume_2fa(self, secret_key: str, mc_nick: str, code: str):
        if secret_key != SECRET_PLUGIN_KEY or not mc_nick or not code:
            return False, "INVALID_KEY"

        code_upper = code.upper()
        nick_lower = mc_nick.lower()
        now = time.time()

        if code_upper in self.active_sessions:
            session = self.active_sessions[code_upper]
            if session["mc_nick"] == nick_lower:
                if now > session["expires"]:
                    del self.active_sessions[code_upper]
                    return False, "EXPIRED"

                if session["verified"]:
                    # Одноразовое использование: подлинник подтвержден -> сжигаем сессию!
                    del self.active_sessions[code_upper]
                    return True, "APPROVED"
                else:
                    return False, "PENDING"

        return False, "NOT_FOUND"

async def setup(bot):
    await bot.add_cog(AuthVerificationCog(bot))
