import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import pytz
import gspread
import os
import asyncio

STAFF_ROLES_ORDER = [
    "Владелец", "Со-Владелец", "Куратор",
    "Ст.Администратор", "Администратор", "Ст.Модератор",
    "Модератор", "Хелпер"
]

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
            ch = self.bot.get_channel(self.personnel_channel_id)
            report_lines = [
                "📊 **Суточный отчёт по норме (00:00 МСК)**",
                "━━━━━━━━━━━━━━━━━━━"
            ]

            # Проходим по всем участникам сервера и ищем роли стаффа
            for guild in self.bot.guilds:
                for member in guild.members:
                    member_roles = [r.name for r in member.roles]
                    matched_role = next((r for r in STAFF_ROLES_ORDER if r in member_roles), None)
                    
                    if matched_role:
                        nick = member.display_name
                        status = "🟢 Освобожден" if member.id in self.exempted_users else "🟡 В процессе"
                        line = f"• **{nick}** ({member.mention}) • `{matched_role}`\n  └ Статус: {status}"
                        report_lines.append(line)

            report_lines.append("━━━━━━━━━━━━━━━━━━━")
            report_lines.append("✨ *Автоматическая проверка реального состава Discord*")

            if ch:
                embed = discord.Embed(
                    title="👑 Суточный отчёт персонала VoidPulse",
                    description="\n".join(report_lines),
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.now()
                )
                await ch.send(embed=embed)
        except Exception as e:
            print(f"Ошибка проверки нормы: {e}")

    @app_commands.command(name="norm", description="Посмотреть статус своей нормы")
    async def norm(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        member_roles = [r.name for r in target.roles]

        if "Тех. администратор" in member_roles:
            embed = discord.Embed(title="🛡️ Статус: Тех. администратор", color=discord.Color.dark_theme())
            embed.add_field(name="Сотрудник", value=target.mention, inline=False)
            embed.add_field(name="Информация", value="Вы являетесь Тех. администратором.\nНорма для данной должности **не учитывается** и не требуется.", inline=False)
            embed.set_footer(text="VoidPulse Staff System")
            return await interaction.response.send_message(embed=embed)

        is_staff = any(role in STAFF_ROLES_ORDER for role in member_roles) or "Владелец проекта" in member_roles
        if not is_staff and not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(title="⛔ Ошибка доступа", description="Вас нет в списке официального персонала.", color=discord.Color.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        is_exempt = target.id in self.exempted_users
        
        embed = discord.Embed(
            title="📊 Статус суточной нормы",
            color=discord.Color.green() if is_exempt else discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Сотрудник", value=f"{target.mention} (`{target.display_name}`)", inline=False)
        embed.add_field(name="Текущий статус", value="🟢 Освобожден" if is_exempt else "🟡 В процессе выполнения", inline=False)
        
        if is_exempt:
            embed.add_field(name="Отыграно на сервере", value="`--` / `--`", inline=False)
            embed.add_field(name="За всё время", value="`-- ч . -- м`", inline=False)
            embed.add_field(name="Прогресс", value="`[██████████] 100%` (Освобожден)", inline=False)
        else:
            embed.add_field(name="Отыграно на сервере", value="`0ч . 00м` / `1ч . 00м`", inline=False)
            embed.add_field(name="За всё время", value="`11ч . 46м`", inline=False)
            embed.add_field(name="Прогресс", value="`[░░░░░░░░░░] 0%`", inline=False)
            
        embed.set_footer(text="VoidPulse Time Tracker")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="norm_exempt", description="Освободить сотрудника от нормы")
    @app_commands.default_permissions(administrator=True)
    async def norm_exempt(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(ephemeral=True)
        self.exempted_users.add(member.id)
        embed = discord.Embed(
            title="🛡️ Освобождение от нормы (Norm Exempt)",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="👤 Сотрудник", value=member.mention, inline=True)
        embed.add_field(name="🛡️ Выдал", value=interaction.user.mention, inline=True)
        embed.add_field(name="Статус", value="🟢 Полностью освобожден от суточной нормы", inline=False)
        embed.set_footer(text="VoidPulse Staff Management")

        ch = self.bot.get_channel(self.personnel_channel_id)
        if ch:
            await ch.send(embed=embed)
        await interaction.followup.send(f"✅ Сотрудник {member.mention} освобожден от суточной нормы.", ephemeral=True)

    @app_commands.command(name="appoint", description="Назначить сотрудника (выдает роль в Discord и пишет в таблицу)")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(member="Кого назначаем", role="Должность из списка", mc_group="Группа в Minecraft", comment="Комментарий к назначению")
    @app_commands.choices(role=[app_commands.Choice(name=r, value=r) for r in STAFF_ROLES_ORDER])
    async def appoint_member(self, interaction: discord.Interaction, member: discord.Member, role: str, mc_group: str, comment: str = "Нет комментариев"):
        if member.id == interaction.user.id:
            embed = discord.Embed(title="⛔ Системная ошибка", description="Вы не можете назначить самого себя.", color=discord.Color.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        
        try:
            # Выдаем реальную роль в Discord, если она существует на сервере
            discord_role = discord.utils.get(interaction.guild.roles, name=role)
            if discord_role:
                await member.add_roles(discord_role)

            # Записываем в Google Таблицу
            ws = await asyncio.to_thread(self.get_lists_sheet)
            new_row = [member.display_name, role, str(member.id), f"@{member.name}", comment, "0"]
            await asyncio.to_thread(ws.append_row, new_row)

            embed = discord.Embed(
                title="🟢 Официальное обновление персонала",
                color=discord.Color.brand_green(),
                timestamp=datetime.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="👤 Игрок", value=f"`{member.display_name}`\n{member.mention}", inline=True)
            embed.add_field(name="💼 Должность", value=f"**{role}**", inline=True)
            embed.add_field(name="🎮 Группа (Minecraft)", value=f"`{mc_group}`", inline=True)
            embed.add_field(name="📝 Комментарий", value=f"*{comment}*", inline=False)
            embed.add_field(name="🛡️ Назначил", value=f"{interaction.user.mention} (`{interaction.user.display_name}`)", inline=False)
            embed.set_footer(text="Роль выдана в Discord и записана в таблицу")

            ch = self.bot.get_channel(self.personnel_channel_id)
            if ch:
                await ch.send(embed=embed)
            await interaction.followup.send(f"✅ Игрок {member.mention} получил роль **{role}** и внесен в базу.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка при назначении: {e}", ephemeral=True)

    @app_commands.command(name="unstaff", description="Снять сотрудника (снимает роль в Discord)")
    @app_commands.default_permissions(administrator=True)
    async def unstaff_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "По решению руководства"):
        if member.id == interaction.user.id:
            embed = discord.Embed(title="⛔ Системная ошибка", description="Вы не можете снять самого себя.", color=discord.Color.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        
        try:
            # Снимаем стафф-роли с участника в Discord
            for r_name in STAFF_ROLES_ORDER:
                d_role = discord.utils.get(interaction.guild.roles, name=r_name)
                if d_role and d_role in member.roles:
                    await member.remove_roles(d_role)

            embed = discord.Embed(
                title="📉 Снятие / Понижение с должности",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="👤 Сотрудник", value=f"{member.mention} (`{member.display_name}`)", inline=True)
            embed.add_field(name="🛡️ Снял", value=interaction.user.mention, inline=True)
            embed.add_field(name="📋 Причина", value=f"```{reason}```", inline=False)
            embed.set_footer(text="Роли в Discord успешно сняты")

            ch = self.bot.get_channel(self.personnel_channel_id)
            if ch:
                await ch.send(embed=embed)
            await interaction.followup.send(f"✅ Сотрудник {member.mention} снят с должности.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка при снятии ролей: {e}", ephemeral=True)

    @app_commands.command(name="staff", description="Показать реальный состав по ролям в Discord")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.user.id)
    async def staff_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            guild = interaction.guild
            staff_by_role = {role: [] for role in STAFF_ROLES_ORDER}

            # Сканируем реальных участников сервера по ролям
            for member in guild.members:
                member_roles = [r.name for r in member.roles]
                for role_name in STAFF_ROLES_ORDER:
                    if role_name in member_roles:
                        staff_by_role[role_name].append(member.mention)

            description_lines = []
            for role in STAFF_ROLES_ORDER:
                members = staff_by_role[role]
                if members:
                    members_str = "\n".join([f"➥ {m}" for m in members])
                else:
                    members_str = "*Вакантно*"
                description_lines.append(f"**🔹 {role}**\n{members_str}\n")

            embed = discord.Embed(
                title="👑 АКТУАЛЬНЫЙ СОСТАВ VOIDPULSE (РКН Discord)",
                description="\n".join(description_lines),
                color=discord.Color.gold(),
                timestamp=datetime.datetime.now()
            )
            embed.set_footer(text="Проверено по реальным ролям на сервере")
            
            ch = self.bot.get_channel(self.personnel_channel_id)
            if ch:
                await ch.send(embed=embed)
            await interaction.followup.send("✅ Актуальный состав по ролям Discord выведен.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка проверки состава: {e}", ephemeral=True)

    @app_commands.command(name="list", description="Показать актуальный список персонала")
    async def list_alias(self, interaction: discord.Interaction):
        await self.staff_list.callback(self, interaction)

    @app_commands.command(name="check_norm", description="Принудительная проверка нормы состава")
    @app_commands.default_permissions(administrator=True)
    async def check_norm(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.execute_norm_check()
        await interaction.followup.send("✅ Отчет по норме отправлен.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(StaffCog(bot))
