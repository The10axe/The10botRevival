import asyncio
import discord
from discord import app_commands

from typing import Optional

import os
from dotenv import load_dotenv
import re

import logging
from datetime import datetime

load_dotenv()

MY_GUILD = discord.Object(id=int(os.getenv('DISCORD_HOME_GUILD')))  # replace with your guild id

log_filename = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
file_handler = logging.FileHandler(filename=f'log/{log_filename}.log', encoding='utf-8', mode='w')
console_handler = logging.StreamHandler()
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger = logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    

    #async def on_message(self, message):
    #    print(f'Message from {message.author}: {message.content}')

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)
            

intents = discord.Intents.default()
# intents.message_content = True

client = MyClient(intents=intents)

@client.event
async def on_ready():
    logging.info(f'Logged in as {client.user} (ID: {client.user.id})')
    release = os.getenv("RELEASE")
    if(release == "True"):
        logging.info("Release mode")
        for guild in client.guilds:
            client.tree.copy_global_to(guild=guild)
            await client.tree.sync(guild=guild)
    else: 
        logging.info("Development mode")
        client.tree.copy_global_to(guild=MY_GUILD)
        await client.tree.sync(guild=MY_GUILD)


@client.tree.command()
@app_commands.describe(
    remindmein='In how many time I shall remind you (#d#h#min#s)',
    message='The message I shall remind you with'
)
async def remind_me(interaction: discord.Interaction, remindmein: str, message: Optional[str] = None):
    """Reminds you with a message after a certain amount of time."""
    def parse_time_string(time_str: str) -> int:
        time_units = {
            'j': 86400,  # days
            'd': 86400,  # days (alternative)
            'h': 3600,   # hours
            'min': 60,   # minutes
            'm': 60,     # minutes (alternative)
            's': 1       # seconds
        }

        total_seconds = 0
        pattern = re.compile(r'(\d+)(j|h|min|m|s)')
        matches = pattern.findall(time_str)

        for value, unit in matches:
            total_seconds += int(value) * time_units[unit]

        return total_seconds

    def parse_time_string_colon_format(time_str: str) -> int:
        time_units = [86400, 3600, 60, 1]  # days, hours, minutes, seconds
        total_seconds = 0
        parts = time_str.split(':')

        for i, part in enumerate(reversed(parts)):
            total_seconds += int(part) * time_units[i]

        return total_seconds

    def format_time_string(seconds: int) -> str:
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return f'{days}:{hours:02}:{minutes:02}:{seconds:02}'

    # Check if the time string contains colons
    if ':' in remindmein:
        remindmein_seconds = parse_time_string_colon_format(remindmein)
    else:
        remindmein_seconds = parse_time_string(remindmein)

    formatted_time = format_time_string(remindmein_seconds)


    if(message == None):
        await interaction.response.send_message(f'I will remind you in {formatted_time}', ephemeral=True, silent=True)
        logging.info(f"{interaction.user.mention} used remind me for {formatted_time}")
    else:
        await interaction.response.send_message(f'I will remind you in {formatted_time} with the message: {message}', ephemeral=True, silent=True)
        logging.info(f"{interaction.user.mention} used remind me for {formatted_time} with message {message}")
        
    await asyncio.sleep(remindmein_seconds)

    if(message == None):
        await interaction.user.send(f"{interaction.user.mention} you asked me to remind you now")
        logging.info(f"{interaction.user.mention} ended reminder")
    else:
        await interaction.user.send(f"{interaction.user.mention} you asked me to remind you: {message}")
        logging.info(f"{interaction.user.mention} ended reminder with message {message}")


@client.tree.command()
@app_commands.describe(
    member='The member you want to get information about'
)
async def member_info(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    """Displays information about a member."""
    member = member or interaction.user

    logging.info(f"{interaction.user.mention} used member info for {member}")

    embed = discord.Embed(title=f"Information for {member}", color=discord.Color.blue())
    embed.set_thumbnail(url=member.avatar.url)
    embed.add_field(name="Username", value=member.name, inline=True)
    embed.add_field(name="Discriminator", value=member.discriminator, inline=True)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Status", value=member.status, inline=True)
    embed.add_field(name="Top Role", value=member.top_role.mention, inline=True)
    embed.add_field(name="Joined Server", value=discord.utils.format_dt(member.joined_at), inline=True)
    embed.add_field(name="Joined Discord", value=discord.utils.format_dt(member.created_at), inline=True)

    await interaction.response.send_message(embed=embed)
    
@client.tree.command()
async def bot_info(interaction: discord.Interaction):
    """Displays information about the bot."""

    logging.info(f"{interaction.user.mention} used bot info")
    embed = discord.Embed(title="Bot Information", color=discord.Color.green())
    embed.set_thumbnail(url=client.user.avatar.url)
    embed.add_field(name="Bot Name", value=client.user.name, inline=True)
    embed.add_field(name="Bot ID", value=client.user.id, inline=True)
    embed.add_field(name="Servers", value=len(client.guilds), inline=True)
    embed.add_field(name="Users", value=sum(guild.member_count for guild in client.guilds), inline=True)
    embed.add_field(name="Latency", value=f"{client.latency * 1000:.2f} ms", inline=True)

    await interaction.response.send_message(embed=embed)


client.run(os.getenv('DISCORD_TOKEN'), log_handler=logger, log_level=logging.INFO)
