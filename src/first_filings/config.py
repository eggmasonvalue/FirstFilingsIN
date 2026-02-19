# src/first_filings/config.py

# Retry configuration
TOTAL_RETRIES = 60
RETRY_MIN_DELAY = 1  # Minimum delay in seconds
RETRY_MAX_DELAY = 600  # Maximum delay in seconds
RETRY_MULTIPLIER = 2  # Multiplier for exponential backoff

# Filing categories
FILING_CATEGORY = "Company Update"
SUBCATEGORY_GENERAL = "General"

FILING_SUBCATEGORY = {
    "Analyst Call Intimation": ["Analyst / Investor Meet"],
    "Press Release": [
        "Press Release / Media Release",
    ],
    "PPT": ["Investor Presentation", SUBCATEGORY_GENERAL],
}

FILING_SUBCATEGORY_GENERAL_KEYWORD = {
    "PPT": "Presentation"
}

NSE_CATEGORY_KEYWORDS = {
    "Analyst Call Intimation": ["Analyst", "Institutional Investor", "Meet", "Con. Call"],
    "Press Release": ["Press Release", "Media Release"],
    "Presentation": ["Presentation", "Investor Presentation"]
}

# CLI Flags mapping
# Flag: Key in FILING_SUBCATEGORY
CLI_FLAGS = {
    "analyst_calls": "Analyst Call Intimation",
    "press_releases": "Press Release",
    "presentations": "PPT",
}

# Logging
LOG_FILE = "first_filings.log"
ARCHIVE_FILE = "first_filings_archive.json"
