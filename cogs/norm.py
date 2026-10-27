import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import config

MSK_TZ = datetime.timezone(datetime.timedelta(hours=3))
CHECK_TIME = datetime.time(hour=0, minute=0, tzinfo=MSK_TZ)

class NormCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.exempt_users = set()
        self.midnight_check.start()

    def cog_unload(self):
        self.midnight_check.cancel()

    @tasks.loop(time=CHECK_TIME)
    async def midnight_check(self):
        if not self.bot.sheet_staff or not self.bot.sheet_warns:
            return

        try:
            rows = self.bot.sheet_staff.get_all_values()
            for idx, row in enumerate(rows, start=1):
                if len(row) < 7 or not row[2] or row[0] in ["Игровой никнейм", "Владельцы", "Кураторы", "Администраторы", "Модераторы", "Хелперы"]:
                    continue

                mc_nick, role_name, discord_info = row[0], row[1], row[2]
                played_hours = float(row[5]) if row[5].replace('.', '', 1).isdigit() else 0.0
                current_warns = int(row[6]) if row[6].isdigit() else 0

                if role_name in ["Владелец проекта", "Со-Владелец", "Куратор"]:
                    continue

                discord_id = None
                if "(" in discord_info and ")" in discord_info:
                    discord_id = int(discord_info.split("(")[-1].replace(")", "").strip())
                elif discord_info.isdigit():
                    discord_id = int(discord_info)

                if not discord_id:
                    continue

                user = self.bot.get_user(discord_id)

                if discord_id in self.exempt_users:
                    if user:
                        try:
                            await user.send("⏸️ **VoidPulse:** Сегодня вы были освобождены от нормы.")
                        except Exception:
                            pass
                    continue

                if played_hours >= 1.0:
                    if user:
                        try:
                            embed = discord.Embed(title="🌌 VoidPulse Staff System", color=config.COLOR_SUCCESS)
                            embed.description = f"🟢 **СУТОЧНАЯ НОРМА ВЫПОЛНЕНА!**\n\nОтличная работа, **{mc_nick}**!\n⏱️ Отыграно: **{played_hours} ч.**"
                            embed.set_footer(text="VoidPulse Staff System • 00:00 МСК")
                            await user.send(embed=embed)
                        except Exception:
                            pass
                else:
                    new_warns = current_warns + 1
                    date_now = datetime.datetime.now(MSK_TZ).strftime("%d.%m.%Y %H:%M")

                    self.bot.sheet_staff.update_cell(idx, 7, new_warns)
                    self.bot.sheet_warns.append_row([mc_nick, date_now, "Невыполнение суточной нормы онлайна", "Система (Авто)"])

                    if user:
                        try:
                            embed = discord.Embed(title="🌌 VoidPulse Staff System", color=config.COLOR_ERROR)
                            embed.description = f"🔴 **СУТОЧНАЯ НОРМА НЕ ВЫПОЛНЕНА**\n\nУважаемый **{mc_nick}**, вы отыграли **{played_hours} ч.** из **1.0 ч.**\n⚠️ Выговор ({new_warns}/3)."
                            embed.set_footer(text="VoidPulse Staff System • 00:00 МСК")
                            await user.send(embed=embed)
                        except Exception:
                            pass

                    log_channel = self.bot.get_channel(config.LOG_PUNISH_CHANNEL)
                    if log_channel:
                        embed = discord.Embed(title="🌌 VoidPulse Staff System", color=config.COLOR_ERROR)
                        embed.description = f"🔴 **АВТО-ВЫГОВОР ЗА НОРМУ**\n\n👤 **Сотрудник:** <@{discord_id}> (`{mc_nick}`)\n⏱️ **Отыграно:** {played_hours} ч. / 1.0 ч.\n⚠️ **Результат:** Выговор ({new_warns}/3)\n\n🛡️ **Выдал:** Система (Авто 00:00 МСК)"
                        embed.set_footer(text="VoidPulse Staff System")
                        await log_channel.send(embed=embed)

            self.exempt_users.clear()
        except Exception as e:
            print(f"Ошибка проверки нормы: {e}")

    @midnight_check.before_loop
    async def before_midnight_check(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="check_norm", description="Проверить норму вручную")
    async def check_norm(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.midnight_check()
        await interaction.followup.send("✅ Проверка нормы завершена!")

    @app_commands.command(name="norm_exempt", description="Освободить от нормы")
    async def norm_exempt(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        self.exempt_users.add(member.id)
        await interaction.response.send_message(f"⏸️ Сотрудник {member.mention} освобожден от нормы. Причина: **{reason}**", ephemeral=True)

async def setup(bot):
    await bot.add_cog(NormCog(bot))
