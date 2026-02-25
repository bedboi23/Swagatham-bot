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
intents.message_content = True # Recommended for prefix bots
bot = commands.Bot(command_prefix='!', intents=intents)

# Data file path
DATA_FILE = 'welcome_settings.json'

# --- FIXED: Used triple quotes for multi-line string ---
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

def save_settings(settings):
    with open(DATA_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

settings = load_settings()

@bot.event
async def on_ready():
    print(f'{bot.user} has logged in!')
    try:
        # Syncing globally for example purposes
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
    
    if not guild_settings.get("enabled", True):
        return
    
    channel_id = guild_settings.get("channel_id")
    if not channel_id:
        return
    
    channel = bot.get_channel(int(channel_id))
    if not channel:
        return 
    
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
        
        footer_text = guild_settings.get("footer", DEFAULT_SETTINGS["footer"])
        if footer_text:
            embed.set_footer(text=footer_text.format(
                user=member.display_name,
                server=member.guild.name
            ))
        
        if guild_settings.get("use_user_avatar", True):
            embed.set_thumbnail(url=member.display_avatar.url)
        
        image_url = guild_settings.get("image_url")
        if image_url and is_valid_url(image_url):
            embed.set_image(url=image_url)
        
        await channel.send(embed=embed)
    except Exception as e:
        print(f"Error sending welcome: {e}")

def is_valid_url(url):
    return url.startswith(('http://', 'https://'))

def is_valid_hex_color(color):
    if color.startswith('#'):
        color = color[1:]
    return len(color) in (3, 6) and all(c in '0123456789abcdefABCDEF' for c in color)

# --- FIXED: Corrected Command Group Structure ---
class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Define the group
    welcome_group = app_commands.Group(name="welcome", description="Manage welcome system")

    @welcome_group.command(name="channel", description="Set welcome channel")
    @app_commands.describe(channel="Channel to send welcome messages")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        if guild_id not in settings:
            settings[guild_id] = DEFAULT_SETTINGS.copy()
        
        settings[guild_id]["channel_id"] = channel.id
        save_settings(settings)
        await interaction.response.send_message(f"✅ Welcome channel set to {channel.mention}", ephemeral=True)

    @welcome_group.command(name="title", description="Set welcome embed title")
    @app_commands.describe(title="Embed title")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_title(self, interaction: discord.Interaction, title: str):
        if len(title) > 256:
            return await interaction.response.send_message("❌ Title too long", ephemeral=True)
        
        guild_id = str(interaction.guild.id)
        settings.setdefault(guild_id, DEFAULT_SETTINGS.copy())["title"] = title
        save_settings(settings)
        await interaction.response.send_message("✅ Welcome title updated!", ephemeral=True)

    @welcome_group.command(name="description", description="Set welcome embed description")
    @app_commands.describe(description="Embed description")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_description(self, interaction: discord.Interaction, description: str):
        if len(description) > 4096:
            return await interaction.response.send_message("❌ Description too long", ephemeral=True)
        
        guild_id = str(interaction.guild.id)
        settings.setdefault(guild_id, DEFAULT_SETTINGS.copy())["description"] = description
        save_settings(settings)
        await interaction.response.send_message("✅ Welcome description updated!", ephemeral=True)

    @welcome_group.command(name="toggle", description="Enable/disable welcome system")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_toggle(self, interaction: discord.Interaction, enabled: bool):
        guild_id = str(interaction.guild.id)
        settings.setdefault(guild_id, DEFAULT_SETTINGS.copy())["enabled"] = enabled
        save_settings(settings)
        status = "enabled" if enabled else "disabled"
        await interaction.response.send_message(f"✅ Welcome system {status}!", ephemeral=True)

    @welcome_group.command(name="preview", description="Preview current welcome embed")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_preview(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        guild_settings = settings.get(guild_id, DEFAULT_SETTINGS)
        
        embed = discord.Embed(
            title=guild_settings.get("title").format(user="@preview", username="PreviewUser", server=interaction.guild.name, membercount=interaction.guild.member_count),
            description=guild_settings.get("description").format(user="@preview", username="PreviewUser", server=interaction.guild.name, membercount=interaction.guild.member_count),
            color=discord.Color.from_str(guild_settings.get("color")),
            timestamp=datetime.utcnow()
        )
        if guild_settings.get("use_user_avatar"):
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Add cog and run
async def main():
    async with bot:
        await bot.add_cog(WelcomeCog(bot))
        # Ensure your TOKEN is in your environment variables
        await bot.start(os.getenv("TOKEN"))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
