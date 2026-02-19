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
  Number of years to look back for history. Defaults to 2 (configurable).

- `-a, --analyst-calls`
  Fetch Analyst Call Intimations only.

- `-p, --press-releases`
  Fetch Press Releases only.

- `-t, --presentations`
  Fetch Investor Presentations (PPT) only.

*Note: If no category flags (`-a`, `-p`, `-t`) are provided, ALL categories are fetched by default.*

### Output

The CLI prints a minimal JSON summary to `stdout` containing the path to the full output file.

**CLI Output Example:**
```json
{
  "status": "success",
  "generated_at": "2024-06-18T10:30:00",
  "total_filings_found": 12,
  "failed_checks_count": 0,
  "output_file": "first_filings_output.json"
}
```

**Full Output File (`first_filings_output.json`):**
The detailed data is saved to a JSON file structured by Category -> Date. This format is optimized for size and structure.

```json
{
  "meta": {
    "generated_at": "...",
    "columns": ["scrip_code", "company_name", "price_announcement", "current_price", "current_mkt_cap_cr"],
    "failed_checks_count": 0
  },
  "data": {
    "Analyst Call Intimation": {
      "2024-06-07": [
        ["500325", "Reliance Industries Ltd", 2950.50, 2980.00, 1950000],
        ...
      ]
    }
  }
}
```
*Note: Market Cap is in Crores.*

## Requirements

- Python 3.12+
- `bse`
- `click`
- `tenacity`
- `yfinance`

## License

See [LICENSE](LICENSE).
