import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# CDC Configuration
COURSE_CODE = os.getenv("COURSE_CODE", "EV-ELITETEAM")
WINDOW_START_HOUR = int(os.getenv("WINDOW_START_HOUR", "9"))
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "5"))

# Session Storage
SESSION_STATE_FILE = os.getenv("SESSION_STATE_FILE", "session_state.json")

# CDC Endpoint
CDC_BOOKING_URL = "https://bookingportal.cdc.com.sg/NewPortal/Booking/BookingPL.aspx"
CDC_LOGIN_URL = "https://bookingportal.cdc.com.sg/"

# Messages
def format_time():
    """Format current time as [HH:MMam/pm]"""
    return datetime.now().strftime("[%I:%M%p]").lower()

def format_no_slots_msg():
    return f"{format_time()} No slots found"

def format_slots_found_msg(slot_count: int, details: str = ""):
    """Format message when slots are found"""
    msg = f"{format_time()} {slot_count} slots found!"
    if details:
        msg += f"\n{details}"
    return msg

def format_session_expired_msg():
    return f"{format_time()} Session expired, program halted. Please manually login and clear captcha to resume"
