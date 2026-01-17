import os
import json
import requests
from datetime import datetime, timedelta
from emaillib import send_ipo_email
from telegram_alert import send_telegram_message, format_telegram_message
from dotenv import load_dotenv


load_dotenv()

GMP_API_URL = "https://webnodejs.investorgain.com/cloud/ipodashboard/gmpList-read/IPO"

GMP_THRESHOLD = 10.0
ALERT_HISTORY_FILE = "sent_alerts.json"
IS_DEBUG = os.getenv("IS_DEBUG", "false").lower() in ("1", "true", "yes")


def is_weekday_ist() -> bool:
    return datetime.utcnow().weekday() < 5


def load_alert_history():
    if not os.path.exists(ALERT_HISTORY_FILE):
        return {}
    with open(ALERT_HISTORY_FILE, "r") as f:
        return json.load(f)


def save_alert_history(history):
    with open(ALERT_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def fetch_gmp_data():

    use_mock = os.getenv("USE_MOCK", "false").lower() in ("1", "true", "yes")

    if use_mock:
        mock_path = os.path.join(os.path.dirname(__file__), "mockdata.json")
        if not os.path.exists(mock_path):
            print("[ERROR] USE_MOCK is true but mockdata.json not found")
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


def should_alert(ipo, alert_history):
    name = ipo.get("company_short_name")
    if not name:
        return False

    if name in alert_history:
        last_alert = datetime.fromisoformat(alert_history[name])
        if datetime.utcnow() - last_alert < timedelta(days=5):
            return False

    return True


def transform_to_email_schema(ipos):
    today = datetime.utcnow().date().isoformat()

    return {
        "model": "InvestorGain GMP API",
        "week": today,
        "ipos": [
            {
                "company_name": ipo["company_short_name"],
                "open_date": ipo["issue_open_dt"][:10],
                "close_date": ipo["issue_end_dt"][:10],
                "price_band": f"₹{ipo.get('ipo_price', 'N/A')}",
                "sector": "N/A",
                "gmp": f"{ipo.get('gmp')} ({ipo.get('gmp_percent_calc')}%)",
                "subscription": {
                    "retail": "N/A",
                    "qib": "N/A",
                    "overall": "N/A"
                },
                "demand_level": "Strong",
                "risk_level": "High",
                "suitable_for": ["Listing gains"]
            }
            for ipo in ipos
        ]
    }


def main():
    print("[INFO] Daily High GMP IPO Alert started")

    if not is_weekday_ist() and not IS_DEBUG:
        print("[INFO] Weekend. Exiting.")
        return

    ipo_list = fetch_gmp_data()
    alert_history = load_alert_history()

    filtered = []

    for ipo in ipo_list:
        if not is_valid_ipo(ipo):
            continue
        if not gmp_above_threshold(ipo):
            continue
        if not should_alert(ipo, alert_history):
            print(f"[INFO] Alert already sent recently for {ipo['company_short_name']}. Skipping.")
            #continue

        filtered.append(ipo)

    if not filtered:
        print("[INFO] No IPOs with GMP > 20%. No email sent.")
        return

    # email_data = transform_to_email_schema(filtered)
    # subject = f"🚀 High GMP IPO Alert (>20%) – {datetime.utcnow().date()}"
    # email_sent  = send_ipo_email(email_data, subject=subject)

    # Send Telegram
    telegram_message = format_telegram_message(filtered)
    telegram_sent = send_telegram_message(telegram_message)


    if telegram_sent:
        for ipo in filtered:
            alert_history[ipo["company_short_name"]] = datetime.utcnow().isoformat()
        save_alert_history(alert_history)
        print("✅ Alerts sent successfully")
    else:
        print("❌ Failed to send alerts")


if __name__ == "__main__":
    main()
