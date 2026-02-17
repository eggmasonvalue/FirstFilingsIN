# Changelog

## [2.0.0] - 2026-05-29

### Added
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
