import os
import json
import re
from html import unescape
import requests
from datetime import datetime, date, timedelta, timezone
from dotenv import load_dotenv
from telegram_alert import send_telegram_message, format_telegram_message

load_dotenv()

GMP_API_URL = "https://ipocentral.in/wp-json/ipo-gmp/v1/data"
GMP_UI_URL = 'https://www.ipoguru.in/live-ipo-gmp'
GMP_THRESHOLD = 20.0

ALERT_HISTORY_FILE = "sent_alerts.json"
IS_DEBUG = os.getenv("IS_DEBUG", "false").lower() in ("1", "true", "yes")
IS_MOCK = os.getenv("IS_MOCK", "false").lower() in ("1", "true", "yes")
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "X-Requested-With": "XMLHttpRequest",
}


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


def normalize_gmp_payload(payload):
    if isinstance(payload, dict):
        if isinstance(payload.get("ipoList"), list):
            return payload["ipoList"]

        normalized = []
        for section_key in ("MB", "SME"):
            section = payload.get(section_key)
            if section_key == "SME":
                continue  # Skip SME section for now:
            if not isinstance(section, list):
                continue
            for item in section:
                if not isinstance(item, dict):
                    continue

                date_text = item.get("date") or ""
                open_dt, end_dt = _parse_date_range(date_text)
                gmp_amount = _parse_amount(str(item.get("num") or item.get("gmp") or ""))
                gmp_percent = _parse_amount(str(item.get("pct") or item.get("gmpPercent") or ""))
                if not gmp_percent and item.get("gmpText"):
                    gmp_text = str(item.get("gmpText", ""))
                    parts = re.findall(r"[-+]?\d+(?:\.\d+)?", gmp_text)
                    if len(parts) >= 2:
                        gmp_amount = _parse_amount(parts[0])
                        gmp_percent = _parse_amount(parts[1])

                normalized.append({
                    "company_short_name": item.get("name") or "",
                    "issue_open_dt": open_dt or f"{datetime.now(timezone.utc).date().isoformat()}T00:00:00.000Z",
                    "issue_end_dt": end_dt or f"{datetime.now(timezone.utc).date().isoformat()}T00:00:00.000Z",
                    "ipo_status": _infer_ipo_status(open_dt or "", end_dt or ""),
                    "gmp": gmp_amount,
                    "gmp_percent_calc": gmp_percent or "0",
                    "ipo_price": "",
                    "url": item.get("url") or item.get("link") or item.get("ipo_url") or "",
                })
        return normalized

    if isinstance(payload, list):
        return payload

    return []


def fetch_url(url: str, timeout: int = 20):
    last_error = None
    for attempt in range(2):
        try:
            response = requests.get(url, timeout=timeout, headers=REQUEST_HEADERS, allow_redirects=True)
            if response.status_code < 400:
                return response
            last_error = RuntimeError(f"{response.status_code} {response.reason}")
            if response.status_code in {403, 429} and attempt == 0:
                print(f"[WARN] Retrying {url} after HTTP {response.status_code}")
        except requests.RequestException as exc:
            last_error = exc
            if attempt == 0:
                print(f"[WARN] Request failed for {url}: {exc}")
    raise last_error or RuntimeError(f"Failed to fetch {url}")


def fetch_gmp_data():

    if IS_MOCK:
        mock_path = os.path.join(os.path.dirname(__file__), "mockdata.json")
        if not os.path.exists(mock_path):
            print("[ERROR] IS_MOCK is true but mockdata.json not found")
            return []
        try:
            with open(mock_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return normalize_gmp_payload(data)
        except Exception as e:
            print(f"[ERROR] Failed to read mockdata.json: {e}")
            return []
    try:
        response = fetch_url(GMP_API_URL, timeout=20)
        data = response.json()
        if data:
            normalized = normalize_gmp_payload(data)
            if normalized:
                return normalized
        print("[WARN] GMP API returned no normalized IPOs, falling back to UI HTML parser")
    except Exception as e:
        print(f"[ERROR] Failed to fetch GMP data: {e}")

    html = fetch_gmp_from_ui_url()
    if html:
        return parse_gmp_html_to_json(html)
    return []


def fetch_gmp_from_ui_url():
    try:
        response = fetch_url(GMP_UI_URL, timeout=20)
        return response.text
    except Exception as e:
        print(f"[ERROR] Failed to fetch GMP data from UI URL: {e}")
        return ""


def _extract_text(html: str) -> str:
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.S | re.I)
    text = re.sub(r'<[^>]+>', '', text)
    return unescape(text).strip()


def _parse_amount(text: str) -> str:
    if not text:
        return ""
    text = unescape(text)
    text = text.replace("₹", "").replace("Rs", "").replace("INR", "").replace("%", "")
    text = text.strip().replace("\xa0", " ")
    text = re.sub(r'[\s,]+', '', text)
    return "" if text in ("-", "–", "—", "") else text


