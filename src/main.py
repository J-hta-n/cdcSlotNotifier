#!/usr/bin/env python3
"""
CDC Slot Notifier - Main entry point

Usage:
    python main.py start          - Start scheduler (runs first check immediately)
    python main.py                - Same as 'start'
"""

import sys


def main():
    if len(sys.argv) < 2:
        command = "start"
        print("\nNo command provided. Defaulting to 'start'.")
    else:
        command = sys.argv[1].lower()

    if command == "start":
        print("\nStarting scheduler...")
        from src.lib.scheduler import ScheduledSlotChecker

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
