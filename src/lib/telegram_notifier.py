from telegram import Bot
from telegram.error import TelegramError
import asyncio
from datetime import datetime, timedelta
import config


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
                parse_mode=None
            )
            return True
        except TelegramError as e:
            print(f"Telegram error: {e}")
            return False
    
    def send_message_sync(self, message: str) -> bool:
        """Synchronous wrapper for async send_message."""
        return asyncio.run(self.send_message(message))
    
    def should_notify(self, notification_type: str) -> bool:
        """
        Determine if a notification should be sent based on deduplication logic.
        
        Args:
            notification_type: "no_slots", "slots_found", or "expired"
        
        Returns:
            True if notification should be sent, False if it's a duplicate
        """
        last_notif_time = self.last_notif_time
        last_notif_type = self.last_notif_type

        # Always send if this is the first notification
        if last_notif_time is None:
            return True
        
        # Send if notification type changed
        if last_notif_type != notification_type:
            return True
        
        # For "no_slots", we want to notify periodically (e.g., every 30 minutes)
        # to keep the user aware the bot is still running
        if notification_type == "no_slots":
            time_diff = datetime.now() - last_notif_time
            # Only re-send "no slots" after 30 minutes
            return time_diff > timedelta(minutes=30)
        
        # For "slots_found", always send (don't deduplicate - user needs to know immediately)
        if notification_type == "slots_found":
            return True
        
        # For "expired", always send immediately
        if notification_type == "expired":
            return True
        
        return False
    
    def notify_no_slots(self) -> bool:
        """Send 'no slots found' notification if dedup allows."""
        if not self.should_notify("no_slots"):
            return False
        
        message = config.format_no_slots_msg()
        success = self.send_message_sync(message)
        
        if success:
            self.last_notif_type = "no_slots"
            self.last_notif_time = datetime.now()
            print(f"✓ Notification sent: {message}")
        
        return success
    
    def notify_slots_found(self, slot_count: int, details: str = "", course_code: str = "") -> bool:
        """Send 'slots found' notification."""
        if not self.should_notify("slots_found"):
            return False
        
        message = config.format_slots_found_msg(slot_count, details, course_code)
        success = self.send_message_sync(message)
        
        if success:
            self.last_notif_type = "slots_found"
            self.last_notif_time = datetime.now()
            print(f"✓ Notification sent: {message}")
        
        return success
    
    def notify_session_expired(self) -> bool:
        """Send 'session expired' notification."""
        message = config.format_session_expired_msg()
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

        message = f"{config.format_time()} Error: {error_message}"
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
        message = config.format_polling_complete_msg()
        success = self.send_message_sync(message)
        if success:
            self.last_notif_type = "complete"
            self.last_notif_time = datetime.now()
            print(f"✓ Notification sent: {message}")
        return success
