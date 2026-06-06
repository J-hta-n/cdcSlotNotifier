from datetime import datetime

from src.lib.cdc.model import format_course_label


def format_time() -> str:
    """Format current time as [HH:MMam/pm]."""
    return datetime.now().strftime("[%I:%M%p]").lower()


def format_slots_found_msg(slot_count: int, details: str = "", course_code: str = "") -> str:
    """Format message when slots are found."""
    course_label = format_course_label(course_code)
    if course_label:
        msg = f"{format_time()} {slot_count} {course_label} slots found!"
    else:
        msg = f"{format_time()} {slot_count} slots found!"
    if details:
        msg += f"\n{details}"
    return msg


def format_session_expired_msg() -> str:
    return f"{format_time()} Session expired, program halted. Please manually login and clear captcha to resume"


def format_polling_complete_msg() -> str:
    return f"{format_time()} Polling complete"


def format_error_msg(error_message: str) -> str:
    return f"{format_time()} Error: {error_message}"


def format_polling_started_msg(
    interval_minutes: int,
    period_hours: float,
    course_code: str,
    first_result: str,
) -> str:
    course_label = format_course_label(course_code)
    course_display = course_label.title() if course_label else (course_code or "Unknown")
    return (
        f"{format_time()} Polling started\n"
        f"Interval: {interval_minutes} minutes\n"
        f"Period: {period_hours} hours\n"
        f"Course: {course_display}\n\n"
        f"Initial poll:\n{first_result}"
    )