import discord
from discord.ext import commands
from discord import app_commands
import time
import asyncio

SECRET_PLUGIN_KEY = "VP_SECURE_KEY_9921_X"

class AuthVerificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verify_channel_id = 1564693207869038632
        self.verified_role_id = 1564692728996958269
        self.main_channel_id = 1554536535247032401
        
        # Хранилище временных кодов от плагина: { "CODE123": {"mc_nick": "Steve", "expires": timestamp} }
        self.pending_mc_codes = {}
        # Запомненные игроки (однократная проверка)
        self.verified_players = set()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.channel.id != self.verify_channel_id:
            return

        user_code = message.content.strip().upper()
        
        # Мгновенно удаляем сообщение с кодом из чата
        try:
            await message.delete()
        except Exception:
            pass

        now = time.time()
        
        # Проверяем, есть ли такой код и не истекли ли 5 минут (300 сек)
        if user_code in self.pending_mc_codes:
            data = self.pending_mc_codes[user_code]
            if now <= data["expires"]:
                mc_nick = data["mc_nick"]
                self.verified_players.add(mc_nick)
                del self.pending_mc_codes[user_code]

                # Выдаем роль "Проверен на бота"
                role = message.guild.get_role(self.verified_role_id)
                if role:
                    await message.author.add_roles(role)

                msg = await message.channel.send(
                    f"✅ {message.author.mention}, код подтвержден! Игрок `{mc_nick}` успешно прошёл 2FA верификацию. Роль выдана!",
                    delete_after=7
                )
                print(f"[2FA SUCCESS] Игрок {mc_nick} верифицирован через Discord пользователя {message.author}")
            else:
                del self.pending_mc_codes[user_code]
                await message.channel.send(f"❌ {message.author.mention}, время действия кода (5 минут) истекло! Войдите в игру заново.", delete_after=5)
        else:
            await message.channel.send(f"❌ {message.author.mention}, неверный или устаревший код верификации!", delete_after=5)

    # API Эндпоинт для приема кода от Minecraft плагина
    async def register_mc_code(self, secret_key: str, mc_nick: str, code: str):
        if secret_key != SECRET_PLUGIN_KEY:
            return False, "Invalid Secret Key"
        
        # Сохраняем код ровно на 5 минут (300 секунд)
        self.pending_mc_codes[code.upper()] = {
            "mc_nick": mc_nick,
            "expires": time.time() + 300
        }
        return True, "Code registered for 5 minutes"

async def setup(bot):
    await bot.add_cog(AuthVerificationCog(bot))
