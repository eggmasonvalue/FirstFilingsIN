# System Design: First Filings

## Architecture

The system follows a modular architecture to support multiple exchanges.

### Components

1.  **CLI (`cli.py`)**:
    - Entry point.
    - Parses arguments (`--exchange`, `--period`, etc.).
    - Instantiates specific `ExchangeClient`.
    - Drivers the analysis loop.
    - Handles output file generation.

2.  **Exchange Client (`exchange.py`, `bse_client.py`, `nse_client.py`)**:
    - `ExchangeClient`: Abstract Base Class defining the contract (`fetch_announcements`, `get_enrichment_info`).
    - `BSEClient`: Implements interaction with BSE. Uses `bse` library. Handles pagination and category mapping.
    - `NSEClient`: Implements interaction with NSE (Main/SME). Uses `nse` local library. Handles keyword-based filtering.
    - `Announcement`: Standardized data model for announcements across exchanges.

3.  **Analyzer (`core.py`)**:
    - `FirstFilingAnalyzer`: Contains the business logic.
    - `fetch_announcements`: Delegates to the injected `ExchangeClient`.
    - `is_first_filing`: Checks history via `ExchangeClient` to determine uniqueness.
    - `enrich_filing_data`: Enriches valid findings with market data (Symbol resolution, Prices) using `yfinance`.

4.  **Utilities (`utils.py`, `config.py`)**:
    - Logging setup.
    - Configuration constants (Keywords, Categories).
    - Output formatting (JSON structure).

## Data Flow

1.  CLI initializes `ExchangeClient` based on user input (e.g., `NSEClient(segment="sme")`).
2.  Analyzer fetches announcements for the requested period for selected categories.
3.  For each announcement:
    - Checks history (Lookback period).
    - If it's a "First Filing":
        - Resolves Symbol/Suffix via `ExchangeClient`.
        - Fetches Market Data via `yfinance`.
        - Adds to results.
4.  Results are saved to JSON.

## Extensibility

- **New Exchange**: To add a new exchange, implement `ExchangeClient` and update `cli.py` factories.
- **New Category**: Add to `config.py` and ensure mapping keywords exist.
