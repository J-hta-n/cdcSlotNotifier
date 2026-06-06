#!/usr/bin/env python3
"""
CDC Slot Notifier - Main entry point

Usage:
    python main.py start          - Start scheduler (runs first check immediately)
    python main.py                - Same as 'start'
"""

import sys
from pathlib import Path


# Allow running as `python src/main.py` by making project root importable.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
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
if __name__ == "__main__":
    main()
