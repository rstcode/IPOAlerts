import os
import re
import requests
from datetime import datetime, timezone

# ------------------ Telegram Sender ------------------

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
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    response = requests.post(url, json=payload, timeout=10)
    return response.status_code == 200


# ------------------ Formatting ------------------

def get_gmp_badge(gmp_percent: float):
    if gmp_percent >= 50:
        return "🔥"
    elif gmp_percent >= 30:
        return "⚡"
    else:
        return "✅"


def format_short_date(date_str: str) -> str:
    """Convert ISO date like '2026-01-13' or full datetime to '13 Jan'."""
    if not date_str:
        return "N/A"
    try:
        # Accept 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SS' etc.
        date_part = date_str.split("T")[0]
        d = datetime.fromisoformat(date_part)
        return d.strftime("%d %b")
    except Exception:
        # Fallback: try to slice YYYY-MM-DD
        try:
            return date_str[:10].replace("-", " ")
        except Exception:
            return date_str


def format_telegram_message(categories, history):
    today = datetime.now(timezone.utc).strftime("%d %b %Y")

    msg = (
        "🚀 <b>High GMP IPO Alert</b>\n"
        f"📅 <b>{today}</b>\n\n"
    )

    def render(title, ipos):
        nonlocal msg
        if not ipos:
            return

        msg += f"<b>{title}:</b>\n"
        for index, ipo in enumerate(ipos,1):
            name = ipo["company_short_name"]
            gmp = float(ipo.get("gmp_percent_calc", 0))
            #badge = get_gmp_badge(gmp)

            # ---- GMP variation logic ----
            variation_text = ""
            if name in history:
                prev_entry = history[name]
                last_gmp = prev_entry.get("last_gmp_percent")
                if last_gmp is None:
                    variation_text = f"Yesterday → Today GMP: N/A → {gmp:.1f}%"
                else:
                    last_gmp = float(last_gmp)
                    diff = round(gmp - last_gmp, 1)
                    if diff > 0:
                        variation_text = f"Yesterday → Today GMP: {last_gmp:.1f}% → {gmp:.1f}%"
                    elif diff < 0:
                        variation_text = f"Yesterday → Today GMP: {last_gmp:.1f}% → {gmp:.1f}%"
                    else:
                        variation_text = f"Yesterday → Today GMP: {last_gmp:.1f}% → {gmp:.1f}%"
            else:
                variation_text = f"Yesterday → Today GMP: N/A → {gmp:.1f}%"

            link = ipo.get("url") or ipo.get("link") or ipo.get("ipo_url")
            if link:
                link_text = f"\n• Link: <a href=\"{link}\">IPO Info</a>"
            else:
                link_text = ""

            msg += (
                f"<b>{index}). {name}</b>\n"
                f"• Open: {format_short_date(ipo.get('issue_open_dt'))}\n"
                f"• Close: {format_short_date(ipo.get('issue_end_dt'))}\n"
                f"• GMP: <b>{gmp}%</b> | ₹{ipo.get('gmp')}\n"
                f"• {variation_text}{link_text}\n\n"
            )

    render("🔴 LAST DAY (Closes Today)", categories["last_day"])
    render("🟢 OPEN NOW", categories["open_now"])
    render("🟡 UPCOMING (Next 7 Days)", categories["upcoming"])
    msg += ("\t<b>Note:</b> Double check before making any investment decisions.\n")
    msg += ("\t<i>  -rstcode.</i>")

    return msg


def format_applicant_results_message(results, ipo_name: str) -> str:
    """Format applicant allotment results into a Telegram-friendly message."""
    total = len(results)
    successful = sum(1 for r in results if r.get("Status") == "Success")
    failed = total - successful

    msg = f"📣 <b>{ipo_name} </b>📣\nIPO allotment status is out.\n"
    msg += f"Total PAN's: {total} | Success: {successful} | Failed: {failed}\n\n"

    for r in results:
        pan = r.get("PAN")
        status = r.get("Status")
        if status == "Success":
            name = r.get("Name") or "N/A"
            name = re.sub(r'^(MR|MS)\.?\s+', '', name, flags=re.IGNORECASE)
            shares = r.get("All_Shares") if r.get("All_Shares") is not None else r.get("App_Shares", "0")
            msg += f"• {name}: <b>{shares} shares.</b>\n"

    msg += "\n<i>This is an allotment status triggerd by rstcode.</i>\n"
    return msg


def send_applicant_results(results, ipo_name: str) -> bool:
    """Format and send applicant results to Telegram using `send_telegram_message`.

    Returns True if the Telegram API reported success.
    """
    message = format_applicant_results_message(results, ipo_name)
    return send_telegram_message(message)
