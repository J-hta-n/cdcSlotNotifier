# CDC Slot Notifier (Simple Mode)

This project now runs with a minimal flow:

- Put `COOKIES` (and optional `COURSE_CODE`) in `.env`
- Run `python main.py`
- First check runs immediately (no 9am/1-hour window logic)
- Then it keeps checking every `CHECK_INTERVAL_MINUTES`

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create `.env` and set these values:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Optional, defaults to EV-ELITETEAM
COURSE_CODE=EV-ELITETEAM

# Runs every N minutes (first check is immediate)
CHECK_INTERVAL_MINUTES=5

# Full Cookie header string copied from booking request
COOKIES=ASP.NET_SessionId=...; ILOAFLLQ=...; cf_clearance=...; __cf_bm=...

# Optional: where each raw POST response is dumped for debugging
POST_RESPONSE_DUMP_FILE=debug/last_post_response.txt
```

## Run

```bash
python main.py
```

or

```bash
python main.py start
```

Behavior:

- First check happens instantly when started
- `No slots found` is deduplicated by notifier logic
- `slots found` notifications are sent immediately with date/session/time details
- `Session expired` is sent immediately and scheduler stops
- Runtime errors (for example 429 rate limit) are also sent to Telegram
- Raw CDC POST response is saved each check to `debug/last_post_response.txt` (or your configured dump file)
- Slot detection now parses the booking grid by date/day/session columns (`Images1.gif` = available)
- POST form payload is auto-constructed in code; only fresh hidden fields + course value are injected at runtime

## Notes

- `python main.py login` is intentionally deprecated in this simplified mode.
- Legacy login/session capture modules were removed in this simplified mode.
- If you get 429/session expired, refresh `COOKIES` from a fresh browser request.
