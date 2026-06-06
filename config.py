import os
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
