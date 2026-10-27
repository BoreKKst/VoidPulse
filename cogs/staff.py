import discord
from discord.ext import commands
from discord import app_commands
import requests
import config

class StaffCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def send_ptero_command(self, cmd: str):
        url = f"{config.PTERO_URL}/api/client/servers/{config.PTERO_SERVER_ID}/command"
        headers = {
            "Authorization": f"Bearer {config.PTERO_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        try:
            requests.post(url, json={"command": cmd}, headers=headers, timeout=5)
        except Exception as e:
            print(f"Ошибка Pterodactyl API: {e}")

    def insert_into_sheet_category(self, category_name: str, row_data: list):
        if not self.bot.sheet_staff:
            return

        try:
            col_a = self.bot.sheet_staff.col_values(1)
            target_row = len(col_a) + 1

            for idx, val in enumerate(col_a, start=1):
                if val.strip().lower() == category_name.strip().lower():
                    target_row = idx + 1
                    break

            self.bot.sheet_staff.insert_row(row_data, target_row)
        except Exception as e:
            print(f"Ошибка вставки в категорию {category_name}: {e}")

    @app_commands.command(name="appoint", description="Назначить сотрудника на должность")
    @app_commands.describe(
        member="Участник Discord", 
        role_key="Должность", 
        mc_nick="Ник в Minecraft",
        comment="Комментарий",
        tg_vk="Telegram / VK"
    )
    @app_commands.choices(role_key=[
        app_commands.Choice(name=data["name"], value=key) for key, data in config.STAFF_HIERARCHY.items()
    ])
    async def appoint(
        self, 
        interaction: discord.Interaction, 
        member: discord.Member, 
        role_key: str, 
        mc_nick: str,
        comment: str = "Принят в состав",
        tg_vk: str = "-"
    ):
        await interaction.response.defer(ephemeral=True)

        role_info = config.STAFF_HIERARCHY[role_key]
        main_role_id, staff_role_id = role_info["roles"]

        for guild in self.bot.guilds:
            guild_member = guild.get_member(member.id)
            if guild_member:
                target_role_id = main_role_id if guild.id != interaction.guild_id else staff_role_id
                role = guild.get_role(target_role_id)
                project_role = guild.get_role(config.EXTRA_ROLES["project_staff"][0] if guild.id != interaction.guild_id else config.EXTRA_ROLES["project_staff"][1])
                
                if role:
                    await guild_member.add_roles(role)
                if project_role:
                    await guild_member.add_roles(project_role)
                
                if role_key == "helper":
                    trial_role_id = config.EXTRA_ROLES["trial"][0] if guild.id != interaction.guild_id else config.EXTRA_ROLES["trial"][1]
                    trial_role = guild.get_role(trial_role_id)
                    if trial_role:
                        await guild_member.add_roles(trial_role)

        try:
            await member.edit(nick=mc_nick)
        except Exception:
            pass

        self.send_ptero_command(f"lp user {mc_nick} parent set {role_info['lp_group']}")

        row_data = [mc_nick, role_info["name"], f"{member.name} ({member.id})", tg_vk, comment, 0, 0]
        self.insert_into_sheet_category(role_info["category"], row_data)

        log_channel = self.bot.get_channel(config.LOG_STAFF_CHANNEL)
        if log_channel:
            embed = discord.Embed(title="🌌 VoidPulse Staff System", color=config.COLOR_SUCCESS)
            embed.description = (
                f"🟢 **НАЗНАЧЕНИЕ СОТРУДНИКА**\n\n"
                f"👤 **Участник:** {member.mention}\n"
                f"💼 **Должность:** {role_info['name']}\n"
                f"🎮 **Ник в MC:** `{mc_nick}`\n"
                f"💬 **Комментарий:** {comment}\n"
                f"⚙️ **LuckPerms:** Группа `{role_info['lp_group']}` выдана\n\n"
                f"🛡️ **Действие выполнил:** {interaction.user.mention}"
            )
            embed.set_footer(text="VoidPulse Staff System")
            await log_channel.send(embed=embed)

        await interaction.followup.send(f"✅ Сотрудник {member.mention} назначен на должность **{role_info['name']}**!")

    @app_commands.command(name="unstaff", description="Снять сотрудника с должности")
    async def unstaff(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        await interaction.response.defer(ephemeral=True)

        for guild in self.bot.guilds:
            guild_member = guild.get_member(member.id)
            if guild_member:
                roles_to_remove = []
                for r_data in config.STAFF_HIERARCHY.values():
                    r1 = guild.get_role(r_data["roles"][0])
                    r2 = guild.get_role(r_data["roles"][1])
                    if r1: roles_to_remove.append(r1)
                    if r2: roles_to_remove.append(r2)
                
                for ex_key in ["project_staff", "trial"]:
                    r1 = guild.get_role(config.EXTRA_ROLES[ex_key][0])
                    r2 = guild.get_role(config.EXTRA_ROLES[ex_key][1])
                    if r1: roles_to_remove.append(r1)
                    if r2: roles_to_remove.append(r2)

                await guild_member.remove_roles(*[r for r in roles_to_remove if r in guild_member.roles])

        if self.bot.sheet_staff:
            try:
                records = self.bot.sheet_staff.get_all_values()
                for idx, row in enumerate(records, start=1):
                    if len(row) > 2 and str(member.id) in row[2]:
                        self.bot.sheet_staff.delete_rows(idx)
                        break
            except Exception as e:
                print(f"Ошибка удаления из таблицы: {e}")

        log_channel = self.bot.get_channel(config.LOG_STAFF_CHANNEL)
        if log_channel:
            embed = discord.Embed(title="🌌 VoidPulse Staff System", color=config.COLOR_ERROR)
            embed.description = (
                f"🔴 **СНЯТИЕ С ДОЛЖНОСТИ**\n\n"
                f"👤 **Сотрудник:** {member.mention}\n"
                f"📝 **Причина:** {reason}\n"
                f"📊 **База данных:** Запись удалена из Google Таблицы\n\n"
                f"🛡️ **Действие выполнил:** {interaction.user.mention}"
            )
            embed.set_footer(text="VoidPulse Staff System")
            await log_channel.send(embed=embed)

        await interaction.followup.send(f"🔴 Пользователь {member.mention} снят со всех ролей персонала.")

    @app_commands.command(name="list", description="Выгрузить список персонала")
    async def list_staff(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        target_channel = self.bot.get_channel(config.LOG_LIST_CHANNEL)
        if not target_channel:
            await interaction.followup.send("❌ Канал списков не найден!")
            return

        embed = discord.Embed(title="🌌 VoidPulse Staff System", color=config.COLOR_PURPLE)
        embed.description = "👑 **АКТУАЛЬНЫЙ СПИСОК СОСТАВА ПРОЕКТА**\n"

        for key, data in config.STAFF_HIERARCHY.items():
            role_id = data["roles"][0]
            role = interaction.guild.get_role(role_id)
            members = [m.mention for m in role.members] if role else []
            val = "\n".join(members) if members else "*Состав отсутствует*"
            embed.add_field(name=f"│ {data['name']}", value=val, inline=False)

        embed.set_footer(text="VoidPulse Staff System • Авто-выгрузка")
        await target_channel.send(embed=embed)
        await interaction.followup.send(f"✅ Список состава выгружен в {target_channel.mention}!")

async def setup(bot):
    await bot.add_cog(StaffCog(bot))
