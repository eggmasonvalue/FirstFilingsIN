# Design & Features

## Implemented Features
- [x] **Date Range Parsing**: Supports `day`, `wtd`, `mtd`, `qtd`.
- [x] **Category Filtering**: Fetches specific subcategories (Analyst Call, Press Release, PPT) or all.
- [x] **Pagination & Retries**: Handles pagination loops and API failures with exponential backoff using `tenacity`.
- [x] **First Filing Check**: Efficiently checks history to verify uniqueness.
- [x] **Data Enrichment**: Adds market context (Price, Market Cap).
- [x] **Multi-Exchange Support**:
    - [x] **BSE**: Via `bse` library.
    - [x] **NSE Main**: Via `nse` library (index="equities").
    - [x] **NSE SME**: Via `nse` library (index="sme").
- [x] **Modular Architecture**:
    - `ExchangeClient` interface for pluggable exchange support.
    - `Announcement` data model for standardization.
- [x] **CLI Interface**: Robust command-line options for exchange, period, categories, and lookback.
- [x] **Output Management**: Separate JSON outputs per exchange to avoid overwrites.

## Pending / Future
- [ ] **Async I/O**: Parallel fetching for faster historical checks.
- [ ] **Database Integration**: Store filings in SQLite/Postgres to avoid redundant API calls.
- [ ] **Alerting**: Slack/Telegram integration for real-time alerts.

## Architecture

1.  **CLI (`cli.py`)**: Entry point. Parses args and instantiates the correct `ExchangeClient`.
2.  **Exchange Layer (`src/first_filings/exchange.py`, `bse_client.py`, `nse_client.py`)**:
    -   `ExchangeClient`: Abstract base class.
    -   `BSEClient`: Implements BSE logic.
    -   `NSEClient`: Implements NSE logic with keyword filtering.
3.  **Analyzer (`src/first_filings/core.py`)**: Orchestrates fetching, first-filing checks (`is_first_filing`), and enrichment (`enrich_filing_data`).
4.  **Utilities**: Config handling, Logging, and JSON output generation.
