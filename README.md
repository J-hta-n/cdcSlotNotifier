# CDC Slot Notifier

A lightweight Python bot that automatically checks for available driving lesson slots on the ComfortDelGro Driving Centre (CDC) Singapore booking portal and sends Telegram notifications when slots become available.

## Features

- **Manual login with CAPTCHA:** You control the authentication; no CAPTCHA bypass automation
- **Session reuse:** Login once, then the bot checks slots automatically via HTTP POST requests (fast, lightweight)
- **Scheduled checks:** Configurable time windows and check intervals (default: every 5 minutes within a 1-hour window)
- **Telegram notifications:** Three types of alerts:
  - `[12:05pm] No slots found` — periodic updates to confirm bot is running
  - `[12:05pm] 3 slots found! <details>` — immediate alert when slots appear
  - `[12:05pm] Session expired, program halted...` — when session needs re-authentication
- **Lightweight and resilient:** Uses direct HTTP requests instead of browser automation for checks; retries on network failures

## Prerequisites

- Python 3.9+
- pip (Python package manager)
- A Telegram bot token (from BotFather)
- Your Telegram chat ID
- CDC Singapore online account (with valid credentials for manual login)

## Setup

### 1. Clone or navigate to the project directory

```bash
cd /Users/jh/Documents/PROJECTS/cdcSlotNotifier
```

### 2. Create a Python virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create `.env` file from template

```bash
cp .env.example .env
```

### 5. Edit `.env` with your configuration

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Optional: customize if not using EV-ELITETEAM or different timing
COURSE_CODE=EV-ELITETEAM
WINDOW_START_HOUR=9
CHECK_INTERVAL_MINUTES=5
SESSION_STATE_FILE=session_state.json
```

#### Getting Telegram credentials:

1. Create a bot with [@BotFather](https://t.me/botfather) on Telegram
2. Copy the bot token and paste into `TELEGRAM_BOT_TOKEN`
3. Send a message to your bot, then:
   ```bash
   curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates"
   ```
4. Find your `chat_id` in the response and add to `TELEGRAM_CHAT_ID`

## Usage

### Step 1: Login with CAPTCHA (one-time)

Open a browser window, log in manually to CDC, and solve the CAPTCHA:

```bash
python main.py login
```

This will:

1. Open a visible Playwright browser
2. Prompt you to log in with your CDC credentials and complete CAPTCHA
3. Capture your session cookies and authentication state
4. Save everything to `session_state.json` for reuse

**Keep the browser open until the login is complete, then press Enter in the terminal.**

### Step 2: Start the scheduler

Once logged in, start the automated slot checker:

```bash
python main.py start
```

This will:

1. Validate your saved session
2. Check for available slots every 5 minutes (configurable)
3. Only run checks during your configured time window (e.g., 9am–10am)
4. Send Telegram notifications when:
   - Slots are found
   - No slots are found (periodic reminder every 30 minutes)
   - Session expires (requires manual re-login)

Press `Ctrl+C` to stop the scheduler.

## Configuration

Edit `.env` to customize:

- **`WINDOW_START_HOUR`:** The hour when checks should begin (0–23, 24-hour format)
  - Example: `WINDOW_START_HOUR=9` → checks run from 9am–10am
- **`CHECK_INTERVAL_MINUTES`:** How often to check for slots
  - Default: `5` (every 5 minutes)
- **`COURSE_CODE`:** The driving lesson type to monitor
  - Default: `EV-ELITETEAM` (Elite Team EV Class)
  - Other options: `INDUCTION-PROGRAMME`, etc.

## Session Management

Your authenticated session is stored in `session_state.json`. It includes:

- Browser cookies (ASP.NET session ID, CloudFlare token, etc.)
- ASP.NET view state and validation fields (needed for POST requests)
- Metadata (last check time, last notification)

**Do not commit `session_state.json` to version control; it contains sensitive data.**

### Re-authenticating

If the session expires (you get the "Session expired" Telegram message), simply run:

```bash
python main.py login
```

This will open the browser again and overwrite the saved session.

## How It Works

### Architecture

1. **Login Phase:**
   - Playwright opens a visible browser
   - You manually log in and solve CAPTCHA
   - Bot captures HTTP cookies and ASP.NET form state
   - Everything saved to `session_state.json`

2. **Check Phase:**
   - APScheduler triggers a check every 5 minutes (within your time window)
   - SlotChecker loads cookies + form state from storage
   - Makes a direct HTTP POST request to CDC booking endpoint
   - Parses the ASP.NET AJAX response for "No available slots" text
   - Updates form state from response (for next request)

3. **Notification Phase:**
   - TelegramNotifier evaluates whether to send a message
   - Deduplicates "no slots" alerts (max once per 30 minutes)
   - Always sends "slots found" alerts immediately
   - Reports session expiry and halts the scheduler

### Why This Approach?

- **Manual login:** Avoids CAPTCHA bypass (no illegal automation)
- **HTTP POST, not browser automation:** Much faster (no Playwright overhead per check)
- **Session reuse:** One login, then hundreds of lightweight checks
- **Deduplication:** Reduces notification spam while keeping you informed
- **Resilient:** Retries on network failures; detects session expiry early

## Troubleshooting

### "Session not valid. Please run /login first."

You haven't completed the initial login yet, or `session_state.json` is missing.

```bash
python main.py login
```

### "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env"

Your `.env` file is missing or incomplete. Check that both values are present and valid.

### "Session expired, program halted..."

Your CDC session has timed out. Re-run:

```bash
python main.py login
```

### Slots are found but no notification arrives

1. Verify your Telegram token and chat ID are correct
2. Check that your Telegram bot has permission to message you
3. Test the bot manually: `curl -X POST https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<CHAT_ID>&text=test`

### Checker keeps reporting "No available slots" even though slots exist

The response parsing may need adjustment if CDC changed their HTML structure. Run a manual check and inspect `session_state.json` to debug.

## Limitations & Roadmap

**Current scope (V1):**

- ✅ Single time window per day
- ✅ Fixed 5-minute interval
- ✅ Read-only checks (no booking)
- ✅ Manual login with CAPTCHA

**Future enhancements (backlog):**

- [ ] Multiple disjoint time windows (e.g., 9am–12pm AND 9pm–12am)
- [ ] Ad-hoc `/check` command to check outside windows
- [ ] Support multiple course types in a single run
- [ ] Configurable notification frequency
- [ ] Persistent logging with date/time of checks and slots

## Security & Privacy

- **No credential storage:** Username and password are never saved; only session cookies
- **CAPTCHA not bypassed:** You solve it yourself during login
- **`.gitignore` ready:** `session_state.json` is excluded from version control
- **No external services:** All data stays on your machine except Telegram notifications

## License

This project is for personal use only. Do not use for commercial purposes or to resell slot access.

## Support

If you encounter issues:

1. Check that your `.env` file is properly configured
2. Verify you've completed `python main.py login` at least once
3. Ensure your Telegram bot token and chat ID are correct
4. Check your network connection and firewall settings

---

Happy slot hunting! 🚗
