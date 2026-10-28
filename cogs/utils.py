import discord
from discord.ext import commands
from discord import app_commands
import psutil
import os
import asyncio
import datetime

PASSWORD_OWNER = "nursat2011n"
PASSWORD_FRIEND = "blackwork"
FRIEND_ID = 1324350693292773438

class PasswordModal(discord.ui.Modal, title="🔐 Секретный доступ VoidPulse"):
    password_input = discord.ui.TextInput(
        label="Введите ключ-пароль",
        placeholder="Пароль...",
        required=True,
        style=discord.TextStyle.short
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        inp = self.password_input.value.strip()
        user_id = interaction.user.id

        is_owner = (inp == PASSWORD_OWNER)
        is_friend = (inp == PASSWORD_FRIEND or user_id == FRIEND_ID) and (inp == PASSWORD_FRIEND or inp == PASSWORD_OWNER)

        if is_owner or is_friend:
            role_title = "Владелец" if is_owner else "Доверенный Администратор"
            embed = discord.Embed(
                title="🖥️ КОНСОЛЬ УПРАВЛЕНИЯ VOIDPULSE",
                description=f"✅ **Доступ разрешен.** \nУровень прав: `{role_title}`\n\nВыберите действие на защищенной панели ниже:",
                color=discord.Color.gold(),
                timestamp=datetime.datetime.now()
            )
            embed.set_footer(text="VoidPulse Secure Core")
            await interaction.response.send_message(embed=embed, view=AdminPanelView(self.bot), ephemeral=True)
        else:
            embed = discord.Embed(title="⛔ Отказ в доступе", description="Введен неверный пароль авторизации.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

class SayModal(discord.ui.Modal, title="📢 Отправить объявление"):
    channel_id = discord.ui.TextInput(
        label="ID канала (пусто = текущий)",
        placeholder="1554536535247032401",
        required=False,
        style=discord.TextStyle.short
    )
    title_text = discord.ui.TextInput(
        label="Заголовок",
        default="Объявление",
        required=True,
        style=discord.TextStyle.short
    )
    body_text = discord.ui.TextInput(
        label="Текст сообщения",
        placeholder="Введите текст...",
        required=True,
        style=discord.TextStyle.paragraph
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            target_channel = interaction.channel
            if self.channel_id.value.strip():
                cid = int(self.channel_id.value.strip())
                ch = self.bot.get_channel(cid)
                if ch:
                    target_channel = ch

            embed = discord.Embed(
                title=f"📢 {self.title_text.value}",
                description=self.body_text.value,
                color=discord.Color.purple(),
                timestamp=datetime.datetime.now()
            )
            embed.set_footer(text="Официальное объявление VoidPulse")
            await target_channel.send(embed=embed)
            await interaction.followup.send("✅ Сообщение успешно отправлено!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка отправки: {e}", ephemeral=True)

class AdminPanelView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot

    @discord.ui.button(label="🔄 Перезагрузить модули", style=discord.ButtonStyle.primary, custom_id="gui_reload")
    async def reload_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.bot.reload_extension(f'cogs.{filename[:-3]}')
        await self.bot.tree.sync()
        await interaction.followup.send("✅ Все модули бота успешно пересобраны и синхронизированы!", ephemeral=True)

    @discord.ui.button(label="📊 Статус бота", style=discord.ButtonStyle.secondary, custom_id="gui_status")
    async def status_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        ram = psutil.virtual_memory()
        cpu = psutil.cpu_percent()
        embed = discord.Embed(
            title="🖥️ Мониторинг ресурсов (Render)",
            color=discord.Color.dark_theme(),
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="ЦП (CPU)", value=f"`{cpu}%`", inline=True)
        embed.add_field(name="ОЗУ (RAM)", value=f"`{ram.percent}%`\n({round(ram.used/1024/1024)}MB / {round(ram.total/1024/1024)}MB)", inline=True)
        embed.add_field(name="Задержка", value=f"`{round(self.bot.latency * 1000)}ms`", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📢 Объявление", style=discord.ButtonStyle.success, custom_id="gui_say")
    async def say_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SayModal(self.bot))

    @discord.ui.button(label="🚨 Рестарт", style=discord.ButtonStyle.danger, custom_id="gui_reset")
    async def reset_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⏳ Инициализация перезапуска...", ephemeral=True)

        ram = psutil.virtual_memory()
        cpu = psutil.cpu_percent()
        latency = round(self.bot.latency * 1000)

        embed = discord.Embed(
            title="⚠️ ВНИМАНИЕ: ПЕРЕЗАГРУЗКА СИСТЕМЫ!",
            description=f"⏱ До перезагрузки осталось: **20 сек**\n\n"
                        f"📊 **Ресурсы перед перезапуском:**\n"
                        f"• **ЦП:** `{cpu}%`\n"
                        f"• **ОЗУ:** `{ram.percent}%`\n"
                        f"• **Пинг:** `{latency}ms`",
            color=discord.Color.red()
        )

        msg = await interaction.channel.send(embed=embed)

        for i in range(19, -1, -1):
            await asyncio.sleep(1)
            embed.description = f"⏱ До перезагрузки осталось: **{i} сек**\n\n" \
                                f"📊 **Ресурсы перед перезапуском:**\n" \
                                f"• **ЦП:** `{cpu}%`\n" \
                                f"• **ОЗУ:** `{ram.percent}%`\n" \
                                f"• **Пинг:** `{latency}ms`"
            await msg.edit(embed=embed)

        embed.description = "🔴 **Перезагрузка ядра выполняется прямо сейчас...**"
        await msg.edit(embed=embed)
        os._exit(0)

class UtilsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="console", description="Секретная консоль управления (требуется пароль)")
    async def console_menu(self, interaction: discord.Interaction):
        await interaction.response.send_modal(PasswordModal(self.bot))

    @app_commands.command(name="обнять", description="Крепко обнять пользователя (Задержка: 3 минуты)")
    @app_commands.checks.cooldown(1, 180, key=lambda i: i.user.id)
    async def hug(self, interaction: discord.Interaction, member: discord.Member):
        embed = discord.Embed(
            title="🤗 Время обнимашек!",
            description=f"**{interaction.user.display_name}** крепко обнял(-а) **{member.display_name}**!\n\n*Тепло передано успешно ❤️*",
            color=discord.Color.pink()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="say", description="Отправить системное сообщение")
    @app_commands.default_permissions(administrator=True)
    async def say(self, interaction: discord.Interaction, текст: str, титл: str = "Объявление", игрок: discord.Member = None):
        embed = discord.Embed(title=f"📢 {титл}", description=текст, color=discord.Color.purple())
        if игрок:
            try:
                await игрок.send(embed=embed)
                await interaction.response.send_message(f"✅ Сообщение отправлено в ЛС {игрок.mention}", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message("❌ Ошибка: У пользователя закрыты личные сообщения.", ephemeral=True)
        else:
            await interaction.channel.send(embed=embed)
            await interaction.response.send_message("✅ Сообщение отправлено.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(UtilsCog(bot))
