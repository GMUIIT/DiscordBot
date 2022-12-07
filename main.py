import asyncio
import datetime
from collections import namedtuple
from discord import utils, Embed, Colour, Intents
from discord.ext import commands
import pytz

from helper import to_local_time, format_time, local_now
import secret


# Bot setup
# We need permissions for sending messages, adding reactions, and managing messages
intents = Intents.all()
bot = commands.Bot(command_prefix=secret.CONTROL_PREFIX, intents=intents)

@bot.event
async def on_ready():
    """
    Prints a message when the bot is ready and starts the event loop.
    """
    print(f"Logged in as {bot.user}")

    # Start the event loop
    bot.loop.create_task(event_loop())

@bot.event
async def on_reaction_add(reaction, user):
    """
    Handles reactions to the control channel messages.
    """
    # Check if the reaction is to a control channel message
    if reaction.message.channel.id != secret.CONTROL_CHANNEL:
        return

    # Check if the user has the control role
    if not utils.get(user.roles, id=secret.CONTROL_ROLE):
        return

    # Check if the reaction is the cancel emoji
    if reaction.emoji != "❌":
        return

    # Cancel the event
    await cancel_event(reaction.message)

async def event_loop():
    """
    The main event loop that sends reminders and messages at the scheduled times.
    """
    # Get the current events
    events = [e for e in sorted(secret.SCHEDULE) if e > local_now()]

    # Get the next event
    print("Processing events...")
    next_event = events[0]

    # Calculate the time until the event
    delta = next_event.datetime - local_now()
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    # Wait until a few hours before the start
    warning_window = datetime.timedelta(hours=secret.WARNING_WINDOW)
    print(f"Waiting {delta - warning_window} until next event warning")
    await asyncio.sleep((delta - warning_window).total_seconds())

    # Send the reminder to the control channel
    control_channel = bot.get_channel(secret.CONTROL_CHANNEL)
    control_role = utils.get(control_channel.guild.roles, id=secret.CONTROL_ROLE)
    embed = Embed(
            title="Notice: Upcoming event",
            description=next_event.message,
            colour=Colour.orange()
            )
    embed.add_field(name="Day", value=next_event.datetime.strftime("%A"))
    embed.add_field(name="Time", value=format_time(next_event.datetime.time()))
    embed.add_field(name="Time until event", value=f"{hours} hours {minutes} minutes")
    message = await control_channel.send(embed=embed)
    await control_channel.send(f"{control_role.mention} Event starting soon!")
    
    # Add the cancel emoji to the message
    await message.add_reaction("❌")

    # Wait until the event, or until it's cancelled
    print("Waiting for event")
    await asyncio.sleep((next_event.datetime - local_now()).total_seconds())

    # If the event hasn't been cancelled, send the message
    if message.channel:
        await send_message(None, message=next_event.message)
    else:
        print("Event cancelled, nothing to do")

    # Restart the event loop
    bot.loop.create_task(event_loop())

async def cancel_event(message):
    """
    Cancels an event and sends a message to the control channel.
    """
    print("Trying to cancel event")
    # Remove the original message
    await message.delete()

    # Send a message to the control channel
    control_channel = bot.get_channel(secret.CONTROL_CHANNEL)
    await control_channel.send("Event cancelled.")

@bot.command()
@commands.has_role(secret.CONTROL_ROLE)
async def list_events(ctx):
    """
    lists the scheduled events.
    """
    # Format the events as a string
    event_str = "\n".join([f"- {event[1]}" for event in secret.SCHEDULE])

    # Send the list of events to the channel
    await ctx.send(f"Scheduled events:\n{event_str}")

@bot.command()
@commands.has_role(secret.CONTROL_ROLE)
async def send_message(ctx, *, message: str):
    """
    Sends a message to the configured channel and role.
    """
    # Get the channel and role
    channel = bot.get_channel(secret.CHANNEL)
    role = utils.get(channel.guild.roles, id=secret.ROLE)

    # Send the message to the channel and role
    await channel.send(f"{role.mention} {message}")

# Simple ping command
@bot.command()
async def ping(ctx):
    await ctx.send("pong")

## Run the bot
if __name__ == "__main__":
    bot.run(secret.TOKEN)
