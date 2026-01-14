"""
IPO Alert Generator using Google Gemini API
Fetches Indian IPO data and generates summarized reports
"""

import os
import json
from typing import Union, Dict
from dotenv import load_dotenv
from google import genai

# Load environment variables from .env file
load_dotenv()


def setup_gemini() -> bool:
    """Configure Google Gemini API with API key from environment variable
    
    Returns:
        True if API key is configured, False otherwise
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[WARNING] GEMINI_API_KEY environment variable is not set")
        return False
    
    return True


def generate_ipo_summary(ipo_data: Union[Dict, str]) -> str:
    """
    Generate a summarized IPO report using Google Gemini API
    
    Args:
        ipo_data: IPO information as a dictionary or JSON string
    
    Returns:
        Plain text IPO summary suitable for email/WhatsApp
    """
    
    # Convert dict to string if needed
    if isinstance(ipo_data, dict):
        ipo_data_str = json.dumps(ipo_data, indent=2)
    else:
        ipo_data_str = str(ipo_data)
    
    # Load the prompt from external file
    prompt_file = os.path.join(os.path.dirname(__file__), "ipo_prompt.txt")
    with open(prompt_file, "r") as f:
        prompt_template = f.read()
    
    # Construct the prompt for Gemini
    prompt = prompt_template.format(ipo_data_str=ipo_data_str)
    
    # Call Gemini API using google-genai SDK
    client = genai.Client()
    print("[INFO] Sending request to Gemini API...")
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt_template
    )
    
    return response.text


def main():
    """Main function to demonstrate IPO alert generation"""
    
    # Sample IPO data (mock data for Phase 1)
    sample_ipo_data = {
        "company_name": "Varun Beverages Ltd (VBL)",
        "sector": "Beverages",
        "opening_date": "2023-03-20",
        "closing_date": "2023-03-22",
        "price_band": "₹305 - ₹320",
        "gmp": "₹125 - ₹135",
        "retail_subscription": "2.5x",
        "qib_subscription": "4.8x",
        "overall_subscription": "3.2x",
        "issue_size": "₹2,000 Cr",
        "market_cap_post_listing": "₹25,000 Cr",
        "listing_date": "2023-03-27",
        "listing_gain": "42%"
    }
    
    # Setup Gemini API
    api_configured = setup_gemini()
    
    if not api_configured:
        print("[ERROR] Cannot proceed without API key")
        return
    
    # Generate and print the IPO summary
    summary = generate_ipo_summary(sample_ipo_data)
    print(summary)


if __name__ == "__main__":
    main()
