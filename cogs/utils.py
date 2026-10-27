import discord
from discord.ext import commands
from discord import app_commands
import psutil
import os

class UtilsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="say", description="Отправить сообщение от имени бота (в канал или ЛС)")
    @app_commands.default_permissions(administrator=True)
    async def say(self, interaction: discord.Interaction, текст: str, титл: str = "Объявление", игрок: discord.Member = None):
        embed = discord.Embed(title=титл, description=текст, color=discord.Color.purple())
        if игрок:
            try:
                await игрок.send(embed=embed)
                await interaction.response.send_message(f"✅ Сообщение отправлено в ЛС {игрок.mention}", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message("❌ У указанного пользователя закрыты личные сообщения.", ephemeral=True)
        else:
            await interaction.channel.send(embed=embed)
            await interaction.response.send_message("✅ Сообщение отправлено в текущий канал.", ephemeral=True)

    @app_commands.command(name="reload", description="Перезагрузить модули бота без полного отключения")
    @app_commands.default_permissions(administrator=True)
    async def reload_bot(self, interaction: discord.Interaction):
        await interaction.response.send_message("🔄 Обновление и перезагрузка модулей...", ephemeral=True)
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.bot.reload_extension(f'cogs.{filename[:-3]}')
        await self.bot.tree.sync()
        await interaction.edit_original_response(content="✅ Все модули успешно пересобраны и синхронизированы.")

    @app_commands.command(name="status", description="Получить технические характеристики сервера хостинга (в ЛС)")
    @app_commands.default_permissions(administrator=True)
    async def status(self, interaction: discord.Interaction):
        ram = psutil.virtual_memory()
        cpu = psutil.cpu_percent()
        embed = discord.Embed(
            title="🖥️ Мониторинг ресурсов хостинга (Render)",
            description=f"**Загрузка ЦП:** `{cpu}%`\n**Загрузка ОЗУ:** `{ram.percent}%` ({round(ram.used / 1024 / 1024)}MB / {round(ram.total / 1024 / 1024)}MB)\n**Задержка бота:** `{round(self.bot.latency * 1000)}ms`",
            color=discord.Color.dark_theme()
        )
        try:
            await interaction.user.send(embed=embed)
            await interaction.response.send_message("✅ Технический отчёт отправлен вам в ЛС.", ephemeral=True)
        except:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="test", description="Проверить отправку сообщений в ЛС")
    async def test_msg(self, interaction: discord.Interaction, текст: str):
        try:
            await interaction.user.send(f"🧪 **Тестовый сигнал:** {текст}")
            await interaction.response.send_message("✅ Тестовое сообщение доставлено в ЛС.", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Не удалось отправить сообщение. Включите ЛС в настройках приватности.", ephemeral=True)

    @app_commands.command(name="cmd", description="Персональное секретное меню управления")
    async def cmd_menu(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔐 Секретное меню консоли",
            description="Доступ подтвержден. Все системы работают в штатном режиме.",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="reset", description="Полный перезапуск процесса бота")
    @app_commands.default_permissions(administrator=True)
    async def reset_bot(self, interaction: discord.Interaction):
        with open("restart_queue.txt", "w") as f:
            f.write("restart")
        await interaction.response.send_message("🔄 Процесс завершен. Хостинг автоматизирует перезапуск...", ephemeral=True)
        os._exit(0)

    @app_commands.command(name="обнять", description="Обнять пользователя (Задержка повтора: 3 минуты)")
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
            m, s = divmod(int(error.retry_after), 60)
            await interaction.response.send_message(f"⏳ Перезарядка команды! Попробуйте через {m} мин. {s} сек.", ephemeral=True)
        else:
            raise error

async def setup(bot):
    await bot.add_cog(UtilsCog(bot))
