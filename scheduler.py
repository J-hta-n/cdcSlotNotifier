from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import time
from slot_checker import SlotChecker
from telegram_notifier import TelegramNotifier
from session_storage import SessionStorage
import config


class ScheduledSlotChecker:
    """Manages scheduled slot checks within a configured time window."""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.checker = SlotChecker()
        self.notifier = TelegramNotifier()
        self.storage = SessionStorage()
        self.job = None
    
    def _is_within_window(self) -> bool:
        """Check if current time is within the configured 1-hour window."""
        current_hour = datetime.now().hour
        window_start = config.WINDOW_START_HOUR
        window_end = (window_start + 1) % 24  # 1-hour window
        
        # Handle case where window spans midnight
        if window_start < window_end:
            return window_start <= current_hour < window_end
        else:
            return current_hour >= window_start or current_hour < window_end
    
    def _check_and_notify(self):
        """
        Perform one slot check and send appropriate notification.
        This is the job function executed by APScheduler.
        """
        timestamp = datetime.now().strftime("%I:%M%p").lower()
        
        print(f"\n[{timestamp}] Checking for slots...")
        
        # Check if we're still in the window
        if not self._is_within_window():
            print(f"[{timestamp}] Outside of checking window. Skipping.")
            return
        
        # Perform check
        slot_count, error = self.checker.check_slots()
        self.storage.set_last_check_time()
        
        # Handle errors (session expired, network issues)
        if error:
            if "Session expired" in error:
                print(f"[{timestamp}] ✗ {error}")
                self.notifier.notify_session_expired()
                # Stop the scheduler since session is dead
                self.stop()
            else:
                print(f"[{timestamp}] ⚠ {error}")
        else:
            # Session is valid, check slot count
            if slot_count > 0:
                # Slots found!
                print(f"[{timestamp}] ✓ {slot_count} slots found!")
                self.notifier.notify_slots_found(slot_count)
            else:
                # No slots
                print(f"[{timestamp}] No slots found")
                self.notifier.notify_no_slots()
    
    def start(self):
        """Start the scheduler with the configured interval and time window."""
        if self.job is not None:
            print("Scheduler already running.")
            return
        
        # Validate configuration
        if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
            print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env")
            return
        
        # Validate session
        if not self.storage.is_session_valid():
            print("Error: No valid session found. Please run 'python main.py login' first.")
            return
        
        print("\n" + "="*60)
        print("CDC SLOT NOTIFIER - SCHEDULER STARTED")
        print("="*60)
        print(f"Window start hour: {config.WINDOW_START_HOUR}:00")
        print(f"Check interval: {config.CHECK_INTERVAL_MINUTES} minutes")
        print(f"Course: {config.COURSE_CODE}")
        print("="*60)
        
        # Schedule the job to run at the specified interval
        self.job = self.scheduler.add_job(
            self._check_and_notify,
            trigger=IntervalTrigger(minutes=config.CHECK_INTERVAL_MINUTES),
            id="slot_check_job",
            name="Slot Availability Check"
        )
        
        self.scheduler.start()
        
        print("\n✓ Scheduler started. Press Ctrl+C to stop.\n")
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("\n✓ Scheduler stopped.")
