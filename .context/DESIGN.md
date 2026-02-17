# Design & Features

## Implemented Features
- [x] **Date Range Parsing**: Supports `day`, `wtd`, `mtd`, `qtd`.
- [x] **Category Filtering**: Monitors "Analyst Call Intimation", "Press Release", and "PPT".
- [x] **First Filing Logic**: Verifies uniqueness against a historical lookback window (default 15 years).
- [x] **Retry Logic**: Handles network flakes with **exponential backoff** and 15 retries (using `tenacity`).
- [x] **Logging**: Silent execution with file logging (`first_filings.log`).
- [x] **Output**: Structured JSON output to stdout.
- [x] **Archival**: Appends results to `first_filings_archive.json`.
- [x] **Modularization**: Split into `cli`, `core`, `bse_client`, `config`, `utils`.

## Pending / Planned
- [ ] **Notifications**: Email or Telegram alerts (currently Console only).
- [ ] **CI/CD**: Automated testing and deployment pipeline.

## Known Issues
-   **Rate Limiting**: Aggressive scraping might trigger BSE rate limits, though backoff mitigates this.
-   **Dependency**: Relies on `bse` library which scrapes the BSE website. Website changes might break the library.
