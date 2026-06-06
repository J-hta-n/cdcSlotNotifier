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
CHECK_PERIOD_HOURS = float(os.getenv("CHECK_PERIOD_HOURS", "1"))
CDC_USER_AGENT = os.getenv(
    "CDC_USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
)

# Direct request replay inputs
COOKIES = os.getenv("COOKIES", "").strip()
POST_RESPONSE_DUMP_FILE = os.getenv("POST_RESPONSE_DUMP_FILE", "debug/last_post_response.txt").strip()

# CDC Endpoint
CDC_BOOKING_URL = "https://bookingportal.cdc.com.sg/NewPortal/Booking/BookingPL.aspx"

# Messages
def format_time():
    """Format current time as [HH:MMam/pm]"""
    return datetime.now().strftime("[%I:%M%p]").lower()


def format_course_label(course_code: str) -> str:
    code = (course_code or "").strip().upper()
    known = {
        "INDUCTION-PROGRAMME": "induction programme",
        "EV-ELITETEAM": "practical",
    }
    if code in known:
        return known[code]
    if not code:
        return ""
    return code.replace("-", " ").lower()

def format_no_slots_msg():
    return f"{format_time()} No slots found"

def format_slots_found_msg(slot_count: int, details: str = "", course_code: str = ""):
    """Format message when slots are found"""
    course_label = format_course_label(course_code)
    if course_label:
        msg = f"{format_time()} {slot_count} {course_label} slots found!"
    else:
        msg = f"{format_time()} {slot_count} slots found!"
    if details:
        msg += f"\n{details}"
    return msg

def format_session_expired_msg():
    return f"{format_time()} Session expired, program halted. Please manually login and clear captcha to resume"


def format_polling_complete_msg():
    return f"{format_time()} Polling complete"
