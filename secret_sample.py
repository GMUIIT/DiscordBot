# DO NOT PUBLISH
import helper

# Configuration options
TOKEN = "YOUR_TOKEN"
# Use "Copy ID" to get the IDs for roles and channels.
ROLE = 0
CHANNEL = 0
SCHEDULE = [
    # Day, time, message
    helper.Event("Monday", "12:00", "Reminder: Weekly meeting today at 4:00 PM in the Mix.  See you there!"),
    helper.Event("Thursday", "13:00", "Reminder: Weekly meeting today at 5:00 PM in the Mix.  See you there!"),
]
TIMEZONE = "America/New_York"
CONTROL_CHANNEL = 0
CONTROL_ROLE = 0
CONTROL_PREFIX = "!"
# How long before the event to send the warning notification, in hours.
WARNING_WINDOW = 10
