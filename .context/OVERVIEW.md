# Project Overview: First Filings

The **First Filings** project identifies the first time a company makes a specific type of announcement (e.g., Analyst Call, Press Release, Presentation) within a lookback period. This helps investors spot companies that are starting to communicate more actively with the market, which can be a signal of change.

## Core Features

- **Multi-Exchange Support**:
    - **BSE (Bombay Stock Exchange)**: Fetches announcements using `bse` library.
    - **NSE (National Stock Exchange)**: Fetches Mainboard ("equities") and SME ("sme") announcements using `nse` library.
- **Announcement Filtering**:
    - Supports specific categories: Analyst Call Intimations, Press Releases, Investor Presentations.
    - Uses efficient keyword filtering (e.g., "Analyst", "Presentation").
- **First Filing Detection**:
    - Checks history (default 2 years) to see if an announcement type is the first of its kind for a company.
- **Data Enrichment**:
    - Enriches findings with Market Cap, Current Price, and Price at Announcement using `yfinance`.
- **Output**:
    - Generates separate JSON files for each exchange (e.g., `bse_output.json`, `nse_sme_output.json`).

## Technology Stack

- **Python 3.12+**
- **Libraries**: `click`, `yfinance`, `tenacity`.
- **Exchange libs**: `bse` (PyPI), `nse` (Local/PyPI).
- **Package Management**: `uv`.
