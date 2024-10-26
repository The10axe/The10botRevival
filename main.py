import asyncio
import discord
from discord import app_commands

from typing import Optional

import os
from dotenv import load_dotenv
import re

load_dotenv()

MY_GUILD = discord.Object(id=int(os.getenv('DISCORD_HOME_GUILD')))  # replace with your guild id

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
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    release = os.getenv("RELEASE")
    if(release == "True"):
        print("Release mode")
        for guild in client.guilds:
            client.tree.copy_global_to(guild=guild)
            await client.tree.sync(guild=guild)
    else: 
        client.tree.copy_global_to(guild=MY_GUILD)
        await client.tree.sync(guild=MY_GUILD)


@client.tree.command()
async def hello(interaction: discord.Interaction):
    """Says hello!"""
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')


@client.tree.command()
@app_commands.describe(
    first_value='The first value you want to add something to',
    second_value='The value you want to add to the first value',
)
async def add(interaction: discord.Interaction, first_value: int, second_value: int):
    """Adds two numbers together."""
    await interaction.response.send_message(f'{first_value} + {second_value} = {first_value + second_value}')


# The rename decorator allows us to change the display of the parameter on Discord.
# In this example, even though we use `text_to_send` in the code, the client will use `text` instead.
# Note that other decorators will still refer to it as `text_to_send` in the code.
@client.tree.command()
@app_commands.rename(text_to_send='text')
@app_commands.describe(text_to_send='Text to send in the current channel')
async def send(interaction: discord.Interaction, text_to_send: str):
    """Sends the text into the current channel."""
    await interaction.response.send_message(text_to_send)


# To make an argument optional, you can either give it a supported default argument
# or you can mark it as Optional from the typing standard library. This example does both.
@client.tree.command()
@app_commands.describe(member='The member you want to get the joined date from; defaults to the user who uses the command')
async def joined(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    """Says when a member joined."""
    # If no member is explicitly provided then we use the command user here
    member = member or interaction.user

    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(f'{member} joined {discord.utils.format_dt(member.joined_at)}')


# A Context Menu command is an app command that can be run on a member or on a message by
# accessing a menu within the client, usually via right clicking.
# It always takes an interaction as its first parameter and a Member or Message as its second parameter.

# This context menu command only works on members
@client.tree.context_menu(name='Show Join Date')
async def show_join_date(interaction: discord.Interaction, member: discord.Member):
    # The format_dt function formats the date time into a human readable representation in the official client
    await interaction.response.send_message(f'{member} joined at {discord.utils.format_dt(member.joined_at)}')

@client.tree.command()
@app_commands.describe(
    remindmein='Le temps dans lequel je dois vous rappeler',
    message='Le message que je dois vous rappeler',
    globale='Si je dois vous le rappeler en global'
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

    # Check if the time string contains colons
    if ':' in remindmein:
        remindmein_seconds = parse_time_string_colon_format(remindmein)
    else:
        remindmein_seconds = parse_time_string(remindmein)
    globale = not globale
    remindmein_seconds = parse_time_string(remindmein)
    def format_time_string(seconds: int) -> str:
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return f'{days}:{hours:02}:{minutes:02}:{seconds:02}'

    formatted_time = format_time_string(remindmein_seconds)
    if(message == None):
        await interaction.response.send_message(f'Je vais vous rappeler dans {formatted_time} secondes', ephemeral=True, silent=True)
    else:
        await interaction.response.send_message(f'Je vais vous rappeler dans {formatted_time} secondes avec le message : {message}', ephemeral=True, silent=True)
    
    await asyncio.sleep(remindmein_seconds)

    if(message == None):
        await interaction.user.send(f"{interaction.user.mention} vous m'avez demander de vous rappeler maintenant")
    else:
        await interaction.user.send(f"{interaction.user.mention} vous m'avez demander de vous rappeler: {message}")
    
    
    


client.run(os.getenv('DISCORD_TOKEN'))