from datetime import datetime
import requests
import os

def send_telegram_message(message: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("[ERROR] Telegram credentials missing")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }

    response = requests.post(url, json=payload, timeout=10)

    if response.status_code == 200:
        print("✅ Telegram message sent")
        return True
    else:
        print("❌ Telegram send failed:", response.text)
        return False

def get_gmp_badge(gmp_percent: float):
    if gmp_percent >= 50:
        return "🔥 Extremely Hot"
    elif gmp_percent >= 30:
        return "⚡ Very Strong"
    else:
        return "✅ Strong"


def format_telegram_message(ipos):
    from datetime import datetime

    today = datetime.utcnow().strftime("%d %b %Y")

    msg = (
        "🚀 <b>High GMP IPO Alert</b>\n\n"
        f"📅 <b>{today}</b>\n\n"
    )

    for ipo in ipos:
        try:
            gmp_percent = float(ipo.get("gmp_percent_calc", 0))
        except ValueError:
            continue

        badge = get_gmp_badge(gmp_percent)

        msg += (
            f"{badge}\n"
            f"🔹 <b>{ipo['company_short_name']}</b>\n"
            f"• Open: {ipo['issue_open_dt'][:10]} | Close: {ipo['issue_end_dt'][:10]}\n"
            f"• IPO Price: ₹{ipo.get('ipo_price', 'N/A')}\n"
            f"• GMP: ₹{ipo.get('gmp')} ({gmp_percent}%)\n\n"
        )

    msg += (
        "ℹ️ <i>GMP is unofficial and can change daily.</i>\n"
        "<i>For informational purposes only.</i>"
    )

    return msg
