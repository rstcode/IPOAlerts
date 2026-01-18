import os
import json
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from telegram_alert import send_telegram_message, format_telegram_message

load_dotenv()

GMP_API_URL = "https://webnodejs.investorgain.com/cloud/ipodashboard/gmpList-read/IPO"

GMP_THRESHOLD = 20.0

ALERT_HISTORY_FILE = "sent_alerts.json"
IS_DEBUG = os.getenv("IS_DEBUG", "false").lower() in ("1", "true", "yes")
IS_MOCK = os.getenv("IS_MOCK", "false").lower() in ("1", "true", "yes")


# ------------------ Helpers ------------------

def is_weekday_ist() -> bool:
    return datetime.now(timezone.utc).weekday() < 5


def parse_date(date_str):
    return datetime.fromisoformat(date_str[:10]).date()


def load_alert_history():
    if not os.path.exists(ALERT_HISTORY_FILE):
        return {}
    with open(ALERT_HISTORY_FILE, "r") as f:
        return json.load(f)


def save_alert_history(history):
    with open(ALERT_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def fetch_gmp_data():

    if IS_MOCK:
        mock_path = os.path.join(os.path.dirname(__file__), "mockdata.json")
        if not os.path.exists(mock_path):
            print("[ERROR] IS_MOCK is true but mockdata.json not found")
            return []
        try:
            with open(mock_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data.get("ipoList", [])
                if isinstance(data, list):
                    return data
        except Exception as e:
            print(f"[ERROR] Failed to read mockdata.json: {e}")
            return []
    try:
        response = requests.get(GMP_API_URL, timeout=15)
        response.raise_for_status()
        return response.json().get("ipoList", [])
    except Exception as e:
        print(f"[ERROR] Failed to fetch GMP data: {e}")
        return []


def is_valid_ipo(ipo):
    return ipo.get("ipo_status") in ["Upcoming", "Open"]


def gmp_above_threshold(ipo):
    try:
        return float(ipo.get("gmp_percent_calc", 0)) >= GMP_THRESHOLD
    except ValueError:
        return False


# ------------------ Momentum + Dedup ------------------

def should_alert(ipo):
    today = datetime.now(timezone.utc).date()
    status = ipo.get("ipo_status")

    open_date = datetime.fromisoformat(ipo["issue_open_dt"][:10]).date()

    # IPO is already open
    if status == "Open":
        return True

    # IPO is upcoming within next 7 days
    if status == "Upcoming" and open_date <= today + timedelta(days=7):
        return True

    return False



# ------------------ Categorisation ------------------

def categorise_ipos(ipos):
    today = datetime.now(timezone.utc).date()
    next_7_days = today + timedelta(days=7)

    categories = {
        "last_day": [],
        "open_now": [],
        "upcoming": []
    }

    for ipo in ipos:
        open_date = parse_date(ipo["issue_open_dt"])
        close_date = parse_date(ipo["issue_end_dt"])
        status = ipo["ipo_status"]

        if status == "Open":
            if close_date == today:
                categories["last_day"].append(ipo)
            elif close_date > today:
                categories["open_now"].append(ipo)

        elif status == "Upcoming" and open_date <= next_7_days:
            categories["upcoming"].append(ipo)

    return categories


def sort_by_priority(ipos, history):
    def score(ipo):
        gmp = float(ipo.get("gmp_percent_calc", 0))
        trending_bonus = 0.0
        return trending_bonus + gmp

    return sorted(ipos, key=score, reverse=True)


# ------------------ MAIN ------------------

def main():
    print("[INFO] High GMP IPO Alert started")

    if not is_weekday_ist() and not IS_DEBUG:
        print("[INFO] Weekend. Exiting.")
        return

    ipo_list = fetch_gmp_data()
    history = load_alert_history()

    eligible = []

    for ipo in ipo_list:
        if not is_valid_ipo(ipo):
            continue
        if not gmp_above_threshold(ipo):
            continue
        if not should_alert(ipo):
            continue
        eligible.append(ipo)

    if not eligible:
        print("[INFO] No qualifying IPOs today.")
        return

    categories = categorise_ipos(eligible)

    for key in categories:
        categories[key] = sort_by_priority(categories[key], history)

    message = format_telegram_message(categories, history)

    if send_telegram_message(message):
        today = datetime.now(timezone.utc).date().isoformat()
        for ipo in eligible:
            history[ipo["company_short_name"]] = {
                "last_alert_date": today,
                "last_gmp_percent": float(ipo.get("gmp_percent_calc", 0))
            }
        save_alert_history(history)
        print("✅ Telegram alert sent")
    else:
        print("❌ Telegram send failed")


if __name__ == "__main__":
    main()
