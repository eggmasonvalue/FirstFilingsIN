# Architecture

## High-Level Flow

```mermaid
graph TD
    User[User / CLI] -->|Run Script with Options| CLI[CLI Controller]
    CLI -->|Setup Logging| Utils[Utils]
    CLI -->|Fetch Announcements| Core[Core Logic]
    Core -->|Get Data (with Retry)| Client[BSE Client]
    Client -->|Fetch Data| BSE[BSE Library / API]
    Core -->|Check History| Client
    Client -->|Fetch Historic Data| BSE
    CLI -->|Archive Result| Utils
    CLI -->|Print JSON| Console[Console Output]
```

## Modules

### `src/first_filings/cli.py`
The entry point for the application using `click`.
- **`main()`**: Parses arguments (`date`, `period`, `lookback_years`) and orchestrates the flow.
- **`get_date_range()`**: Utility to calculate date ranges based on period.

### `src/first_filings/core.py`
Contains the business logic.
- **`FirstFilingAnalyzer`**: Class to analyze filings.
    - **`fetch_announcements`**: Fetches and filters announcements for a date range.
    - **`is_first_filing`**: Checks if a filing is unique in the lookback window.
    - **`_filter_announcements`**: Internal helper to filter by keywords.

### `src/first_filings/bse_client.py`
Handles interaction with the BSE library.
- **`BSEClient`**: Wrapper around `bse` library.
    - **`fetch_paginated_announcements`**: Fetches data with **exponential backoff** and retries (using `tenacity`).

### `src/first_filings/config.py`
Configuration constants.
- **`FILING_CATEGORY`**, **`FILING_SUBCATEGORY`**: Categories to monitor.
- **`TOTAL_RETRIES`**, **`RETRY_DELAY`**: Retry settings.

### `src/first_filings/utils.py`
Utility functions.
- **`setup_logging`**: Configures logging to file.
- **`print_json_output`**: Prints structured JSON to stdout.
- **`archive_output`**: Appends result to archive file.

## Data Flow
1.  **Input**: Date, Period, Lookback period.
2.  **Process**:
    -   Calculate date range.
    -   Fetch all announcements for the target range (with retries).
    -   For each announcement, query historical data (lookback period) to see if a similar announcement exists.
3.  **Output**: Structured JSON object with list of companies with their "First Filing".
4.  **Archive**: Result is appended to `first_filings_archive.json`.
