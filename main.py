
import os
import json
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from datetime import datetime
import asyncio

# Bot setup
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Data file path
DATA_FILE = 'welcome_settings.json'

# Default welcome settings
DEFAULT_SETTINGS = {
    "enabled": True,
    "channel_id": None,
    "title": "Welcome to {server}!",
    "description": "Hey {user}!"

Welcome to the server! We now have {membercount} members!
"Enjoy your stay! 🎉",
    "color": "#00ff00",
    "image_url": None,
    "use_user_avatar": True,
    "footer": "Welcome aboard! 🚀"
}

# Load settings from JSON
def load_settings():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save settings to JSON
def save_settings(settings):
    with open(DATA_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

settings = load_settings()

@bot.event
async def on_ready():
    print(f'{bot.user} has logged in!')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

@bot.event
async def on_member_join(member):
    guild_id = str(member.guild.id)
    if guild_id not in settings:
        settings[guild_id] = DEFAULT_SETTINGS.copy()
        save_settings(settings)
    
    guild_settings = settings[guild_id]
    
    # Check if welcome is enabled
    if not guild_settings.get("enabled", True):
        return
    
    # Get channel
    channel_id = guild_settings.get("channel_id")
    if not channel_id:
        return
    
    channel = bot.get_channel(int(channel_id))
    if not channel:
        return  # Channel deleted or inaccessible
    
    try:
        # Prepare embed
        embed = discord.Embed(
            title=guild_settings.get("title", DEFAULT_SETTINGS["title"]).format(
                user=member.mention,
                username=member.display_name,
                server=member.guild.name,
                membercount=member.guild.member_count
            ),
            description=guild_settings.get("description", DEFAULT_SETTINGS["description"]).format(
                user=member.mention,
                username=member.display_name,
                server=member.guild.name,
                membercount=member.guild.member_count
            ),
            color=discord.Color.from_str(guild_settings.get("color", DEFAULT_SETTINGS["color"])),
            timestamp=datetime.utcnow()
        )
        
        # Set footer
        footer_text = guild_settings.get("footer", DEFAULT_SETTINGS["footer"])
        if footer_text:
            embed.set_footer(text=footer_text.format(
                user=member.display_name,
                server=member.guild.name
            ))
        
        # Set thumbnail (user avatar)
        if guild_settings.get("use_user_avatar", True):
            embed.set_thumbnail(url=member.display_avatar.url)
        
        # Set image (supports GIFs)
        image_url = guild_settings.get("image_url")
        if image_url:
            # Validate image URL
            if is_valid_url(image_url):
                embed.set_image(url=image_url)
        
        await channel.send(embed=embed)
        
    except discord.HTTPException:
        pass  # Silently fail if no embed permissions
    except Exception as e:
        print(f"Error sending welcome: {e}")

def is_valid_url(url):
    """Basic URL validation"""
    if not url.startswith(('http://', 'https://')):
        return False
    return True

def is_valid_hex_color(color):
    """Validate hex color"""
    if color.startswith('#'):
        color = color[1:]
    return len(color) in (3, 6) and all(c in '0123456789abcdefABCDEF' for c in color)

# Welcome cog
class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="welcome", description="Manage welcome system")
    @app_commands.describe(subcommand="Welcome system subcommand")
    async def welcome_group(self, interaction: discord.Interaction, subcommand: str):
        pass

    @welcome_group.command(name="channel", description="Set welcome channel")
    @app_commands.describe(channel="Channel to send welcome messages")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        if guild_id not in settings:
            settings[guild_id] = DEFAULT_SETTINGS.copy()
        
        settings[guild_id]["channel_id"] = channel.id
        save_settings(settings)
        
        await interaction.response.send_message(
            f"✅ Welcome channel set to {channel.mention}", 
            ephemeral=True
        )

    @welcome_group.command(name="title", description="Set welcome embed title")
    @app_commands.describe(title="Embed title (supports {user}, {username}, {server}, {membercount})")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_title(self, interaction: discord.Interaction, title: str):
        if len(title) > 256:
            await interaction.response.send_message("❌ Title too long (max 256 chars)", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)
        if guild_id not in settings:
            settings[guild_id] = DEFAULT_SETTINGS.copy()
        
        settings[guild_id]["title"] = title
        save_settings(settings)
        
        await interaction.response.send_message("✅ Welcome title updated!", ephemeral=True)

    @welcome_group.command(name="description", description="Set welcome embed description")
    @app_commands.describe(description="Embed description (supports {user}, {username}, {server}, {membercount})")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_description(self, interaction: discord.Interaction, description: str):
        if len(description) > 4096:
            await interaction.response.send_message("❌ Description too long (max 4096 chars)", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)
        if guild_id not in settings:
            settings[guild_id] = DEFAULT_SETTINGS.copy()
        
        settings[guild_id]["description"] = description
        save_settings(settings)
        
        await interaction.response.send_message("✅ Welcome description updated!", ephemeral=True)

    @welcome_group.command(name="color", description="Set embed color")
    @app_commands.describe(color="Hex color (e.g. #FF0000 or FF0000)")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_color(self, interaction: discord.Interaction, color: str):
        color_clean = color.replace('#', '')
        if not is_valid_hex_color(color_clean):
            await interaction.response.send_message("❌ Invalid hex color! Use format like #FF0000 or FF0000", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)
        if guild_id not in settings:
            settings[guild_id] = DEFAULT_SETTINGS.copy()
        
        settings[guild_id]["color"] = f"#{color_clean}"
        save_settings(settings)
        
        await interaction.response.send_message(f"✅ Embed color set to `{color}`!", ephemeral=True)

    @welcome_group.command(name="image", description="Set welcome embed image/GIF")
    @app_commands.describe(url="Image or GIF URL")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_image(self, interaction: discord.Interaction, url: str):
        if not is_valid_url(url):
            await interaction.response.send_message("❌ Invalid URL! Must start with http:// or https://", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)
        if guild_id not in settings:
            settings[guild_id] = DEFAULT_SETTINGS.copy()
        
        settings[guild_id]["image_url"] = url
        save_settings(settings)
        
        await interaction.response.send_message("✅ Welcome image updated!", ephemeral=True)

    @welcome_group.command(name="thumbnail", description="Toggle user avatar thumbnail")
    @app_commands.describe(use_avatar="Use user avatar as thumbnail? (True/False)")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_thumbnail(self, interaction: discord.Interaction, use_avatar: bool):
        guild_id = str(interaction.guild.id)
        if guild_id not in settings:
            settings[guild_id] = DEFAULT_SETTINGS.copy()
        
        settings[guild_id]["use_user_avatar"] = use_avatar
        save_settings(settings)
        
        status = "enabled" if use_avatar else "disabled"
        await interaction.response.send_message(f"✅ User avatar thumbnail {status}!", ephemeral=True)

    @welcome_group.command(name="footer", description="Set welcome embed footer")
    @app_commands.describe(footer="Footer text")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_footer(self, interaction: discord.Interaction, footer: str):
        if len(footer) > 2048:
            await interaction.response.send_message("❌ Footer too long (max 2048 chars)", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)
        if guild_id not in settings:
            settings[guild_id] = DEFAULT_SETTINGS.copy()
        
        settings[guild_id]["footer"] = footer
        save_settings(settings)
        
        await interaction.response.send_message("✅ Welcome footer updated!", ephemeral=True)

    @welcome_group.command(name="toggle", description="Enable/disable welcome system")
    @app_commands.describe(enabled="Enable welcome messages?")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_toggle(self, interaction: discord.Interaction, enabled: bool):
        guild_id = str(interaction.guild.id)
        if guild_id not in settings:
            settings[guild_id] = DEFAULT_SETTINGS.copy()
        
        settings[guild_id]["enabled"] = enabled
        save_settings(settings)
        
        status = "enabled" if enabled else "disabled"
        await interaction.response.send_message(f"✅ Welcome system {status}!", ephemeral=True)

    @welcome_group.command(name="preview", description="Preview current welcome embed")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_preview(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if guild_id not in settings:
            settings[guild_id] = DEFAULT_SETTINGS.copy()
        
        guild_settings = settings[guild_id]
        
        # Create preview embed (simulate new member)
        embed = discord.Embed(
            title=guild_settings.get("title", DEFAULT_SETTINGS["title"]).format(
                user="@preview",
                username="PreviewUser",
                server=interaction.guild.name,
                membercount=interaction.guild.member_count
            ),
            description=guild_settings.get("description", DEFAULT_SETTINGS["description"]).format(
                user="@preview",
                username="PreviewUser",
                server=interaction.guild.name,
                membercount=interaction.guild.member_count
            ),
            color=discord.Color.from_str(guild_settings.get("color", DEFAULT_SETTINGS["color"])),
            timestamp=datetime.utcnow()
        )
        
        if guild_settings.get("use_user_avatar", True):
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        image_url = guild_settings.get("image_url")
        if image_url and is_valid_url(image_url):
            embed.set_image(url=image_url)
        
        footer_text = guild_settings.get("footer", DEFAULT_SETTINGS["footer"])
        if footer_text:
            embed.set_footer(text=footer_text.format(
                user="PreviewUser",
                server=interaction.guild.name
            ))
        
        embed.set_author(name="Welcome Preview", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @welcome_group.command(name="reset", description="Reset to default settings")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_reset(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        settings[guild_id] = DEFAULT_SETTINGS.copy()
        save_settings(settings)
        
        await interaction.response.send_message("✅ Settings reset to default!", ephemeral=True)

# Error handler for permission checks
async def check_permissions(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ You need **Administrator** permissions to use this command!", 
            ephemeral=True
        )

# Add cog
async def main():
    async with bot:
        await bot.add_cog(WelcomeCog(bot))
        await bot.start(os.environ["TOKEN"])

if __name__ == "__main__":
    asyncio.run(main())