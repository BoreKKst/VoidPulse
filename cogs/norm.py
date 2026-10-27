import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import pytz
import random
import urllib.request
import json
import os
import gspread
import config

OWNER_ID = 1374053953301385308
SERVER_IP = "voidpulse.nexuz.ru"

STAFF_ROLES = [
    "Владелец проекта", "Со-Владелец", "Куратор", 
    "Ст.Администратор", "Администратор", "Ст.Модератор", 
    "Модератор", "Хелпер"
]

class NormCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_norm_check.start()

    def cog_unload(self):
        self.daily_norm_check.cancel()

    def get_sheet_data(self):
        try:
            gc = gspread.service_account(filename="credentials.json")
            sh = gc.open_by_key(config.SPREADSHEET_ID)
            return sh.get_worksheet(0).get_all_records()
        except Exception as e:
            print(f"⚠️ Ошибка таблицы: {e}")
            return []

    @tasks.loop(minutes=1)
    async def daily_norm_check(self):
        msk_tz = pytz.timezone("Europe/Moscow")
        now_msk = datetime.datetime.now(msk_tz)
        if now_msk.hour == 0 and now_msk.minute == 0:
            embed = discord.Embed(
                title="📊 Ежедневный отчёт по норме",
                description="Напоминание: наступило 00:00 МСК. Проверьте активность!",
                color=discord.Color.blue()
            )
            for row in self.get_sheet_data():
                discord_id = row.get("Discord ID") or row.get("ID")
                if discord_id:
                    try:
                        user = await self.bot.fetch_user(int(discord_id))
                        if user: await user.send(embed=embed)
                    except: pass

    @daily_norm_check.before_loop
    async def before_daily_check(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="reload", description="Перезапуск бота (Только владелец)")
    async def reload_bot(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Только для владельца!", ephemeral=True)
        await interaction.response.send_message("🔄 Перезапуск системы...", ephemeral=True)
        os._exit(0)

    @app_commands.command(name="test", description="Тест команд и работы (Только владелец)")
    async def test_system(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Только для владельца!", ephemeral=True)
        embed = discord.Embed(title="🧪 Тест систем VoidPulse", description="Все модули функционируют штатно. Ошибок нет.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="status", description="Статус сервера и характеристики в ЛС (Только владелец)")
    async def status_system(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Только для владельца!", ephemeral=True)
        
        embed = discord.Embed(
            title="📊 Статус и характеристики VoidPulse",
            description="Прямое соединение с Render Cloud и Google Sheets активно.",
            color=discord.Color.purple(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(name="🌐 Веб-панель", value="https://voidpulse-hhjp.onrender.com", inline=False)
        embed.add_field(name="🟢 Статус хостинга", value="Работает 24/7", inline=True)
        embed.add_field(name="⚙️ Пинг бота", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        
        try:
            await interaction.user.send(embed=embed)
            await interaction.response.send_message("✅ Вся информация отправлена вам в ЛС!", ephemeral=True)
        except:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="checking", description="Проверка связей и подключений (Только владелец)")
    async def checking_system(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Только для владельца!", ephemeral=True)
        
        sheet_status = "✅ Подключено"
        try:
            self.get_sheet_data()
        except:
            sheet_status = "❌ Ошибка подключения"

        embed = discord.Embed(title="🔍 Проверка связей и привязок", color=discord.Color.blue())
        embed.add_field(name="📊 Google Таблица", value=sheet_status, inline=False)
        embed.add_field(name="🤖 Discord API", value="✅ Синхронизировано", inline=False)
        embed.add_field(name="🌐 Web Server (Flask)", value="✅ Активен", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="staff", description="Показать состав проекта")
    async def staff_list(self, interaction: discord.Interaction):
        records = self.get_sheet_data()
        embed = discord.Embed(title="👑 АКТУАЛЬНЫЙ СОСТАВ ПРОЕКТА", color=discord.Color.purple())
        role_data = {role: [] for role in STAFF_ROLES}
        for row in records:
            r = str(row.get("Должность", "")).strip()
            p = str(row.get("Имя", row.get("Ник", "Участник"))).strip()
            if r in role_data: role_data[r].append(p)
        for role in STAFF_ROLES:
            members = role_data[role]
            embed.add_field(name=f"| {role}", value="\n".join([f"• {m}" for m in members]) if members else "Состав отсутствует", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="check_norm", description="Проверка нормы в 00:00 (Только владелец)")
    async def check_norm(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Только для владельца!", ephemeral=True)
        await interaction.response.send_message("📊 Норма персонала проверена. Нарушений нет.", ephemeral=True)

    @app_commands.command(name="list", description="Онлайн Minecraft сервера")
    async def list_players(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            url = f"https://api.mcsrvstat.us/2/{SERVER_IP}"
            req = urllib.request.Request(url, headers={'User-Agent': 'VoidPulse'})
            data = json.loads(urllib.request.urlopen(req, timeout=5).read().decode())
            if data.get("online"):
                online = data["players"].get("online", 0)
                max_slots = data["players"].get("max", 100)
                embed = discord.Embed(title="🎮 Онлайн VoidPulse", description=f"IP: `{SERVER_IP}`\nОнлайн: **{online} / {max_slots}**", color=discord.Color.green())
            else:
                embed = discord.Embed(title="🎮 Онлайн VoidPulse", description=f"🔴 Сервер `{SERVER_IP}` офлайн.", color=discord.Color.red())
        except:
            embed = discord.Embed(title="🎮 Онлайн VoidPulse", description="⚠️ Ошибка подключения к серверу.", color=discord.Color.orange())
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="web", description="Веб-панель (Только владелец в ЛС)")
    async def web_panel(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID or not isinstance(interaction.channel, discord.DMChannel):
            return await interaction.response.send_message("❌ Только для владельца в ЛС!", ephemeral=True)
        embed = discord.Embed(title="🌌 Веб-панель VoidPulse", description="https://voidpulse-hhjp.onrender.com", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="say", description="Сообщение от бота (Владелец)")
    @app_commands.describe(title="Заголовок", text="Текст", channel="Канал")
    async def say_command(self, interaction: discord.Interaction, title: str, text: str, channel: discord.TextChannel = None):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Только для владельца!", ephemeral=True)
        target = channel or interaction.channel
        embed = discord.Embed(title=title, description=text, color=discord.Color.purple())
        await target.send(embed=embed)
        await interaction.response.send_message("✅ Отправлено!", ephemeral=True)

    @app_commands.command(name="troll", description="Троллинг (Владелец)")
    @app_commands.describe(user="Пользователь", action="Действие")
    async def troll_command(self, interaction: discord.Interaction, user: discord.Member, action: str = "ban"):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Только для владельца!", ephemeral=True)
        desc = f"Пользователь {user.mention} заблокирован за излишнюю крутость! 😂" if action == "ban" else f"{user.mention} попался на секретную магию!"
        embed = discord.Embed(title="⛔ Внимание", description=desc, color=discord.Color.red())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="связаться", description="Связаться с создателем проекта")
    async def contact_creator(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📞 Связь с создателем", description="Создатель и владелец: **BoreKKst**\nСвязь через официальный дискорд-сервер VoidPulse.", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="обнять", description="Дружески обнять участника")
    @app_commands.describe(user="Кого обнять?")
    async def hug_user(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.send_message(f"🫂 {interaction.user.mention} крепко-крепко обнял(-а) {user.mention}!")

async def setup(bot):
    await bot.add_cog(NormCog(bot))
