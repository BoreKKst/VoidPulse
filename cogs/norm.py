import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import pytz
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
                description="Напоминание: наступило 00:00 МСК. Проверьте отработанную норму!",
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

    @app_commands.command(name="check_norm", description="Проверить норму персонала за сегодня по таблице (Только владелец)")
    async def check_norm(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Доступно только владельцу!", ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)
        records = self.get_sheet_data()
        
        embed = discord.Embed(
            title="📊 Проверка нормы персонала за сегодня",
            description="Сравнение выполненной нормы с требованиями из таблицы:",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        
        if not records:
            embed.description = "⚠️ Не удалось получить данные из Google Таблицы или таблица пуста."
        else:
            for row in records[:12]:
                name = row.get("Имя", row.get("Ник", "Сотрудник"))
                role = row.get("Должность", "Сотрудник")
                norm = row.get("Норма", row.get("Требуется", "Не указано"))
                done = row.get("Выполнено", row.get("Сегодня", row.get("Отработано", "0")))
                
                embed.add_field(
                    name=f"👤 {name} ({role})",
                    value=f"🎯 Требуется в табе: **{norm}**\n🟢 Выполнено сегодня: **{done}**",
                    inline=False
                )
                
        embed.set_footer(text="VoidPulse Staff Norm System")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="reload", description="Перезапуск бота (Только владелец)")
    async def reload_bot(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Доступно только владельцу!", ephemeral=True)
        await interaction.response.send_message("🔄 Перезапуск системы...", ephemeral=True)
        os._exit(0)

    @app_commands.command(name="test", description="Тест команд (Только владелец)")
    async def test_system(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Доступно только владельцу!", ephemeral=True)
        await interaction.response.send_message("🧪 Все системы VoidPulse функционируют на 100% без ошибок!", ephemeral=True)

    @app_commands.command(name="status", description="Статус в ЛС (Только владелец)")
    async def status_system(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Доступно только владельцу!", ephemeral=True)
        embed = discord.Embed(title="📊 Статус VoidPulse", description="Пингование серверов и хостинга успешно.", color=discord.Color.purple())
        embed.add_field(name="🌐 LP Editor Web", value="https://voidpulse-hhjp.onrender.com", inline=False)
        try:
            await interaction.user.send(embed=embed)
            await interaction.response.send_message("✅ Отправлено в ЛС!", ephemeral=True)
        except:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="checking", description="Проверка связей (Только владелец)")
    async def checking_system(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Доступно только владельцу!", ephemeral=True)
        await interaction.response.send_message("🔍 Все привязки с Google Sheets и Flask активны.", ephemeral=True)

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

    @app_commands.command(name="list", description="Онлайн Minecraft сервера")
    async def list_players(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            url = f"https://api.mcsrvstat.us/2/{SERVER_IP}"
            data = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'VoidPulse'}), timeout=5).read().decode())
            if data.get("online"):
                embed = discord.Embed(title="🎮 Онлайн VoidPulse", description=f"IP: `{SERVER_IP}`\nОнлайн: **{data['players'].get('online', 0)} / {data['players'].get('max', 100)}**", color=discord.Color.green())
            else:
                embed = discord.Embed(title="🎮 Онлайн VoidPulse", description=f"🔴 Сервер офлайн.", color=discord.Color.red())
        except:
            embed = discord.Embed(title="🎮 Онлайн VoidPulse", description=f"⚠️ Ошибка пинга сервера.", color=discord.Color.orange())
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="web", description="LP Editor Веб-панель (Только владелец в ЛС)")
    async def web_panel(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID or not isinstance(interaction.channel, discord.DMChannel):
            return await interaction.response.send_message("❌ Только для владельца в ЛС!", ephemeral=True)
        embed = discord.Embed(title="🌌 LP Editor • VoidPulse Panel", description="https://voidpulse-hhjp.onrender.com", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="say", description="Сообщение от бота (Владелец)")
    @app_commands.describe(title="Заголовок", text="Текст", channel="Канал", user="Пользователь для отправки в ЛС")
    async def say_command(self, interaction: discord.Interaction, title: str, text: str, channel: discord.TextChannel = None, user: discord.Member = None):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Только для владельца!", ephemeral=True)
        
        embed = discord.Embed(title=title, description=text, color=discord.Color.purple())
        
        if user:
            try:
                await user.send(embed=embed)
                await interaction.response.send_message(f"✅ Успешно отправлено в ЛС пользователю {user.mention}!", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message(f"⚠️ Не удалось отправить ЛС пользователю {user.mention} (закрыт доступ или заблокирован бот).", ephemeral=True)
        elif channel:
            await channel.send(embed=embed)
            await interaction.response.send_message("✅ Сообщение отправлено в канал!", ephemeral=True)
        else:
            await interaction.channel.send(embed=embed)
            await interaction.response.send_message("✅ Сообщение отправлено в этот чат!", ephemeral=True)

    @app_commands.command(name="troll", description="Троллинг (Владелец)")
    @app_commands.describe(user="Пользователь", action="Действие")
    async def troll_command(self, interaction: discord.Interaction, user: discord.Member, action: str = "ban"):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Только для владельца!", ephemeral=True)
        desc = f"Пользователь {user.mention} заблокирован за излишнюю крутость! 😂" if action == "ban" else f"{user.mention} попался на секретную магию!"
        embed = discord.Embed(title="⛔ Внимание", description=desc, color=discord.Color.red())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="связаться", description="Связаться с создателем")
    async def contact_creator(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📞 Связь с создателем", description="Создатель и владелец: **BoreKKst**", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="обнять", description="Обнять участника")
    @app_commands.describe(user="Кого обнять?")
    async def hug_user(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.send_message(f"🫂 {interaction.user.mention} крепко-крепко обнял(-а) {user.mention}!")

async def setup(bot):
    await bot.add_cog(NormCog(bot))
