import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# CDC Configuration
COURSE_CODE = os.getenv("COURSE_CODE", "EV-ELITETEAM")
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "5"))
CDC_USER_AGENT = os.getenv(
    "CDC_USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
)

# Direct request replay inputs
COOKIES = os.getenv("COOKIES", "").strip()
POST_PAYLOAD = os.getenv("POST_PAYLOAD", "").strip()
POST_RESPONSE_DUMP_FILE = os.getenv("POST_RESPONSE_DUMP_FILE", "debug/last_post_response.txt").strip()

REQUIRED_POST_PAYLOAD_KEYS = [
    "ctl00$ContentPlaceHolder1$ScriptManager1",
    "__EVENTTARGET",
    "__VIEWSTATE",
    "__VIEWSTATEGENERATOR",
    "__PREVIOUSPAGE",
    "__EVENTVALIDATION",
    "ctl00$ContentPlaceHolder1$ddlCourse",
]

# CDC Endpoint
CDC_BOOKING_URL = "https://bookingportal.cdc.com.sg/NewPortal/Booking/BookingPL.aspx"

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
