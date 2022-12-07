import asyncio
import datetime
from collections import namedtuple
from discord import utils, Embed, Colour, Intents
from discord.ext import commands
import pytz
import calendar
from functools import total_ordering

# Constants
@total_ordering
class Event:
    """
    Represents an event.
    """
    def __init__(self, day: str, time: str, message: str):
        self.day = parse_day(day)
        self.time = parse_time(time)
        self.message = message

    @property
    def datetime(self):
        """
        Returns a datetime object representing the event.
        """
        now = datetime.datetime.now()
        # calc day offset
        day_offset = self.day - now.weekday()
        if day_offset < 0:
            day_offset += 7
        now = now.replace(hour=self.time.hour, minute=self.time.minute, second=0, microsecond=0)
        return to_local_time(now + datetime.timedelta(days=day_offset))

    def __repr__(self):
        return f"Event(day={self.day}, time={self.time}, message={self.message})"

    def __str__(self):
        # day
        day_str = calendar.day_name[self.day]
        return f"{day_str} at {format_time(self.time)}: {self.message}"

    def __eq__(self, other):
        if isinstance(other, Event):
            return self.datetime == other.datetime
        if isinstance(other, datetime.datetime):
            return self.datetime == other
        return NotImplemented
    
    def __gt__(self, other):
        if isinstance(other, Event):
            return self.datetime > other.datetime
        if isinstance(other, datetime.datetime):
            return self.datetime > other
        return NotImplemented

# Helper functions

def parse_day(day: str) -> int:
    """
    Parses a day of the week and returns its integer representation.
    """
    return list(calendar.day_name).index(day)

def parse_time(time: str) -> datetime.time:
    """
    Parses a time string and returns a datetime.time object.
    """
    return datetime.datetime.strptime(time, "%H:%M").time()

def format_time(time: datetime.time) -> str:
    """
    Formats a datetime.time object as a string.
    """
    return time.strftime("%I:%M %p")

def to_local_time(dt: datetime.datetime) -> datetime.datetime:
    """
    Converts a datetime object to the bot's local time.
    """
    return dt.astimezone(datetime.timezone.utc).astimezone(pytz.timezone(secret.TIMEZONE))

def local_now() -> datetime.datetime:
    """
    Returns the current local time.
    """
    return to_local_time(datetime.datetime.now())

import secret
