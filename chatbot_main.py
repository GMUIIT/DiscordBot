import asyncio
import datetime
from collections import namedtuple
from discord import utils, Embed, Colour, Intents
from discord.ext import commands
import pytz


# Constants
Event = namedtuple("Event", ["day", "time", "message"])

# Configuration options
from secret import *

# Helper functions

def parse_day(day: str) -> int:
    """Parses a day of the week and returns its integer representation.
    """
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days.index(day)

def parse_time(time: str) -> datetime.time:
    """Parses a time string and returns a datetime.time object.
    """
    return datetime.datetime.strptime(time, "%H:%M").time()

def format_time(time: datetime.time) -> str:
    """Formats a datetime.time object as a string.
    """
    return time.strftime("%I:%M %p")

def to_local_time(dt: datetime.datetime) -> datetime.datetime:
    """Converts a datetime object to the bot's local time.
    """
    return dt.astimezone(datetime.timezone.utc).astimezone(pytz.timezone(TIMEZONE))

def schedule_events(events: list[Event]) -> list[tuple[datetime.datetime, str]]:
    """Schedules the events for the current week and returns a list of
    tuples containing the scheduled datetime and the event's message.
    """
    # Get the current local time
    now = to_local_time(datetime.datetime.utcnow())

    # Get the current week's schedule
    current_week = [(event, datetime.datetime.combine(now, parse_time(event.time)))
                    for event in events
                    if event.day == now.strftime("%A")]

    # Get the next week's schedule
    next_week = [(event, datetime.datetime.combine(now + datetime.timedelta(days=7), parse_time(event.time)))
                 for event in events
                 if event.day != now.strftime("%A")]

    # Sort the events by scheduled time
    events = sorted(current_week + next_week, key=lambda x: x[1])

    # Filter out events that have already passed
    events = [(dt, message) for (dt, message) in events if dt > now]

    return events

# Bot setup
# We need permissions for sending messages, adding reactions, and managing messages
intents = Intents.default()
bot = commands.Bot(command_prefix=CONTROL_PREFIX, intents=intents)

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
    if reaction.message.channel.id != CONTROL_CHANNEL:
        return

    # Check if the user has the control role
    if not utils.get(user.roles, name=CONTROL_ROLE):
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
    events = schedule_events(SCHEDULE)

    # Send a reminder for the next event
    if events:
        # Get the next event
        next_event = events[0]

        # Calculate the time until the event
        delta = next_event[0] - to_local_time(datetime.datetime.utcnow())
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        # Send the reminder to the control channel
        control_channel = bot.get_channel(CONTROL_CHANNEL)
        embed = Embed(
            title="Upcoming event",
            description=next_event[1],
            colour=Colour.orange()
        )
        embed.add_field(name="Time", value=format_time(next_event[0].time()))
        embed.add_field(name="Time until event", value=f"{hours} hours {minutes} minutes")
        message = await control_channel.send(embed=embed)

        # Add the cancel emoji to the message
        await message.add_reaction("❌")

    # Wait for the next event
    if events:
        await asyncio.sleep((events[0][0] - to_local_time(datetime.datetime.utcnow())).total_seconds())
    else:
        # If there are no events, wait for a day
        await asyncio.sleep(86400)

    # Restart the event loop
    bot.loop.create_task(event_loop())

async def cancel_event(message):
    """
    Cancels an event and sends a message to the control channel.
    """
    # Remove the original message
    await message.delete()

    # Send a message to the control channel
    control_channel = bot.get_channel(CONTROL_CHANNEL)
    await control_channel.send("Event cancelled.")

@bot.command()
@commands.has_role(CONTROL_ROLE)
async def list_events(ctx):
    """
    lists the scheduled events.
    """
    # Get the scheduled events
    events = schedule_events(SCHEDULE)

    # Format the events as a string
    event_str = "\n".join([f"- {format_time(event[0].time())}: {event[1]}" for event in events])

    # Send the list of events to the channel
    await ctx.send(f"Scheduled events:\n{event_str}")

@bot.command()
@commands.has_role(CONTROL_ROLE)
async def send_message(ctx, *, message: str):
    """
    Sends a message to the configured channel and role.
    """
    # Get the channel and role
    channel = bot.get_channel(CHANNEL)
    role = utils.get(ctx.guild.roles, name=ROLE)

    # Send the message to the channel and role
    await channel.send(f"{role.mention} {message}")

## Run the bot
if __name__ == "__main__":
    bot.run(TOKEN)
