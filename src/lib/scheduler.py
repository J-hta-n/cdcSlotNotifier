from datetime import datetime, timedelta
import time
from src.lib.cdc.model import format_course_label
from src.lib.cdc.slot_checker import SlotChecker
from src.lib.telegram_notifier import TelegramNotifier
import config


class ScheduledSlotChecker:
    """Manages periodic slot checks and Telegram notifications."""
    
    def __init__(self):
        self.checker = SlotChecker()
        self.notifier = TelegramNotifier()
        self.running = False
        self.stop_reason = None
        self.last_slots_signature = None

    def _perform_check(self):
        """Run one slot-check request and return timestamp + result tuple."""
        timestamp = datetime.now().strftime("%I:%M%p").lower()
        print(f"\n[{timestamp}] Checking for slots...")
        slot_count, error, details = self.checker.check_slots()
        return timestamp, slot_count, error, details

    @staticmethod
    def _format_first_result(slot_count: int, error: str, details: str) -> str:
        if error:
            return f"Polling stopped due to error: {error}"

        if slot_count > 0:
            course_label = format_course_label(config.COURSE_CODE)
            if course_label:
                summary = f"{slot_count} {course_label} slots found"
            else:
                summary = f"{slot_count} slots found"
            if details:
                return f"{summary}\n{details}"
            return summary

        course_label = format_course_label(config.COURSE_CODE)
        if course_label:
            return f"No {course_label} slots found, will update only when new slots are found"
        return "No slots found, will update only when new slots are found"
    
    def _check_and_notify(self):
        """
        Perform one slot check and send notification only on slots found or stop conditions.
        """
        timestamp, slot_count, error, details = self._perform_check()
        
        # Handle errors (session expired, network issues)
        if error:
            print(f"[{timestamp}] ✗ {error}")

            if "Session expired" in error:
                self.notifier.notify_session_expired()
            else:
                self.notifier.notify_error(f"{error}. Polling stopped.")

            self.stop(reason="error")
        else:
            if slot_count > 0:
                current_signature = f"{slot_count}|{details}"
                if current_signature != self.last_slots_signature:
                    print(f"[{timestamp}] ✓ {slot_count} slots found!")
                    self.notifier.notify_slots_found(slot_count, details, config.COURSE_CODE)
                    self.last_slots_signature = current_signature
                else:
                    print(f"[{timestamp}] Slots still available (unchanged), no alert sent")
            else:
                course_label = format_course_label(config.COURSE_CODE)
                if course_label:
                    print(f"[{timestamp}] No {course_label} slots found")
                else:
                    print(f"[{timestamp}] No slots found")
                self.last_slots_signature = None
    
    def start(self):
        """Run checks every interval for a fixed period, then stop."""
        if self.running:
            print("Scheduler already running.")
            return
        
        # Validate configuration
        if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
            print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env")
            return

        print("\n" + "="*60)
        print("CDC SLOT NOTIFIER - SCHEDULER STARTED")
        print("="*60)
        print(f"Check interval: {config.CHECK_INTERVAL_MINUTES} minutes")
        print(f"Check period: {config.CHECK_PERIOD_HOURS} hours")
        print(f"Course: {config.COURSE_CODE}")
        print("="*60)

        self.running = True
        self.stop_reason = None

        interval_seconds = max(1, int(config.CHECK_INTERVAL_MINUTES * 60))
        period_seconds = max(1, int(config.CHECK_PERIOD_HOURS * 3600))
        end_time = datetime.now() + timedelta(seconds=period_seconds)

        print("\n✓ Polling started. Press Ctrl+C to stop early.\n")

        try:
            timestamp, slot_count, error, details = self._perform_check()

            first_result = self._format_first_result(slot_count, error, details)
            self.notifier.notify_polling_started(
                interval_minutes=config.CHECK_INTERVAL_MINUTES,
                period_hours=config.CHECK_PERIOD_HOURS,
                course_code=config.COURSE_CODE,
                first_result=first_result,
            )

            if error:
                print(f"[{timestamp}] ✗ {error}")
                self.stop(reason="error")
                return

            if slot_count > 0:
                self.last_slots_signature = f"{slot_count}|{details}"

            while self.running and datetime.now() < end_time:
                remaining_seconds = int((end_time - datetime.now()).total_seconds())
                if remaining_seconds <= 0:
                    break

                time.sleep(min(interval_seconds, remaining_seconds))

                self._check_and_notify()
                if not self.running:
                    break

            if self.running:
                self.notifier.notify_polling_complete()
                self.stop(reason="complete")
        except KeyboardInterrupt:
            self.stop(reason="manual")
    
    def stop(self, reason: str = "manual"):
        """Stop the polling loop."""
        if not self.running and self.stop_reason is not None:
            return

        self.running = False
        self.stop_reason = reason
        print("\n✓ Scheduler stopped.")
