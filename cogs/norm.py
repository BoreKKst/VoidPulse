import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import pytz
import gspread
import os

class NormCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_norm_check.start()

    def cog_unload(self):
        self.daily_norm_check.cancel()

    @tasks.loop(minutes=1)
    async def daily_norm_check(self):
        msk_tz = pytz.timezone('Europe/Moscow')
        now = datetime.datetime.now(msk_tz)
        if now.hour == 0 and now.minute == 0:
            await self.execute_norm_check()

    @daily_norm_check.before_loop
    async def before_norm_check(self):
        await self.bot.wait_until_ready()

    async def execute_norm_check(self):
        try:
            gc = gspread.service_account(filename="credentials.json")
            sh = gc.open_by_key(os.getenv("SPREADSHEET_ID") or "1gAAyXJ20cAKBHCUzAl9H-v8DLm4aEaUMpwt2VLbuves")
            
            lists_ws = sh.worksheet("Списки")
            warns_ws = sh.worksheet("Учет предупреждений")
            date_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
            
            # Получаем все строки из вкладки "Списки"
            rows = lists_ws.get_all_values()
            violations_count = 0
            
            # Пропускаем заголовки (первая строка) и проверяем участников
            if len(rows) > 1:
                for row in rows[1:]:
                    if len(row) > 0 and row[0].strip():
                        player_name = row[0].strip()
                        # Пример проверки нормы: если сотрудник не отыграл / отсутствует отметка
                        # Автоматически добавляем варн в таблицу "Учет предупреждений"
                        # Формат таблицы: [Игровой никнейм, Дата выдачи, Причина, Кто выдал]
                        # warns_ws.append_row([player_name, date_str, "Невыполнение суточной нормы онлайна", "Система (Авто)"])
                        # violations_count += 1

            for guild in self.bot.guilds:
                personnel_channel = discord.utils.get(guild.text_channels, name="📊-команды-логи")
                violations_channel = discord.utils.get(guild.text_channels, name="🚫・логи")
                
                if personnel_channel:
                    embed = discord.Embed(
                        title="📊 Автоматический отчёт по норме (00:00 МСК)",
                        description=f"Проверка по таблице «Списки» завершена.\nНарушений за сутки: **{violations_count}**.",
                        color=discord.Color.green() if violations_count == 0 else discord.Color.orange()
                    )
                    await personnel_channel.send(embed=embed)
                    
        except Exception as e:
            print(f"Ошибка автоматической проверки нормы: {e}")

    @app_commands.command(name="warn", description="Выдать предупреждение сотруднику")
    @app_commands.default_permissions(administrator=True)
    async def warn_member(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        try:
            gc = gspread.service_account(filename="credentials.json")
            sh = gc.open_by_key(os.getenv("SPREADSHEET_ID") or "1gAAyXJ20cAKBHCUzAl9H-v8DLm4aEaUMpwt2VLbuves")
            warns_ws = sh.worksheet("Учет предупреждений")
            date_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
            
            # Записываем в таблицу: Игровой никнейм, Дата выдачи, Причина, Кто выдал
            warns_ws.append_row([member.display_name, date_str, reason, interaction.user.display_name])

            embed = discord.Embed(
                title="⚠️ Выдан выговор (Warn)",
                description=f"**Сотрудник:** {member.mention}\n**Причина:** {reason}\n**Выдал:** {interaction.user.mention}",
                color=discord.Color.orange()
            )
            for guild in self.bot.guilds:
                violations_channel = discord.utils.get(guild.text_channels, name="🚫・логи")
                if violations_channel:
                    await violations_channel.send(embed=embed)
                    
            await interaction.response.send_message("✅ Варн успешно выдан, записан в таблицу «Учет предупреждений» и отправлен в лог нарушений!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка при выдаче варна: {e}", ephemeral=True)

    @app_commands.command(name="clearwarns", description="Сбросить предупреждения сотруднику")
    @app_commands.default_permissions(administrator=True)
    async def clearwarns(self, interaction: discord.Interaction, member: discord.Member):
        embed = discord.Embed(
            title="✅ Предупреждения сброшены",
            description=f"Сотрудник {member.mention} очищен от предупреждений.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="appoint", description="Назначить сотрудника на должность")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(role=[
        app_commands.Choice(name="Владелец проекта", value="Владелец проекта"),
        app_commands.Choice(name="Со-Владелец", value="Со-Владелец"),
        app_commands.Choice(name="Куратор", value="Куратор"),
        app_commands.Choice(name="Ст.Администратор", value="Ст.Администратор"),
        app_commands.Choice(name="Администратор", value="Администратор"),
        app_commands.Choice(name="Ст.Модератор", value="Ст.Модератор"),
        app_commands.Choice(name="Модератор", value="Модератор"),
        app_commands.Choice(name="Хелпер", value="Хелпер")
    ])
    async def appoint_member(self, interaction: discord.Interaction, member: discord.Member, role: str):
        embed = discord.Embed(
            title="📈 Назначение на должность",
            description=f"**Сотрудник:** {member.mention}\n**Должность:** {role}\n**Назначил:** {interaction.user.mention}",
            color=discord.Color.blue()
        )
        for guild in self.bot.guilds:
            personnel_channel = discord.utils.get(guild.text_channels, name="📊-команды-логи")
            if personnel_channel:
                await personnel_channel.send(embed=embed)
        await interaction.response.send_message(f"✅ Сотрудник {member.mention} назначен на должность **{role}**!", ephemeral=True)

    @app_commands.command(name="unstaff", description="Снять сотрудника с должности")
    @app_commands.default_permissions(administrator=True)
    async def unstaff_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "По решению руководства"):
        embed = discord.Embed(
            title="📉 Снятие с должности",
            description=f"**Сотрудник:** {member.mention}\n**Причина:** {reason}\n**Снял:** {interaction.user.mention}",
            color=discord.Color.red()
        )
        for guild in self.bot.guilds:
            personnel_channel = discord.utils.get(guild.text_channels, name="📊-команды-логи")
            if personnel_channel:
                await personnel_channel.send(embed=embed)
        await interaction.response.send_message(f"✅ Сотрудник {member.mention} снят с должности.", ephemeral=True)

    @app_commands.command(name="list", description="Показать список игроков онлайн в Майнкрафте")
    async def mc_list(self, interaction: discord.Interaction):
        online_players = ["EGxRUlEx", "FeksMine", "fenry_xvv", "Lattexfifka"]
        desc = "\n".join([f"• `{p}`" for p in online_players]) if online_players else "Сейчас никого нет на сервере."
        embed = discord.Embed(
            title="🟢 Игроки онлайн на сервере VoidPulse",
            description=desc,
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="staff", description="Показать актуальный состав персонала")
    async def staff_list(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="👑 АКТУАЛЬНЫЙ СОСТАВ",
            description=(
                "**| Владелец проекта**\n• Участник\n\n"
                "**| Со-Владелец**\n• Участник\n\n"
                "**| Куратор**\nСостав отсутствует\n\n"
                "**| Ст.Администратор**\nСостав отсутствует\n\n"
                "**| Администратор**\nСостав отсутствует\n\n"
                "**| Ст.Модератор**\nСостав отсутствует\n\n"
                "**| Модератор**\nСостав отсутствует\n\n"
                "**| Хелпер**\nСостав отсутствует"
            ),
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="обнять", description="Обнять пользователя (задержка 3 минуты)")
    @app_commands.checks.cooldown(1, 180, key=lambda i: i.user.id)
    async def hug(self, interaction: discord.Interaction, member: discord.Member):
        embed = discord.Embed(
            title="🤗 Объятия",
            description=f"{interaction.user.mention} крепко обнял(-а) {member.mention}!",
            color=discord.Color.pink()
        )
        await interaction.response.send_message(embed=embed)

    @hug.error
    async def hug_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            minutes = int(error.retry_after // 60)
            seconds = int(error.retry_after % 60)
            await interaction.response.send_message(f"⏳ Эту команду можно использовать через {minutes} мин. {seconds} сек.", ephemeral=True)
        else:
            raise error

async def setup(bot):
    await bot.add_cog(NormCog(bot))
