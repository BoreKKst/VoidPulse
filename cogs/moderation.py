import discord
from discord.ext import commands
from discord import app_commands
import datetime
import gspread
import os
import asyncio

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.violations_channel_id = 1564335766300004434

    def get_sheet(self):
        gc = gspread.service_account(filename="credentials.json")
        return gc.open_by_key(os.getenv("SPREADSHEET_ID") or "1gAAyXJ20cAKBHCUzAl9H-v8DLm4aEaUMpwt2VLbuves").worksheet("Учет предупреждений")

    @app_commands.command(name="warn", description="Выдать выговор сотруднику с записью в таблицу")
    @app_commands.default_permissions(administrator=True)
    async def warn_member(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        if member.id == interaction.user.id:
            embed = discord.Embed(title="⛔ Системная ошибка", description="Действие отклонено: Вы не можете выдать выговор самому себе.", color=discord.Color.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        try:
            ws = await asyncio.to_thread(self.get_sheet)
            date_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
            await asyncio.to_thread(ws.append_row, [member.display_name, date_str, reason, interaction.user.display_name])

            embed = discord.Embed(
                title="⚠️ Выдан официальный выговор",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="👤 Сотрудник", value=f"{member.mention} (`{member.display_name}`)", inline=False)
            embed.add_field(name="📋 Причина", value=f"```{reason}```", inline=False)
            embed.add_field(name="🛡️ Выдал", value=interaction.user.mention, inline=False)
            embed.set_footer(text="VoidPulse Moderation Log")

            ch = self.bot.get_channel(self.violations_channel_id)
            if ch:
                await ch.send(embed=embed)
            await interaction.followup.send(f"✅ Выговор для {member.mention} зафиксирован в базе.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка подключения к базе данных: {e}", ephemeral=True)

    @app_commands.command(name="unwarn", description="Снять последнее предупреждение (Куратор+)")
    @app_commands.default_permissions(administrator=True)
    async def unwarn_member(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(ephemeral=True)
        restricted_roles = ["Хелпер", "Модератор", "Ст.Модератор"]
        if any(r.name in restricted_roles for r in interaction.user.roles):
            return await interaction.followup.send("❌ Доступ запрещен. У вас недостаточно прав для снятия выговоров.", ephemeral=True)

        try:
            ws = await asyncio.to_thread(self.get_sheet)
            rows = await asyncio.to_thread(ws.get_all_values)
            for i in range(len(rows) - 1, 0, -1):
                if rows[i] and member.display_name.lower() in rows[i][0].lower():
                    await asyncio.to_thread(ws.delete_rows, i + 1)
                    
                    embed = discord.Embed(
                        title="🛡️ Снятие выговора (Амнистия)",
                        color=discord.Color.green(),
                        timestamp=datetime.datetime.now()
                    )
                    embed.add_field(name="👤 Сотрудник", value=member.mention, inline=True)
                    embed.add_field(name="🛡️ Снял", value=interaction.user.mention, inline=True)
                    embed.set_footer(text="VoidPulse Moderation Log")

                    ch = self.bot.get_channel(self.violations_channel_id)
                    if ch:
                        await ch.send(embed=embed)
                    return await interaction.followup.send(f"✅ Последний активный выговор {member.mention} успешно удален.", ephemeral=True)
                    
            await interaction.followup.send("⚠️ Активных предупреждений в базе не найдено.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка базы данных: {e}", ephemeral=True)

    @app_commands.command(name="warns", description="Просмотреть активные выговоры сотрудника")
    async def warns(self, interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer()
        target = member or interaction.user
        try:
            ws = await asyncio.to_thread(self.get_sheet)
            rows = await asyncio.to_thread(ws.get_all_values)
            records = [r for r in rows[1:] if r and target.display_name.lower() in r[0].lower()]
            
            desc = "\n\n".join([f"🕒 `{r[1]}`\n📝 Причина: **{r[2]}**\n🛡️ Выдал: `{r[3]}`" for r in records]) if records else "✅ Нарушений не зафиксировано."
            
            embed = discord.Embed(
                title=f"📋 Личное дело — {target.display_name}",
                description=desc,
                color=discord.Color.red() if records else discord.Color.green(),
                timestamp=datetime.datetime.now()
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            embed.set_footer(text=f"Всего выговоров: {len(records)}")
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка чтения данных: {e}", ephemeral=True)

    @app_commands.command(name="clearwarns", description="Очистить абсолютно все предупреждения пользователя")
    @app_commands.default_permissions(administrator=True)
    async def clearwarns(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(ephemeral=True)
        try:
            ws = await asyncio.to_thread(self.get_sheet)
            rows = await asyncio.to_thread(ws.get_all_values)
            deleted = 0
            for i in range(len(rows) - 1, 0, -1):
                if rows[i] and member.display_name.lower() in rows[i][0].lower():
                    await asyncio.to_thread(ws.delete_rows, i + 1)
                    deleted += 1
                    
            embed = discord.Embed(
                title="🧹 Полная амнистия (Очистка)",
                color=discord.Color.gold(),
                timestamp=datetime.datetime.now()
            )
            embed.add_field(name="👤 Сотрудник", value=member.mention, inline=False)
            embed.add_field(name="🗑️ Очищено записей", value=f"`{deleted} шт.`", inline=True)
            embed.add_field(name="🛡️ Инициатор", value=interaction.user.mention, inline=True)
            embed.set_footer(text="VoidPulse System")

            ch = self.bot.get_channel(self.violations_channel_id)
            if ch:
                await ch.send(embed=embed)
            await interaction.followup.send(f"✅ База очищена. Удалено {deleted} записей для {member.mention}.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка базы данных: {e}", ephemeral=True)

    @app_commands.command(name="кик", description="Исключить участника с сервера (Доступно Тех. Админам)")
    @app_commands.default_permissions(kick_members=True)
    async def kick_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Грубое нарушение правил"):
        if member.id == interaction.user.id:
            embed = discord.Embed(title="⛔ Ошибка", description="Вы не можете исключить самого себя.", color=discord.Color.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        if member.top_role >= interaction.user.top_role and interaction.guild.owner_id != interaction.user.id:
             embed = discord.Embed(title="⛔ Отказ в доступе", description="Вы не можете исключить пользователя, чья роль выше или равна вашей.", color=discord.Color.red())
             return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="🚫 Исключение с сервера (KICK)",
                color=discord.Color.dark_red(),
                timestamp=datetime.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="👤 Пользователь", value=f"{member.mention} (`{member.display_name}`)", inline=True)
            embed.add_field(name="🛡️ Модератор", value=interaction.user.mention, inline=True)
            embed.add_field(name="📋 Причина", value=f"```{reason}```", inline=False)
            
            ch = self.bot.get_channel(self.violations_channel_id)
            if ch:
                await ch.send(embed=embed)
            await interaction.followup.send(f"✅ Пользователь {member.mention} был исключен.", ephemeral=True)
        except discord.Forbidden:
             await interaction.followup.send("❌ У бота недостаточно прав для исключения этого пользователя.", ephemeral=True)

    @app_commands.command(name="mclog", description="Зафиксировать серверное действие (доступно Тех. Админам)")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(action=[
        app_commands.Choice(name="Бан", value="Бан"),
        app_commands.Choice(name="Пермбан", value="Пермбан"),
        app_commands.Choice(name="Темп-бан", value="Темп-бан"),
        app_commands.Choice(name="Варн", value="Варн"),
        app_commands.Choice(name="Анварн", value="Анварн"),
        app_commands.Choice(name="Кик", value="Кик"),
        app_commands.Choice(name="Мут", value="Мут"),
        app_commands.Choice(name="Анмут", value="Анмут"),
        app_commands.Choice(name="Темп-мут", value="Темп-мут"),
        app_commands.Choice(name="GM 1 (Креатив)", value="GM 1"),
        app_commands.Choice(name="Выдача OP", value="Выдача OP"),
        app_commands.Choice(name="Снятие OP (Deop)", value="Снятие OP")
    ])
    async def mclog(self, interaction: discord.Interaction, action: str, player: str, admin: str, reason: str = "Причина не указана"):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title=f"⛏️ Лог Minecraft сервера: {action.upper()}",
            color=discord.Color.dark_purple(),
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="Игрок/Нарушитель", value=f"`{player}`", inline=True)
        embed.add_field(name="Исполнитель", value=f"`{admin}`", inline=True)
        embed.add_field(name="Детали / Причина", value=f"```{reason}```", inline=False)
        embed.set_footer(text="Интеграция с консолью VoidPulse")

        ch = self.bot.get_channel(self.violations_channel_id)
        if ch:
            await ch.send(embed=embed)
        await interaction.followup.send(f"✅ Игровое действие **{action}** успешно записано в лог.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
