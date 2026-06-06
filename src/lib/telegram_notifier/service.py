import asyncio
from datetime import datetime

from telegram import Bot
from telegram.error import TelegramError

import config
from src.lib.telegram_notifier.utils import (
    format_error_msg,
    format_polling_complete_msg,
    format_polling_started_msg,
    format_session_expired_msg,
    format_slots_found_msg,
)


class TelegramNotifier:
    """Handles Telegram notifications with deduplication logic."""

    def __init__(self):
        self.bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.last_notif_time = None
        self.last_notif_type = None
        self.last_error_message = None
        self.last_error_time = None

    async def send_message(self, message: str) -> bool:
        """Send a message via Telegram. Returns True if successful."""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=None,
            )
            return True
        except TelegramError as e:
            print(f"Telegram error: {e}")
            return False

    def send_message_sync(self, message: str) -> bool:
        """Synchronous wrapper for async send_message."""
        return asyncio.run(self.send_message(message))

    def notify_slots_found(self, slot_count: int, details: str = "", course_code: str = "") -> bool:
        """Send 'slots found' notification."""
        message = format_slots_found_msg(slot_count, details, course_code)
        success = self.send_message_sync(message)

        if success:
            self.last_notif_type = "slots_found"
            self.last_notif_time = datetime.now()
            print(f"✓ Notification sent: {message}")

        return success

    def notify_session_expired(self) -> bool:
        """Send 'session expired' notification."""
        message = format_session_expired_msg()
        success = self.send_message_sync(message)

        if success:
            self.last_notif_type = "expired"
            self.last_notif_time = datetime.now()
            print(f"✓ Notification sent: {message}")

        return success

    def notify_error(self, error_message: str) -> bool:
        """Send non-session runtime errors (e.g. 429) with dedupe for repeats."""
        now = datetime.now()
        if (
            self.last_error_message == error_message
            and self.last_error_time is not None
            and now - self.last_error_time <= timedelta(minutes=15)
        ):
            return False

        message = format_error_msg(error_message)
        success = self.send_message_sync(message)
        if success:
            self.last_error_message = error_message
            self.last_error_time = now
            self.last_notif_type = "error"
            self.last_notif_time = now
            print(f"✓ Notification sent: {message}")
        return success

    def notify_polling_complete(self) -> bool:
        """Send one final notification when polling window ends."""
        message = format_polling_complete_msg()
        success = self.send_message_sync(message)
        if success:
            self.last_notif_type = "complete"
            self.last_notif_time = datetime.now()
            print(f"✓ Notification sent: {message}")
        return success

    def notify_polling_started(
        self,
        interval_minutes: int,
        period_hours: float,
        course_code: str,
        first_result: str,
    ) -> bool:
        """Send one startup summary notification with first poll outcome."""
        message = format_polling_started_msg(
            interval_minutes=interval_minutes,
            period_hours=period_hours,
            course_code=course_code,
            first_result=first_result,
        )
        success = self.send_message_sync(message)
        if success:
            self.last_notif_type = "started"
            self.last_notif_time = datetime.now()
            print(f"✓ Notification sent: {message}")
        return success
