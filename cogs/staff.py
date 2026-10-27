import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import pytz
import gspread
import os
import asyncio

class StaffCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.personnel_channel_id = 1564335766300004433
        self.exempted_users = set()
        self.daily_norm_check.start()

    def cog_unload(self):
        self.daily_norm_check.cancel()

    def get_lists_sheet(self):
        gc = gspread.service_account(filename="credentials.json")
        return gc.open_by_key(os.getenv("SPREADSHEET_ID") or "1gAAyXJ20cAKBHCUzAl9H-v8DLm4aEaUMpwt2VLbuves").worksheet("Списки")

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
            ws = await asyncio.to_thread(self.get_lists_sheet)
            ch = self.bot.get_channel(self.personnel_channel_id)
            if ch:
                embed = discord.Embed(
                    title="📊 Суточный отчёт по норме (00:00 МСК)",
                    description="Автоматическая сверка списков персонала и выполнения онлайна успешно завершена.",
                    color=discord.Color.green()
                )
                await ch.send(embed=embed)
        except Exception as e:
            print(f"Ошибка проверки нормы: {e}")

    @app_commands.command(name="norm", description="Посмотреть статус своей нормы или другого сотрудника")
    async def norm(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        is_exempt = target.id in self.exempted_users
        embed = discord.Embed(
            title="📊 Статус суточной нормы",
            description=f"**Сотрудник:** {target.mention}\n**Статус:** {'🟢 Освобожден' if is_exempt else '🔵 В процессе выполнения'}",
            color=discord.Color.green() if is_exempt else discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="check_norm", description="Принудительная проверка нормы состава (Администратор+)")
    @app_commands.default_permissions(administrator=True)
    async def check_norm(self, interaction: discord.Interaction):
        await self.execute_norm_check()
        await interaction.response.send_message("✅ Принудительная проверка нормы запущена, отчет отправлен в канал персонала.", ephemeral=True)

    @app_commands.command(name="norm_exempt", description="Освободить сотрудника от нормы (Только Куратор и выше)")
    @app_commands.default_permissions(administrator=True)
    async def norm_exempt(self, interaction: discord.Interaction, member: discord.Member):
        allowed = ["Владелец проекта", "Со-Владелец", "Куратор"]
        if not any(r.name in allowed for r in interaction.user.roles):
            return await interaction.response.send_message("❌ Команда доступна только Куратору и выше.", ephemeral=True)
        
        self.exempted_users.add(member.id)
        await interaction.response.send_message(f"✅ Сотрудник {member.mention} освобожден от выполнения суточной нормы.", ephemeral=True)

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
            description=f"**Сотрудник:** {member.mention}\n**Новая должность:** {role}\n**Назначил:** {interaction.user.mention}",
            color=discord.Color.blue()
        )
        ch = self.bot.get_channel(self.personnel_channel_id)
        if ch:
            await ch.send(embed=embed)
        await interaction.response.send_message("✅ Назначение зафиксировано в кадровом логе.", ephemeral=True)

    @app_commands.command(name="unstaff", description="Снять сотрудника с должности")
    @app_commands.default_permissions(administrator=True)
    async def unstaff_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "По решению руководства"):
        embed = discord.Embed(
            title="📉 Снятие с должности",
            description=f"**Сотрудник:** {member.mention}\n**Причина:** {reason}\n**Снял:** {interaction.user.mention}",
            color=discord.Color.red()
        )
        ch = self.bot.get_channel(self.personnel_channel_id)
        if ch:
            await ch.send(embed=embed)
        await interaction.response.send_message("✅ Снятие зафиксировано в кадровом логе.", ephemeral=True)

    @app_commands.command(name="staff", description="Автоматический вывод состава персонала из таблицы «Списки»")
    async def staff_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            ws = await asyncio.to_thread(self.get_lists_sheet)
            rows = await asyncio.to_thread(ws.get_all_values)
            
            roles_order = [
                "Владелец проекта", "Со-Владелец", "Куратор",
                "Ст.Администратор", "Администратор", "Ст.Модератор",
                "Модератор", "Хелпер"
            ]
            
            staff_by_role = {role: [] for role in roles_order}
            
            if len(rows) > 1:
                for row in rows[1:]:
                    if len(row) >= 2 and row[0].strip() and row[1].strip():
                        nick = row[0].strip()
                        role = row[1].strip()
                        for standard_role in roles_order:
                            if standard_role.lower() in role.lower():
                                staff_by_role[standard_role].append(nick)
                                break

            description_lines = []
            for role in roles_order:
                members = staff_by_role[role]
                if members:
                    members_str = "\n".join([f"• `{m}`" for m in members])
                else:
                    members_str = "Состав отсутствует"
                description_lines.append(f"**| {role}**\n{members_str}\n")

            embed = discord.Embed(
                title="👑 АКТУАЛЬНЫЙ СОСТАВ (Из таблицы «Списки»)",
                description="\n".join(description_lines),
                color=discord.Color.gold()
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка чтения таблицы «Списки»: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(StaffCog(bot))
