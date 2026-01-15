"""
IPO Alert Generator using Google Gemini API
Fetches Indian IPO data and generates summarized reports
"""

import os
import json
from typing import Union, Dict
from dotenv import load_dotenv
from google import genai
# Assuming emaillib.py is in the same directory
from emaillib import send_ipo_email

# Load environment variables from .env file
load_dotenv()

def setup_gemini() -> bool:
    """Configure Google Gemini API with API key from environment variable"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[WARNING] GEMINI_API_KEY environment variable is not set")
        return False
    return True

def generate_ipo_summary() -> str:
    """
    Generate a summarized IPO report using Google Gemini API
    Returns: Raw JSON string response from Gemini
    """
    
    # Load the prompt from external file
    try:
        prompt_path = os.path.join(os.path.dirname(__file__), "ipo_prompt.txt")
        with open(prompt_path, "r") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        print("[ERROR] ipo_prompt.txt not found.")
        return "{}"

    # Call Gemini API
    # Note: For real-time data, ensure your model has access to Search or you provide context
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    print("[INFO] Sending request to Gemini API...")
    try:
        # Using a standard model that handles JSON well
        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=prompt_template
        )
        return response.text
    except Exception as e:
        print(f"[ERROR] Gemini API call failed: {e}")
        return "{}"

def clean_and_parse_json(raw_text: str) -> Dict:
    """
    Cleans markdown formatting from Gemini response and parses JSON
    """
    if not raw_text:
        return {}

    # Remove markdown code blocks if present
    clean_text = raw_text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    if clean_text.startswith("```"):
        clean_text = clean_text[3:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
        
    try:
        return json.loads(clean_text.strip())
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON: {e}")
        print(f"[DEBUG] Raw text was: {raw_text}")
        return {}

def main():
    """Main function to generate alert and send email"""
    
    # 1. Setup
    if not setup_gemini():
        return

    # 2. Generate Content
    raw_summary = generate_ipo_summary()
    
    # 3. Parse JSON
    print("[INFO] Parsing Gemini response...")
    ipo_data = clean_and_parse_json(raw_summary)
    
    if not ipo_data:
        print("[ERROR] No valid IPO data found to send.")
        return

    # 4. Check if there are IPOs to report (Optional logic)
    # If the list is empty, you might still want to send a "No IPOs this week" email
    # which your template handles automatically.
    
    # 5. Send Email
    print("[INFO] Formatting and sending email...")
    week_range = ipo_data.get("week", "Upcoming Week")
    subject = f"📈 IPO Alerts: Weekly Summary ({week_range})"
    
    success = send_ipo_email(ipo_data, subject=subject)
    
    if success:
        print("✅ Process completed successfully.")
    else:
        print("❌ Process finished with email errors.")

if __name__ == "__main__":
    main()