# Changelog

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
