import os
import json
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import asyncio

# Bot setup
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

DATA_FILE = 'welcome_settings.json'

# --- FIXED: Triple quotes for multi-line string ---
DEFAULT_SETTINGS = {
    "enabled": True,
    "channel_id": None,
    "title": "Welcome to {server}!",
    "description": """Hey {user}!

Welcome to the server! We now have {membercount} members!
Enjoy your stay! 🎉""",
    "color": "#00ff00",
    "image_url": None,
    "use_user_avatar": True,
    "footer": "Welcome aboard! 🚀"
}

def load_settings():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_settings(settings_data):
    with open(DATA_FILE, 'w') as f:
        json.dump(settings_data, f, indent=2)

settings = load_settings()

def is_valid_url(url):
    return url.startswith(('http://', 'https://'))

def is_valid_hex_color(color):
    if color.startswith('#'):
        color = color[1:]
    return len(color) in (3, 6) and all(c in '0123456789abcdefABCDEF' for c in color)

class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Correct Slash Command Group
    welcome_group = app_commands.Group(name="welcome", description="Manage welcome system")

    @welcome_group.command(name="channel", description="Set welcome channel")
    @app_commands.describe(channel="Channel to send welcome messages")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        settings.setdefault(guild_id, DEFAULT_SETTINGS.copy())["channel_id"] = channel.id
        save_settings(settings)
        await interaction.response.send_message(f"✅ Welcome channel set to {channel.mention}", ephemeral=True)

    @welcome_group.command(name="toggle", description="Enable/disable welcome system")
    @app_commands.describe(enabled="True to enable, False to disable")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_toggle(self, interaction: discord.Interaction, enabled: bool):
        guild_id = str(interaction.guild.id)
        settings.setdefault(guild_id, DEFAULT_SETTINGS.copy())["enabled"] = enabled
        save_settings(settings)
        status = "enabled" if enabled else "disabled"
        await interaction.response.send_message(f"✅ Welcome system {status}!", ephemeral=True)

    @welcome_group.command(name="color", description="Set embed color")
    @app_commands.describe(color="Hex color (e.g. #FF6B6B)")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_color(self, interaction: discord.Interaction, color: str):
        color_clean = color.replace('#', '')
        if not is_valid_hex_color(color_clean):
            return await interaction.response.send_message("❌ Invalid hex color!", ephemeral=True)
        guild_id = str(interaction.guild.id)
        settings.setdefault(guild_id, DEFAULT_SETTINGS.copy())["color"] = f"#{color_clean}"
        save_settings(settings)
        await interaction.response.send_message(f"✅ Color set to `#{color_clean}`", ephemeral=True)

    @welcome_group.command(name="image", description="Set welcome image/GIF")
    @app_commands.describe(url="URL of the image or GIF")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_image(self, interaction: discord.Interaction, url: str):
        if not is_valid_url(url):
            return await interaction.response.send_message("❌ Invalid URL!", ephemeral=True)
        guild_id = str(interaction.guild.id)
        settings.setdefault(guild_id, DEFAULT_SETTINGS.copy())["image_url"] = url
        save_settings(settings)
        await interaction.response.send_message("✅ Welcome image updated!", ephemeral=True)

    @welcome_group.command(name="thumbnail", description="Toggle user avatar thumbnail")
    @app_commands.describe(use_avatar="True = ON, False = OFF")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_thumbnail(self, interaction: discord.Interaction, use_avatar: bool):
        guild_id = str(interaction.guild.id)
        settings.setdefault(guild_id, DEFAULT_SETTINGS.copy())["use_user_avatar"] = use_avatar
        save_settings(settings)
        status = "ON" if use_avatar else "OFF"
        await interaction.response.send_message(f"✅ User avatar thumbnail: **{status}**", ephemeral=True)

    @welcome_group.command(name="title", description="Set welcome title")
    @app_commands.describe(title="Title (supports {user}, {server}, etc)")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_title(self, interaction: discord.Interaction, title: str):
        guild_id = str(interaction.guild.id)
        settings.setdefault(guild_id, DEFAULT_SETTINGS.copy())["title"] = title
        save_settings(settings)
        await interaction.response.send_message("✅ Welcome title updated!", ephemeral=True)

    @welcome_group.command(name="description", description="Set welcome description")
    @app_commands.describe(description="Description (supports {user}, {server}, {membercount})")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_description(self, interaction: discord.Interaction, description: str):
        guild_id = str(interaction.guild.id)
        # Handle manual \n if user types them in slash commands
        processed_desc = description.replace("\\n", "\n")
        settings.setdefault(guild_id, DEFAULT_SETTINGS.copy())["description"] = processed_desc
        save_settings(settings)
        await interaction.response.send_message("✅ Welcome description updated!", ephemeral=True)

    @welcome_group.command(name="footer", description="Set welcome footer")
    @app_commands.describe(footer="Footer text")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_footer(self, interaction: discord.Interaction, footer: str):
        guild_id = str(interaction.guild.id)
        settings.setdefault(guild_id, DEFAULT_SETTINGS.copy())["footer"] = footer
        save_settings(settings)
        await interaction.response.send_message("✅ Welcome footer updated!", ephemeral=True)

    @welcome_group.command(name="preview", description="See live preview")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_preview(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        g_set = settings.get(guild_id, DEFAULT_SETTINGS)
        
        embed = discord.Embed(
            title=g_set.get("title").format(user=interaction.user.mention, username=interaction.user.display_name, server=interaction.guild.name, membercount=interaction.guild.member_count),
            description=g_set.get("description").format(user=interaction.user.mention, username=interaction.user.display_name, server=interaction.guild.name, membercount=interaction.guild.member_count),
            color=discord.Color.from_str(g_set.get("color")),
            timestamp=datetime.utcnow()
        )
        if g_set.get("use_user_avatar"):
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
        if g_set.get("image_url"):
            embed.set_image(url=g_set["image_url"])
        if g_set.get("footer"):
            embed.set_footer(text=g_set["footer"].format(user=interaction.user.display_name, server=interaction.guild.name))

        await interaction.response.send_message("📸 **Preview:**", embed=embed, ephemeral=True)

    @welcome_group.command(name="reset", description="Reset to defaults")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_reset(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        settings[guild_id] = DEFAULT_SETTINGS.copy()
        save_settings(settings)
        await interaction.response.send_message("♻️ Settings reset to default!", ephemeral=True)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()

@bot.event
async def on_member_join(member):
    guild_id = str(member.guild.id)
    g_set = settings.get(guild_id, DEFAULT_SETTINGS)
    
    if not g_set.get("enabled") or not g_set.get("channel_id"):
        return

    channel = bot.get_channel(int(g_set["channel_id"]))
    if not channel: return

    embed = discord.Embed(
        title=g_set["title"].format(user=member.mention, username=member.display_name, server=member.guild.name, membercount=member.guild.member_count),
        description=g_set["description"].format(user=member.mention, username=member.display_name, server=member.guild.name, membercount=member.guild.member_count),
        color=discord.Color.from_str(g_set["color"]),
        timestamp=datetime.utcnow()
    )
    if g_set["use_user_avatar"]:
        embed.set_thumbnail(url=member.display_avatar.url)
    if g_set["image_url"]:
        embed.set_image(url=g_set["image_url"])
    if g_set["footer"]:
        embed.set_footer(text=g_set["footer"].format(user=member.display_name, server=member.guild.name))
    
    await channel.send(embed=embed)

async def main():
    async with bot:
        await bot.add_cog(WelcomeCog(bot))
        await bot.start(os.getenv("TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())
