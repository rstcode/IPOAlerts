import re
import json
import os
from typing import List, Dict, Optional
import sys
import time

import requests
from dotenv import load_dotenv
from telegram_alert import send_applicant_results

load_dotenv()

# Configuration - Read from environment variables or use defaults
HTML_URL = os.getenv("IPO_STATUS_HTML_URL", "https://ipostatus.kfintech.com/")
API_URL = os.getenv("IPO_STATUS_API_URL", "https://0uz601ms56.execute-api.ap-south-1.amazonaws.com/prod/api/query")
PAN_COMMA = os.getenv("PAN_COMMA", "")
IPO_NAME_PREFIX = os.getenv("IPO_NAME_PREFIX", "")

JS_PATTERN = re.compile(r"src=[\"'](./static/js/main\.([0-9a-fA-F]+)\.js)[\"']")
CLIENT_DATA_PATTERN = re.compile(r'const rf=JSON\.parse\(\'\[(.+?)\]\'\)')


def fetch_url(url: str, headers: Optional[Dict[str, str]] = None) -> str:
    """Fetch content from a URL using requests library."""
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/125.0.0.0 Safari/537.36"
    }
    if headers:
        default_headers.update(headers)
    
    try:
        response = requests.get(url, headers=default_headers, timeout=20, allow_redirects=True)
        response.raise_for_status()  # Raise exception for bad status codes
        return response.text
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"HTTP error fetching {url}: {e.response.status_code} {e.response.reason}") from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error fetching {url}: {str(e)}") from e


def find_main_js_path(html: str) -> str:
    """Extract the main.js file path from HTML."""
    match = JS_PATTERN.search(html)
    if not match:
        raise ValueError("Could not find main.<hash>.js in the HTML source.")
    return match.group(1)


def extract_client_data(js_source: str) -> List[Dict[str, str]]:
    """Extract client data array from JS source."""
    match = CLIENT_DATA_PATTERN.search(js_source)
    if not match:
        raise ValueError("Could not find client data in JS source.")
    
    json_str = "[" + match.group(1) + "]"
    return json.loads(json_str)


def search_ipo_by_name(clients: List[Dict[str, str]], name_prefix: str) -> Optional[Dict[str, str]]:
    """Search for IPO by name prefix (case-insensitive)."""
    name_prefix = name_prefix.strip().upper()
    
    for client in clients:
        if client["name"].upper().startswith(name_prefix):
            return client
    
    return None


def fetch_applicant_data(client_id: str, pan: str, retry_count: int = 3) -> Dict:
    """Fetch applicant data from the API with retry logic using requests library."""
    headers = {
        "client_id": client_id,
        "origin": "https://ipostatus.kfintech.com",
        "referer": "https://ipostatus.kfintech.com/",
        "reqparam": pan
    }
    
    url = f"{API_URL}?type=pan"
    
    
    for attempt in range(retry_count):
        try:
            response = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
            response.raise_for_status()  # Raise exception for bad status codes
            result = response.json()
            
            
            return result
            
        except requests.exceptions.HTTPError as e:
            
            if e.response.status_code == 502 and attempt < retry_count - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            return {"error": f"HTTP {e.response.status_code}: {e.response.reason}"}
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to fetch: {str(e)}"}


def process_pan_list(clients: List[Dict[str, str]], ipo_name: str, pans: List[str]) -> (List[Dict], str):
    """Process a list of PANs and return results."""
    results = []
    
    # Search for the IPO
    ipo = search_ipo_by_name(clients, ipo_name)
    
    if not ipo:
        print(f"IPO not found for prefix: {ipo_name}")
        return results, "N/A"

    client_id = ipo["clientId"]
    for pan in pans:
        pan = pan.strip().upper()
        
        response = fetch_applicant_data(client_id, pan)
        
        if "error" in response:
            error_msg = response.get("error", "Unknown error")
            print(f"{error_msg}")
            results.append({
                "PAN": pan,
                "Status": "Error",
                "Message": error_msg,
                "Name": None,
                "All_Shares": None
            })
        elif "data" in response and response["data"]:
            applicant = response["data"][0]
            name = applicant.get("Name", "N/A")
            all_shares = applicant.get("All_Shares", "0")
            
            results.append({
                "PAN": pan,
                "Status": "Success",
                "Name": name,
                "All_Shares": int(all_shares) if all_shares.isdigit() else 0
            })
        else:
            results.append({
                "PAN": pan,
                "Status": "Not Found",
                "Message": "Record Not Found",
                "Name": None,
                "All_Shares": None
            })
            #apply some time delay here
            time.sleep(2)

        
    return results,ipo.get("name", "N/A")


def main():
    """Main execution function."""
    try:
        html = fetch_url(HTML_URL)
        js_path = find_main_js_path(html)
        js_url = HTML_URL.rstrip("/") + "/" + js_path.lstrip("./")
        js_source = fetch_url(js_url)
        clients = extract_client_data(js_source)
        
        # Use environment variables or prompt user
        ipo_prefix = IPO_NAME_PREFIX.strip()
        
        if not ipo_prefix:
            print("IPO prefix cannot be empty.")
            return 1
        
        pan_input = PAN_COMMA.strip()
        if not pan_input:
            pan_input = input("Enter PAN numbers (comma-separated): ").strip()
        
        if not pan_input:
            print("PAN list cannot be empty.")
            return 1
        
        pans = [p.strip() for p in pan_input.split(",") if p.strip()]
        if not pans:
            print("No valid PANs provided.")
            return 1
        
        results, ipo_name = process_pan_list(clients, ipo_prefix, pans)
        if not results:
            print("No results found or IPO not found.")
            return 1

        sent = send_applicant_results(results, ipo_name)
        if sent:
            print("✅ Telegram message sent")
        else:
            print("Telegram message failed")
            return 1

        return 0
    
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
