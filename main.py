#!/usr/bin/env python3
# A simple discord bot that can be configured to remind a given role
# on a schedule.
# 
# The bot's configuration file allows for the following options:
#
#   - token: The bot's token
#   - role: The role to be reminded
#   - channel: The channel to send the reminder in
#   - schedule: A list of objects representing weekly events
#       - day: The day of the week to send the reminder
#       - time: The time of day to send the reminder
#       - message: The message to send
#   - timezone: The timezone to use for scheduling
#   - control_channel: The channel to listen for commands in
#   - control_role: The role that can use commands
#   - control_prefix: The prefix to use for commands
#
# A couple of hours before each event, the bot will first send a 
# reminder to the control channel, with a message that includes the
# event's time and message.  The message sent to the control channel
# will have a preapplied reaction that can be used to cancel the event,
# if it's deemed necessary.  If the event is not cancelled, the bot
# will send the event's message to the configured channel at the
# configured time.

import asyncio
import datetime
import json
import logging
import os
import sys
import time

import discord
from discord.ext import commands

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the configuration file
with open('config.json') as f:
    config = json.load(f)

# Configure all intents:
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True
intents.message_reactions = True

# Create the bot
bot = commands.Bot(command_prefix=config['control_prefix'], intents=intents)

# setup handlers for basic commands
@bot.command()
async def ping(ctx):
    """Responds with a simple pong message"""
    await ctx.send('pong!')

@bot.command()
async def info(ctx):
    """Responds with information about the bot - only available to the control role"""
    if config['control_role'] not in [role.name for role in ctx.author.roles]:
        await ctx.send('You do not have permission to use this command.')
        return
    await ctx.send('I am a simple reminder bot.')
    await ctx.send('I am currently configured to remind the {} role on the following schedule:'.format(config['role']))
    for event in config['schedule']:
        await ctx.send('  - {} {}: {}'.format(event['day'], event['time'], event['message']))


async def event_reminder(event):
    """
    Sends a reminder to the control channel, and then sends the event message to the configured channel
    """
    while True:
        # Calculate actual time of the next occurance of this event
        now = datetime.datetime.now(datetime.timezone.utc)
        # Send the reminder to the control channel
        channel = bot.get_channel(config['control_channel'])
        message = await channel.send('Reminder: {} {} {}'.format(event['day'], event['time'], event['message']))

        # Add a reaction to the message
        await message.add_reaction('❌')

        # Wait for a reaction from a control role, or for the event to occur
        def check(reaction, user):
            return user != bot.user and reaction.message.id == message.id and config['control_role'] in [role.name for role in user.roles]
        while time.time() < event['time']:
            try:
                # calc remaining time
                remaining = event['time'] - time.time()
                reaction, user = await bot.wait_for('reaction_add', timeout=(event['time'] - time.time()).seconds, check=check)
            except asyncio.TimeoutError:
                pass
            else:
                if reaction.emoji == '❌':
                    await channel.send('Event cancelled.')
                    continue

        # Send the event message to the configured channel
        channel = bot.get_channel(config['channel'])
        await channel.send(event['message'])
