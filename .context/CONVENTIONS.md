# Coding Conventions

## Code Style
- **Standard**: Follow [PEP 8](https://peps.python.org/pep-0008/) guidelines.
- **Linting**: Use `ruff` for linting and formatting. Ensure code passes checks with `ruff check .` and `ruff format .`.
- **Imports**: Organize imports with standard library first, followed by third-party, then local imports. `ruff` handles this automatically.

## Type Hinting
- **Usage**: Use type hints for all function arguments and return values.
- **Example**:
  ```python
  from typing import List, Optional

  def fetch_data(scrip_code: str) -> Optional[List[dict]]:
      ...
  ```

## Docstrings
- **Requirement**: Public functions and classes must have docstrings.
- **Style**: Google style or similar, providing a brief description, arguments (Args), and return values (Returns).

## Logging
- **Module**: Use the standard `logging` module.
- **Setup**: Logging is configured in `src/first_filings/utils.py`.
- **Usage**: Instantiate a logger at the module level:
  ```python
  import logging
  logger = logging.getLogger(__name__)
  ```
- **Output**: Logs are written to `first_filings.log`.

## Error Handling
- **Pattern**: Use `try-except` blocks to catch expected exceptions.
- **Logging**: Log errors with `logger.error(f"Message: {e}")` or `logger.exception("Message")` for stack traces.
- **Resilience**: Use `tenacity` for retrying transient network errors (see `src/first_filings/retries.py`).

## Project Structure
- **Layout**: `src/` layout.
- **Entry Point**: `src/first_filings/cli.py`.
- **Core Logic**: `src/first_filings/core.py`.
- **Interfaces**: `src/first_filings/exchange.py`.

## Testing
- **Framework**: Use `pytest` for unit testing.
- **Location**: Tests are located in `tests/`.

## Dependency Management
- **Tool**: Use `uv` for package management.
- **File**: `pyproject.toml` defines dependencies.
