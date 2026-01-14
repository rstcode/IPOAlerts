# IPO Alert - Weekly Indian IPO Summary Generator

A Python script that fetches Indian IPO data and generates concise, neutral summaries using Google Gemini API.

## Phase 1 (Current)
- ✅ Gemini API integration (gemini-1.5-flash)
- ✅ IPO summary generation with structured analysis
- ✅ Mock IPO data support
- ✅ Environment variable for API key

## Setup

### Prerequisites
- Python 3.8+
- Google Gemini API key

### Installation

1. Install dependencies:
```bash
py -m pip install -r requirements.txt
```

2. Set up your Gemini API key:
```bash
# Windows (PowerShell)
$env:GEMINI_API_KEY = "your-api-key-here"

# Windows (Command Prompt)
set GEMINI_API_KEY=your-api-key-here

# Linux/Mac
export GEMINI_API_KEY="your-api-key-here"
```

### Usage

Run the script:
```bash
python ipo_alert.py
```

### Output Format

The script generates a neutral, plain-text IPO summary including:
- Company details (name, sector)
- Key dates (opening, closing, listing)
- Price band and GMP
- Subscription metrics (Retail, QIB, Overall)
- Demand and risk assessment
- Suitable investor types
- Key observations

## Function Reference

### `setup_gemini()`
Initializes Gemini API with credentials from `GEMINI_API_KEY` environment variable.

### `generate_ipo_summary(ipo_data: Union[Dict, str]) -> str`
Accepts IPO data as dict or JSON string, sends to Gemini, returns formatted summary.

## Future Phases
- [ ] Live IPO data fetching
- [ ] WhatsApp/Email notifications
- [ ] GitHub Actions weekly scheduler
- [ ] GPT fallback option
