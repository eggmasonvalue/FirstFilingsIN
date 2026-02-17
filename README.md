# FirstFilings
A script to fetch and analyze BSE corporate announcements, identifying first-time filings for each company in a given subcategory in the given lookback period.

## Value Proposition
The first investor presentation, analyst or earnings call intimation or media release often signifies the start of the market's discovery of the company or the promoter's interest in value creation via market capitalisation increase, often leading to rapid rerating.

## Installation

This project uses `uv` for dependency management.

1. Install `uv` if not already installed (see [uv docs](https://github.com/astral-sh/uv)).

2. Sync dependencies:
   ```bash
   uv sync
   ```

3. Install the package (optional but recommended):
   ```bash
   uv pip install -e .
   ```

## Usage

### Command Line Interface

Run the tool using `uv run`:

```bash
uv run first-filings [OPTIONS]
```

### Options

- `--date DATE`
  Reference date (DD-MM-YYYY or YYYY-MM-DD). Defaults to today.

- `--period [day|wtd|mtd|qtd]`
  Fetch period:
  - `day`: Single day (default).
  - `wtd`: Week-to-date (Monday to reference date).
  - `mtd`: Month-to-date (1st of month to reference date).
  - `qtd`: Quarter-to-date (1st of quarter to reference date).

- `--lookback-years INTEGER`
  Number of years to look back for history. Defaults to 15.

### Examples

- Filings for a single day (07-06-2024):
  ```bash
  uv run first-filings --date 07-06-2024
  ```

- Filings for week-to-date ending 07-06-2024:
  ```bash
  uv run first-filings --date 07-06-2024 --period wtd
  ```

- Filings for month-to-date ending 07-06-2024:
  ```bash
  uv run first-filings --date 07-06-2024 --period mtd
  ```

- Filings for quarter-to-date ending 07-06-2024:
  ```bash
  uv run first-filings --date 07-06-2024 --period qtd
  ```

- Specify lookback period (in years):
  ```bash
  uv run first-filings --date 07-06-2024 --lookback-years 10
  ```

### Output

The output is provided as a structured JSON object printed to stdout.
Silent execution is enforced; all logs are written to `first_filings.log`.
The result is also appended to `first_filings_archive.json`.

Example Output:
```json
{
  "status": "success",
  "reference_date": "2024-06-07",
  "period": "day",
  "lookback_years": 15,
  "filings": {
    "Press Release": ["Company A", "Company B"],
    "PPT": []
  },
  "errors": []
}
```

## Requirements

- Python 3.12+
- `bse`
- `click`
- `tenacity`

## License

See [LICENSE](LICENSE).
