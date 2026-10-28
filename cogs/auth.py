import discord
from discord.ext import commands
import time
import asyncio
import os
from aiohttp import web

# Новый безопасный ключ
SECRET_PLUGIN_KEY = "VP_SECURE_KEY_7749_BETA_SECURE"

class AuthVerificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verify_channel_id = 1564693207869038632
        self.verified_role_id = 1564692728996958269
        # Структура сессий: { "SESSION_UUID": {"code": "2GD239", "mc_nick": "steve", "expires": timestamp, "verified": False} }
        self.sessions = {}
        self.runner = None
        
        # Запускаем локальный веб-сервер для связи с плагином на NexuzHost
        self.bot.loop.create_task(self.start_web_server())

    async def start_web_server(self):
        app = web.Application()
        app.router.add_post('/api/register', self.handle_register_api)
        app.router.add_post('/api/check', self.handle_check_api)
        
        # Render автоматически выделяет порт через переменные окружения
        port = int(os.environ.get("PORT", 8080))
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, '0.0.0.0', port)
        try:
            await site.start()
            print(f"✅ [API SERVER] Веб-сервер для связи с плагином успешно запущен на порту {port}")
        except Exception as e:
            print(f"❌ [API SERVER ERROR] Не удалось запустить веб-сервер: {e}")

    def cog_unload(self):
        if self.runner:
            self.bot.loop.create_task(self.runner.cleanup())

    async def handle_register_api(self, request):
        try:
            data = await request.json()
            secret = data.get("secret_key")
            mc_nick = data.get("mc_nick")
            code = data.get("code")
            session_id = data.get("session_id")

            success, message = await self.register_mc_session(secret, mc_nick, code, session_id)
            if success:
                return web.json_response({"status": "success", "message": message})
            else:
                return web.json_response({"status": "error", "message": message}, status=400)
        except Exception as e:
            return web.json_response({"status": "error", "message": str(e)}, status=500)

    async def handle_check_api(self, request):
        try:
            data = await request.json()
            secret = data.get("secret_key")
            mc_nick = data.get("mc_nick")
            code = data.get("code")
            session_id = data.get("session_id")

            success, status_code = self.atomic_consume_session(secret, mc_nick, code, session_id)
            return web.json_response({"success": success, "code": status_code})
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)}, status=500)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.channel.id != self.verify_channel_id:
            return

        user_code = message.content.strip().upper()
        
        # Мгновенно удаляем сообщение из чата ради безопасности
        try:
            await message.delete()
        except Exception:
            pass

        now = time.time()
        matched_session = None

        # Ищем активную сессию по введенному коду
        for sid, data in self.sessions.items():
            if data["code"] == user_code and now <= data["expires"] and not data["verified"]:
                matched_session = data
                matched_session["sid"] = sid
                break

        if matched_session:
            matched_session["verified"] = True
            mc_nick = matched_session["mc_nick"]

            # Безопасная выдача роли (ошибка API не должна ломать логику доступа)
            try:
                role = message.guild.get_role(self.verified_role_id)
                if role:
                    await message.author.add_roles(role)
            except Exception as e:
                print(f"[DISCORD API ERROR] Не удалось выдать роль: {e}")

            await message.channel.send(
                f"✅ {message.author.mention}, код подтвержден! Игрок `{mc_nick}` авторизован.",
                delete_after=7
            )
        else:
            await message.channel.send(f"❌ {message.author.mention}, неверный или просроченный код!", delete_after=5)

    async def register_mc_session(self, secret_key: str, mc_nick: str, code: str, session_id: str):
        if secret_key != SECRET_PLUGIN_KEY or not mc_nick or not code or not session_id:
            return False, "Invalid parameters or secret key"
        
        # Очищаем старые сессии этого же игрока, чтобы исключить мусор
        expired_keys = [sid for sid, d in self.sessions.items() if d["mc_nick"] == mc_nick.lower() or time.time() > d["expires"]]
        for k in expired_keys:
            self.sessions.pop(k, None)

        # Создаем новую уникальную сессию на 5 минут (300 сек)
        self.sessions[session_id] = {
            "code": code.upper(),
            "mc_nick": mc_nick.lower(),
            "expires": time.time() + 300,
            "verified": False
        }
        return True, "Session registered"

    def atomic_consume_session(self, secret_key: str, mc_nick: str, code: str, session_id: str):
        if secret_key != SECRET_PLUGIN_KEY or not session_id or session_id not in self.sessions:
            return False, "NOT_FOUND"

        session = self.sessions[session_id]
        now = time.time()

        # Проверка таймаута (5 минут)
        if now > session["expires"]:
            self.sessions.pop(session_id, None)
            return False, "EXPIRED"

        # Строгая сверка никнейма и кода
        if session["mc_nick"] != mc_nick.lower() or session["code"] != code.upper():
            return False, "MISMATCH"

        # Атомарное подтверждение: проверяем и СРАЗУ удаляем сессию (сжигаем навсегда)
        if session["verified"]:
            self.sessions.pop(session_id, None)
            return True, "APPROVED"

        return False, "PENDING"

async def setup(bot):
    await bot.add_cog(AuthVerificationCog(bot))
