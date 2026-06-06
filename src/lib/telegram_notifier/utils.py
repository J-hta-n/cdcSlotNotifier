from datetime import datetime

from src.lib.cdc.model import format_course_label


def format_time() -> str:
    """Format current time as [HH:MMam/pm]."""
    return datetime.now().strftime("[%I:%M%p]").lower()


def format_no_slots_msg(course_code: str = "") -> str:
    course_label = format_course_label(course_code)
    if course_label:
        return f"{format_time()} No {course_label} slots found"
    return f"{format_time()} No slots found"


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