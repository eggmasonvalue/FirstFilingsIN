
# Changelog

## [2.3.2] - 2026-03-18

### Added
-   **Testing**: Added unit tests for `save_output` in `utils.py`, covering both successful data transformation and error handling (e.g., file permission issues).

## [2.3.1] - 2026-02-27

### Optimized
-   **NSE Client**: Optimized announcement filtering logic by pre-calculating lowered keywords and lowercasing the description once per item, resulting in ~50% reduction in filtering time.

## [2.3.0] - 2026-02-26

### Added
-   **Financial Snapshot**: Added `financial_snapshot` field to BSE output (via `bse.resultsSnapshot`) and displayed it as a Markdown table in Discord notifications.
-   **Resilience**: Introduced a 350ms delay between BSE pagination requests to prevent server timeouts and throttling.

### Changed
-   **Dependencies**: Updated `bse` dependency to `>=3.2.0` to support new API methods.
-   **Resilience**: Optimized retry configuration (reduced max retries to 10 and max delay to 30s) to fail fast on persistent issues while handling transient ones.

### Fixed
-   **Regression**: Fixed broken Market Cap field in BSE output by migrating from `stockTrading` to `getScripTradingStats`.
-   **Workflow**: Resolved issue where BSE workflow would get stuck for hours due to infinite retry loops on timeouts.

## [2.2.1] - 2026-02-21

### Added
-   **CI/CD**: Exposed `period`, `lookback_years`, and category flags (`analyst_calls`, `press_releases`, `presentations`) as inputs in `daily_run.yml` workflow dispatch.

## [2.2.0] - 2026-02-21

### Added
-   **Resilience**: Implemented centralized retry mechanism (`src/first_filings/retries.py`) handling `TimeoutError` and specific `ConnectionError` codes (429, 502, 503, 504) for both BSE and NSE clients.
-   **NSE/BSE Client**: Updated clients to use the new smart retry decorator, improving reliability during transient network issues or rate limiting.

## [2.1.1] - 2026-02-21

### Fixed
-   **CI/CD**: Fixed `skip_wait` option in `daily_run.yml` workflow which was not correctly evaluating boolean inputs.

## [2.1.0] - 2026-02-19


### Changed
-   **Code Optimization**: Refactored `core.py` to remove duplicate code and legacy implementations, ensuring clean architecture using `ExchangeClient`.
-   **Quality Assurance**: Fixed critical bugs (missing imports, bare excepts) identified by linting.
-   **Testing**: Updated `test_basic.py` to test the clean `FirstFilingAnalyzer` using mocks, achieving full test coverage for core logic.
-   **Tooling**: Added `scripts/check.sh` for easy verification of linting and tests.

## [2.0.0] - 2026-02-19

### Added
-   **Multi-Exchange Support**: Added support for NSE Mainboard and NSE SME via `--exchange` flag.
-   **Modular Architecture**: Introduced `ExchangeClient` interface for extensibility.
-   **Enrichment**: Added lookback years to output metadata and refined enrichment logic.
-   **Output**: Standardized JSON output structure across exchanges with separate files.
-   **Usage**: Updated `README.md` with comprehensive usage examples.
-   Refactored CLI using `click` with structured JSON output.
-   Modularized codebase into `src/first_filings/` package.
-   Implemented exponential backoff with 15 retries using `tenacity`.
-   Silent execution with file logging (`first_filings.log`).
-   Results archival to `first_filings_archive.json`.
-   Updated `README.md` and documentation.

## [1.0.0] - 2026-01-26

### Added
-   Standardized project structure using `standardize-legacy-project` skill.
-   Initialized `uv` for dependency management.
-   Added `.context` documentation (`OVERVIEW`, `ARCHITECTURE`, `DESIGN`, `CHANGELOG`).
-   Configured linting and testing tooling (`ruff`, `pytest`).

### Fixed
-   Fixed `.gitignore` to include standard Python ignored files.
