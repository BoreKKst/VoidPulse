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
        await interaction.response.defer(ephemeral=True)
        try:
            ws = await asyncio.to_thread(self.get_sheet)
            date_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
            await asyncio.to_thread(ws.append_row, [member.display_name, date_str, reason, interaction.user.display_name])
            
            embed = discord.Embed(
                title="⚠️ Выдан выговор (Warn)",
                description=f"**Сотрудник:** {member.mention}\n**Причина:** {reason}\n**Выдал:** {interaction.user.mention}",
                color=discord.Color.orange()
            )
            ch = self.bot.get_channel(self.violations_channel_id)
            if ch:
                await ch.send(embed=embed)
            await interaction.followup.send("✅ Варн выдан и занесен в лог нарушений.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

    @app_commands.command(name="unwarn", description="Снять последнее предупреждение (Администратор и выше)")
    @app_commands.default_permissions(administrator=True)
    async def unwarn_member(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(ephemeral=True)
        restricted = ["Хелпер", "Модератор"]
        if any(r.name in restricted for r in interaction.user.roles):
            return await interaction.followup.send("❌ У вас нет прав для снятия варнов.", ephemeral=True)

        try:
            ws = await asyncio.to_thread(self.get_sheet)
            rows = await asyncio.to_thread(ws.get_all_values)
            for i in range(len(rows) - 1, 0, -1):
                if rows[i] and member.display_name.lower() in rows[i][0].lower():
                    await asyncio.to_thread(ws.delete_rows, i + 1)
                    embed = discord.Embed(
                        title="🛡️ Снятие выговора",
                        description=f"**Сотрудник:** {member.mention}\n**Снял:** {interaction.user.mention}",
                        color=discord.Color.green()
                    )
                    ch = self.bot.get_channel(self.violations_channel_id)
                    if ch:
                        await ch.send(embed=embed)
                    return await interaction.followup.send(f"✅ Последний варн {member.mention} удален.", ephemeral=True)
            await interaction.followup.send("⚠️ Активных варнов в таблице не найдено.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

    @app_commands.command(name="warns", description="Просмотреть активные выговоры сотрудника")
    async def warns(self, interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer()
        target = member or interaction.user
        try:
            ws = await asyncio.to_thread(self.get_sheet)
            rows = await asyncio.to_thread(ws.get_all_values)
            records = [r for r in rows[1:] if r and target.display_name.lower() in r[0].lower()]
            desc = "\n".join([f"`{r[1]}` | {r[2]} *(Выдал: {r[3]})*" for r in records]) if records else "Нарушений не зафиксировано."
            embed = discord.Embed(
                title=f"📋 Список нарушений — {target.display_name}",
                description=desc,
                color=discord.Color.red() if records else discord.Color.green()
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка чтения данных: {e}", ephemeral=True)

    @app_commands.command(name="clearwarns", description="Очистить абсолютно все предупреждения указанного пользователя")
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
            await interaction.followup.send(f"✅ Очищено записей из таблицы: **{deleted}** для {member.mention}.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

    @app_commands.command(name="кик", description="Исключить участника с сервера")
    @app_commands.default_permissions(kick_members=True)
    async def kick_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Нарушение правил"):
        await interaction.response.defer(ephemeral=True)
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="🚫 Исключение с сервера (Kick)",
            description=f"**Пользователь:** {member.mention}\n**Причина:** {reason}\n**Модератор:** {interaction.user.mention}",
            color=discord.Color.dark_red()
        )
        ch = self.bot.get_channel(self.violations_channel_id)
        if ch:
            await ch.send(embed=embed)
        await interaction.followup.send(f"✅ Пользователь {member.mention} исключен.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
