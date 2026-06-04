# CDC Slot Notifier (Simple Mode)

This project now runs with a minimal flow:

- Put `COOKIE` and `POST_PAYLOAD` in `.env`
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
COOKIE=ASP.NET_SessionId=...; ILOAFLLQ=...; cf_clearance=...; __cf_bm=...

# Full URL-encoded POST form payload copied from booking POST request
POST_PAYLOAD=ctl00%24ContentPlaceHolder1%24ScriptManager1=...&__VIEWSTATE=...&__EVENTVALIDATION=...&...
```

Required payload keys include:

- `ctl00$ContentPlaceHolder1$ScriptManager1`
- `__EVENTTARGET`
- `__VIEWSTATE`
- `__VIEWSTATEGENERATOR`
- `__PREVIOUSPAGE`
- `__EVENTVALIDATION`
- `ctl00$ContentPlaceHolder1$ddlCourse`

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
- `slots found` notifications are sent immediately
- `Session expired` is sent immediately and scheduler stops

## Notes

- `python main.py login` is intentionally deprecated in this simplified mode.
- Legacy login/session capture modules were removed in this simplified mode.
- If you get 429/session expired, refresh both `COOKIE` and `POST_PAYLOAD` from a fresh browser request.
