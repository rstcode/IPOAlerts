"""
        IPO Alert Generator using Google Gemini API
Fetches Indian IPO data and generates summarized reports
"""

import os
import json
from typing import Dict
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
from google import genai

# Assuming emaillib.py is in the same directory
from emaillib import send_ipo_email

# Load environment variables (.env for local, Secrets for GitHub)
load_dotenv()


def setup_gemini() -> bool:
    """Validate Gemini API key availability"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY is not set")
        return False
    
    return True


def generate_ipo_summary(week_range: str | None = None) -> str:
    """Call Gemini API and return raw response text"""

    prompt_path = os.path.join(os.path.dirname(__file__), "ipo_prompt.txt")

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        print("[ERROR] ipo_prompt.txt not found")
        return "{}"

    print("[INFO] Calling Gemini API...")

    # Use safe replacement instead of str.format to avoid KeyError
    # if the prompt template contains other braces (e.g., JSON blocks).
    prompt = prompt_template.replace("{WEEK_RANGE}", week_range or "")

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    try:
        
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"[ERROR] Gemini API call failed: {e}")
        return "{}"


def clean_and_parse_json(raw_text: str) -> Dict:
    """Strip markdown and safely parse JSON"""

    if not raw_text:
        return {}

    clean_text = raw_text.strip()

    # Remove markdown code blocks if Gemini adds them
    if clean_text.startswith("```"):
        clean_text = clean_text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(clean_text)
    except json.JSONDecodeError as e:
        print("[ERROR] JSON parsing failed")
        print("[DEBUG RAW OUTPUT]")
        print(raw_text)
        return {}


def is_safe_to_send_email() -> bool:
    """
    Prevent spam:
    - Allow emails on manual runs
    - Allow emails only on Monday for scheduled runs
    """
    event = os.getenv("GITHUB_EVENT_NAME")

    if not event:
        # Local run
        return True

    if event == "schedule":
        return datetime.utcnow().weekday() == 0  # Monday

    if event == "workflow_dispatch":
        return True

    return False


def main():
    print("[INFO] Starting Weekly IPO Alert")

    if not setup_gemini():
        return
    
    # Compute current week (Monday to Sunday) and format as YYYY-MM-DD to YYYY-MM-DD
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    dynamic_week = f"{monday.isoformat()} to {sunday.isoformat()}"

    raw_summary = generate_ipo_summary(week_range=dynamic_week)
    
    ipo_data = clean_and_parse_json(raw_summary)

    if not ipo_data:
        print("[ERROR] No valid IPO data received")
        return

    # if not is_safe_to_send_email():
    #     print("[INFO] Not a valid time to send email. Skipping.")
    #     return

    week_range = ipo_data.get("week", "Upcoming Week")
    subject = f"📈 Weekly IPO Alert ({week_range})"

    print("[INFO] Sending email...")
    success = send_ipo_email(ipo_data, subject=subject)

    if success:
        print("✅ Weekly IPO Alert completed successfully")
    else:
        print("❌ Email sending failed")


if __name__ == "__main__":
    main()
