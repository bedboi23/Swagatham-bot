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

    # Correct way to define a group within a Cog
    welcome_group = app_commands.Group(name="welcome", description="Manage welcome system")

    @welcome_group.command(name="channel", description="Set welcome channel")
    @app_commands.describe(channel="Channel to send welcome messages")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        settings.setdefault(guild_id, DEFAULT_SETTINGS.copy())["channel_id"] = channel.id
        save_settings(settings)
        await interaction.response.send_message(f"✅ Welcome channel set to {channel.mention}", ephemeral=True)

    @welcome_group.command(name="color", description="Set embed color")
    @app_commands.describe(color="Hex color (e.g. #FF0000)")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_color(self, interaction: discord.Interaction, color: str):
        color_clean = color.replace('#', '')
        if not is_valid_hex_color(color_clean):
            return await interaction.response.send_message("❌ Invalid hex color!", ephemeral=True)
        
        guild_id = str(interaction.guild.id)
        settings.setdefault(guild_id, DEFAULT_SETTINGS.copy())["color"] = f"#{color_clean}"
        save_settings(settings)
        await interaction.response.send_message(f"✅ Embed color set to `#{color_clean}`!", ephemeral=True)

    @welcome_group.command(name="image", description="Set welcome embed image/GIF")
    @app_commands.describe(url="Image or GIF URL")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_image(self, interaction: discord.Interaction, url: str):
        if not is_valid_url(url):
            return await interaction.response.send_message("❌ Invalid URL!", ephemeral=True)
        
        guild_id = str(interaction.guild.id)
        settings.setdefault(guild_id, DEFAULT_SETTINGS.copy())["image_url"] = url
        save_settings(settings)
        await interaction.response.send_message("✅ Welcome image updated!", ephemeral=True)

    @welcome_group.command(name="thumbnail", description="Toggle user avatar thumbnail")
    @app_commands.describe(use_avatar="Use user avatar as thumbnail?")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_thumbnail(self, interaction: discord.Interaction, use_avatar: bool):
        guild_id = str(interaction.guild.id)
        settings.setdefault(guild_id, DEFAULT_SETTINGS.copy())["use_user_avatar"] = use_avatar
        save_settings(settings)
        status = "enabled" if use_avatar else "disabled"
        await interaction.response.send_message(f"✅ User avatar thumbnail {status}!", ephemeral=True)

    @welcome_group.command(name="preview", description="Preview current welcome embed")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_preview(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        g_set = settings.get(guild_id, DEFAULT_SETTINGS)
        
        embed = discord.Embed(
            title=g_set.get("title", DEFAULT_SETTINGS["title"]).format(
                user=interaction.user.mention, username=interaction.user.display_name,
                server=interaction.guild.name, membercount=interaction.guild.member_count
            ),
            description=g_set.get("description", DEFAULT_SETTINGS["description"]).format(
                user=interaction.user.mention, username=interaction.user.display_name,
                server=interaction.guild.name, membercount=interaction.guild.member_count
            ),
            color=discord.Color.from_str(g_set.get("color", DEFAULT_SETTINGS["color"])),
            timestamp=datetime.utcnow()
        )
        
        if g_set.get("use_user_avatar", True):
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        if g_set.get("image_url"):
            embed.set_image(url=g_set["image_url"])
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ... (You can add the title, description, and toggle commands back following this same pattern)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()

async def main():
    async with bot:
        await bot.add_cog(WelcomeCog(bot))
        await bot.start(os.getenv("TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())
