# CDC Slot Notifier

This program helps poll for available practical lesson slots at a specified frequency over a period of time, eg every 5 minutes for 3 hours, and will notify the user via Telegram whenever new slots are found

## Setup

1. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Configure your local `.env` file with reference to `.env.example`

## Usage

From the virtual environment, run

```bash
python src/main.py
```

Notes:

- First check happens instantly when started
- `No slots found` is deduplicated by notifier logic
- `slots found` notifications are sent immediately with date/session/time details
- `Session expired` is sent immediately and scheduler stops
- Runtime errors (for example 429 rate limit) are also sent to Telegram
- Raw CDC POST response is saved each check to `debug/last_post_response.txt` (or your configured dump file)
- Slot detection now parses the booking grid by date/day/session columns (`Images1.gif` = available)
- POST form payload is auto-constructed in code; only fresh hidden fields + course value are injected at runtime
