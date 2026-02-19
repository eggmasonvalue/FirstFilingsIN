# Design & Features

## Implemented Features
- [x] **Date Range Parsing**: Supports `day`, `wtd`, `mtd`, `qtd`.
- [x] **Category Filtering**: Monitors "Analyst Call Intimation", "Press Release", and "PPT".
- [x] **First Filing Logic**: Verifies uniqueness against a historical lookback window (default 15 years).
- [x] **Data Enrichment**: Adds Symbol, Historical Price, Current Price, and Market Cap (in Crores).
- [x] **Retry Logic**: Handles network flakes with **exponential backoff** and 15 retries (using `tenacity`).
- [x] **Logging**: Silent execution with file logging (`first_filings.log`).
- [x] **Output**:
  -   Detailed JSON saved to disk (`first_filings_output.json`).
  -   Minimal JSON summary printed to stdout.
- [x] **Modularization**: Split into `cli`, `core`, `bse_client`, `config`, `utils`.

## Pending / Planned
- [ ] **Notifications**: Email alerts (via GitHub Actions).
- [ ] **CI/CD**: Automated testing and deployment pipeline.

## Known Issues
-   **Rate Limiting**: Aggressive scraping might trigger BSE rate limits.
-   **Data Gaps**: `yfinance` might not have data for all BSE scrips.
