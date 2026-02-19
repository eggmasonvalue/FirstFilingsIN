import json
import logging
import os
from datetime import datetime
from . import config

def setup_logging(log_file=config.LOG_FILE):
    """
    Configure logging to write to a file.
    Overwrites the log file on each run.
    """
    # Remove existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        filename=log_file,
        filemode='w',  # Overwrite mode
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def save_output(filings_data, failed_checks_count, lookback_years, filename="first_filings_output.json"):
    """
    Save the rich, structured output JSON to disk.

    Structure:
    Category -> Date -> List of Filings
    """

    # 1. Transform flat filings list to nested structure
    # Input filings_data structure: { "Category": [ {filing_dict}, ... ], ... }

    nested_data = {}

    for category, filings_list in filings_data.items():
        if category not in nested_data:
            nested_data[category] = {}

        for filing in filings_list:
            # Filing is a dict returned by enrich_filing_data
            if not filing:
                continue

            date_str = filing['date'] # ISO string YYYY-MM-DD

            if date_str not in nested_data[category]:
                nested_data[category][date_str] = []

            # Create the optimized array: [scrip, name, price, cur_price, mkt_cap]
            row = [
                filing['scrip_code'],
                filing['company_name'],
                filing['price_at_announcement'],
                filing['current_price'],
                filing['current_mkt_cap_cr']
            ]

            nested_data[category][date_str].append(row)

    output = {
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "columns": ["scrip_code", "company_name", "price_announcement", "current_price", "current_mkt_cap_cr"],
            "failed_checks_count": failed_checks_count,
            "lookback_years": lookback_years
        },
        "data": nested_data
    }

    try:
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        logging.info(f"Detailed output saved to {filename}")
        return filename
    except Exception as e:
        logging.error(f"Failed to save output file: {e}")
        return None

def print_cli_json(output_file, total_filings, failed_checks_count):
    """
    Print the minimal CLI JSON summary.
    """
    summary = {
        "status": "success",
        "generated_at": datetime.now().isoformat(),
        "total_filings_found": total_filings,
        "failed_checks_count": failed_checks_count,
        "output_file": output_file
    }
    print(json.dumps(summary, indent=2))
