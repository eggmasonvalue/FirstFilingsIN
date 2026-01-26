# Design & Features

## Implemented Features
- [x] **Date Range Parsing**: Supports `-WTD` (Week to Date), `-MTD` (Month to Date), `-QTD` (Quarter to Date), and `-D` (Specific Day).
- [x] **Category Filtering**: Monitors "Analyst Call Intimation", "Press Release", and "PPT".
- [x] **First Filing Logic**: Verifies uniqueness against a historical lookback window.
- [x] **Retry Logic**: Handles network flakes with retries.

## Pending / Planned
- [ ] **Data Persistence**: Cache results to avoid re-fetching historical data repeatedly.
- [ ] **Notifications**: Email or Telegram alerts (currently Console only).
- [ ] **Modularization**: Split `FirstFilingsBSE.py` into smaller modules (e.g., `fetcher.py`, `analyzer.py`).

## Known Issues
-   **Rate Limiting**: Aggressive scraping might trigger BSE rate limits.
-   **Error Handling**: Some "Unexpected result type" errors are swallowed or skipped.
