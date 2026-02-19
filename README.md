# First Filings Finder

This tool fetches corporate announcements from BSE and NSE (Mainboard & SME) to identify "first filings" of specific types (e.g., Analyst Call Intimations, Press Releases, Investor Presentations) within a specified lookback period.

## Value Proposition
The first investor presentation, analyst or earnings call intimation or media release often signifies the start of the market's discovery of the company or the promoter's interest in value creation via market capitalisation increase, often leading to rapid rerating.

### Note:
This repo has been designed putting AI agents first. So, expect token-efficient CLI output with progressive disclosure, silent execution on the terminal, graceful exits with status information provided in the CLI return. If you're a human, use the log to be informed of progress.

AI agent skill coming soon to help agents understand the tool better. If you're a human, the recommended approach is to ask the agent to use the tool and generate a dashboard tailored to YOU. All frontend is bloat in the LLM era. Inference-time frontend FTW!

## Features

- **Multi-Exchange Support**: BSE(SME and Mainboard), NSE Mainboard, NSE SME.
- **First Filing Detection**: Checks if a company has made a specific type of announcement in the past `N` years.
- **Enrichment**: Adds Current Market Cap, Current Price, and Price at Announcement (using `yfinance`).
- **Flexible Filtering**: Filter by Date Range (Day, WTD, MTD, QTD) and Categories.
- **Output**: JSON file with structured data.

## Installation

This project uses `uv` for dependency management.

```bash
# Install dependencies
uv sync
```

## Usage

Run the tool using `uv run first-filings`.

### Basic Command

```bash
# Fetch BSE announcements for today (default)
uv run first-filings

# Fetch NSE Mainboard announcements for today
uv run first-filings --exchange nse-main

# Fetch NSE SME announcements
uv run first-filings --exchange nse-sme
```

### Options

- `--exchange`: `bse` (default), `nse-main`, `nse-sme`.
- `--period`: `day` (default), `wtd`, `mtd`, `qtd`.
- `--date`: Reference date (DD-MM-YYYY). Defaults to today.
- `--lookback-years`: Number of years to check history (default: 2).
- `-a` / `--analyst-calls`: Fetch Analyst Call Intimations.
- `-p` / `--press-releases`: Fetch Press Releases.
- `-t` / `--presentations`: Fetch Investor Presentations.

### Examples

```bash
# Check for first Analyst Calls on NSE Mainboard for the current month
uv run first-filings --exchange nse-main --period mtd --analyst-calls

# Check for Press Releases on BSE with a 3-year lookback
uv run first-filings --exchange bse --lookback-years 3 --press-releases
```

## Output

The tool generates a JSON output file based on the exchange (e.g., `bse_output.json`, `nse_main_output.json`).

**Structure:**
```json
{
  "meta": {
    "generated_at": "...",
    "columns": ["scrip_code", "company_name", "price_announcement", "current_price", "current_mkt_cap_cr"],
    "failed_checks_count": 0,
    "lookback_years": 2
  },
  "data": {
    "Analyst Call Intimation": {
      "YYYY-MM-DD": [
        ["Symbol", "Company Name", Price, CurrentPrice, MktCap],
        ...
      ]
    }
  }
}
```