def _parse_day_month(value: str, reference: date, fallback_month: int | None = None) -> date | None:
    value = value.strip()
    match = re.match(r'^(\d{1,2})(?:\s+([A-Za-z]{3}))?$', value)
    if not match:
        return None
    day = int(match.group(1))
    month_str = match.group(2)

    if month_str:
        try:
            month = datetime.strptime(month_str.title(), "%b").month
        except ValueError:
            return None
    elif fallback_month is not None:
        month = fallback_month
    else:
        month = reference.month

    year = reference.year
    if month < reference.month - 6:
        year += 1
    elif month > reference.month + 6:
        year -= 1

    try:
        return date(year, month, day)
    except ValueError:
        return None


def _parse_date_range(text: str) -> tuple[str, str] | tuple[None, None]:
    if not text:
        return None, None

    cleaned = re.sub(r'[\(\)]', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    parts = [part.strip() for part in re.split(r'\s*-\s*', cleaned) if part.strip()]
    if len(parts) != 2:
        return None, None

    today = datetime.now(timezone.utc).date()
    start_part, end_part = parts[0], parts[1]

    start_month = None
    end_month = None

    start_month_match = re.search(r'([A-Za-z]{3})', start_part)
    if start_month_match:
        try:
            start_month = datetime.strptime(start_month_match.group(1).title(), "%b").month
        except ValueError:
            start_month = None

    end_month_match = re.search(r'([A-Za-z]{3})', end_part)
    if end_month_match:
        try:
            end_month = datetime.strptime(end_month_match.group(1).title(), "%b").month
        except ValueError:
            end_month = None

    start = _parse_day_month(start_part, today, fallback_month=end_month if start_month is None else None)
    end = _parse_day_month(end_part, today, fallback_month=start_month if end_month is None else None)
    if not start or not end:
        return None, None

    if end < start:
        end = date(start.year + 1, end.month, end.day)

    return start.isoformat() + "T00:00:00.000Z", end.isoformat() + "T00:00:00.000Z"


def _infer_ipo_status(open_date: str, close_date: str) -> str:
    try:
        start = datetime.fromisoformat(open_date[:10]).date()
        end = datetime.fromisoformat(close_date[:10]).date()
    except Exception:
        return "Upcoming"

    today = datetime.now(timezone.utc).date()
    if start <= today <= end:
        return "Open"
    if end < today:
        return "Closed"
    return "Upcoming"


def _is_mainboard_ipo(company_html: str) -> bool:
    spans = re.findall(r'<span[^>]*>(.*?)</span>', company_html, flags=re.S | re.I)
    for span in spans:
        if _extract_text(span).strip().lower() == "mainboard":
            return True
    return False


def parse_gmp_html_to_json(html: str) -> list:
    rows = re.findall(r'<tr[^>]*\bid="ipo-[^"]*"[^>]*>(.*?)</tr>', html, flags=re.S | re.I)
    parsed = []

    for row in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, flags=re.S | re.I)
        if len(cells) < 5:
            continue

        company_html = cells[0]
        if not _is_mainboard_ipo(company_html):
            continue

        issue_price_html = cells[1]
        gmp_html = cells[2]
        gmp_pct_html = cells[3]

        company_name_match = re.search(r'<a[^>]*>(.*?)</a>', company_html, flags=re.S | re.I)
        company = _extract_text(company_name_match.group(1)) if company_name_match else _extract_text(company_html)

        company_url_match = re.search(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>', company_html, flags=re.S | re.I)
        company_url = company_url_match.group(1) if company_url_match else ""

        date_match = re.search(r'([0-9]{1,2}\s+[A-Za-z]{3}\s*-\s*[0-9]{1,2}\s+[A-Za-z]{3})', company_html)
        open_dt, end_dt = _parse_date_range(date_match.group(1)) if date_match else (None, None)

        issue_price = _parse_amount(_extract_text(issue_price_html))
        gmp_amount = _parse_amount(_extract_text(gmp_html))
        gmp_percent = _extract_text(gmp_pct_html).replace("%", "").strip()
        if gmp_percent in ("", "--"):
            gmp_percent = "0"

        parsed.append({
            "company_short_name": company,
            "issue_open_dt": open_dt or f"{datetime.now(timezone.utc).date().isoformat()}T00:00:00.000Z",
            "issue_end_dt": end_dt or f"{datetime.now(timezone.utc).date().isoformat()}T00:00:00.000Z",
            "ipo_status": _infer_ipo_status(open_dt or "", end_dt or ""),
            "gmp": gmp_amount,
            "gmp_percent_calc": gmp_percent,
            "ipo_price": issue_price,
            "url": company_url,
        })

    return parsed


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
        #return

    ipo_list = fetch_gmp_data()
    print(f"[INFO] Fetched {len(ipo_list)} IPOs from GMP API")
    history = load_alert_history()
    print(f"[INFO] Loaded {len(history)} entries from alert history")

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
