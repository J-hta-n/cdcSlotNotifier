from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import time
from src.lib.cdc.slot_checker import SlotChecker
from src.lib.telegram_notifier import TelegramNotifier
import config


class ScheduledSlotChecker:
    """Manages periodic slot checks and Telegram notifications."""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.checker = SlotChecker()
        self.notifier = TelegramNotifier()
        self.job = None
    
    def _check_and_notify(self):
        """
        Perform one slot check and send appropriate notification.
        This is the job function executed by APScheduler.
        """
        timestamp = datetime.now().strftime("%I:%M%p").lower()
        
        print(f"\n[{timestamp}] Checking for slots...")

        # Perform check
        slot_count, error, details = self.checker.check_slots()
        
        # Handle errors (session expired, network issues)
        if error:
            if "Session expired" in error:
                print(f"[{timestamp}] ✗ {error}")
                self.notifier.notify_session_expired()
                # Stop the scheduler since session is dead
                self.stop()
            else:
                print(f"[{timestamp}] ⚠ {error}")
                self.notifier.notify_error(error)
        else:
            # Session is valid, check slot count
            if slot_count > 0:
                # Slots found!
                print(f"[{timestamp}] ✓ {slot_count} slots found!")
                self.notifier.notify_slots_found(slot_count, details, config.COURSE_CODE)
            else:
                # No slots
                print(f"[{timestamp}] No slots found")
                self.notifier.notify_no_slots()
    
    def start(self):
        """Start checks immediately, then keep running at configured interval."""
        if self.job is not None:
            print("Scheduler already running.")
            return
        
        # Validate configuration
        if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
            print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env")
            return

        print("\n" + "="*60)
        print("CDC SLOT NOTIFIER - SCHEDULER STARTED")
        print("="*60)
        print("First check: immediate")
        print(f"Check interval: {config.CHECK_INTERVAL_MINUTES} minutes")
        print(f"Course: {config.COURSE_CODE}")
        print("="*60)

        # Run once immediately so user doesn't wait for first interval tick.
        self._check_and_notify()
        
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
