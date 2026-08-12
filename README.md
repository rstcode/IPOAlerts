# IPO Alerts

A Python project that fetches Indian IPO GMP data, filters high-potential IPOs, and sends Telegram alerts with the latest GMP movement and IPO details.

## What it does
- Fetches IPO GMP data from the live source
- Filters IPOs above a configurable GMP threshold
- Categorizes IPOs into:
  - closing today
  - open now
  - upcoming in the next 7 days
- Sends a formatted Telegram message
- Saves previous alert values in sent_alerts.json for comparison

## Setup

### Prerequisites
- Python 3.8+
- Telegram bot token and chat ID

### Install dependencies
```bash
py -m pip install -r requirements.txt
```

### Environment variables
```bash
# Windows (PowerShell)
$env:TELEGRAM_BOT_TOKEN = "your-bot-token"
$env:TELEGRAM_CHAT_ID = "your-chat-id"

# Optional
$env:IS_DEBUG = "true"
$env:IS_MOCK = "true"
```

### Run
```bash
python main.py
```

## Project files
- main.py: fetches data, filters IPOs, and sends alerts
- telegram_alert.py: formats and sends the Telegram message
- sent_alerts.json: stores prior alert GMP values for comparison
- tests/: basic regression tests

## Notes
- The Telegram message includes the IPO name, dates, GMP, change from the last saved value, and a link when available.
- Mock mode can be enabled for testing with sample data.
