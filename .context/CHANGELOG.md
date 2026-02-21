
# Changelog

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
