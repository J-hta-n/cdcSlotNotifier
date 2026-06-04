#!/usr/bin/env python3
"""
CDC Slot Notifier - Main entry point

Usage:
    python main.py login          - Perform manual login with CAPTCHA
    python main.py start          - Start the scheduler for slot checks
"""

import sys
import os


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "login":
        print("\nStarting login flow...")
        from browser_login import sync_login_and_capture_session
        try:
            sync_login_and_capture_session(headless=False)
        except Exception as e:
            print(f"\nError during login: {e}")
            sys.exit(1)
    
    elif command == "start":
        print("\nStarting scheduler...")
        from scheduler import ScheduledSlotChecker
        try:
            scheduler = ScheduledSlotChecker()
            scheduler.start()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"\nError during scheduler: {e}")
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
