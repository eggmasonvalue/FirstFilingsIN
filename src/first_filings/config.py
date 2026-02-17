# src/first_filings/config.py

# Retry configuration
TOTAL_RETRIES = 15
RETRY_MIN_DELAY = 1  # Minimum delay in seconds
RETRY_MAX_DELAY = 60  # Maximum delay in seconds
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

# Logging
LOG_FILE = "first_filings.log"
ARCHIVE_FILE = "first_filings_archive.json"
