# Project Overview

## Purpose
`FirstFilings` is a tool designed to identify and alert on the **first time** a company makes a specific type of announcement (e.g., Analyst Call Intimation, Press Release, Investor Presentation) within a lookback period.

This signal often indicates a company's increasing focus on investor relations and market communication.

## Core Features
1.  **Multi-Exchange Support**:
    - **BSE (Bombay Stock Exchange)**: Fetches announcements using `bse` library.
    - **NSE (National Stock Exchange)**: Fetches Mainboard ("equities") and SME ("sme") announcements using `nse` library.
2.  **Announcement Fetching**: Retrieves corporate announcements for a configurable date range (Day, WTD, MTD, QTD) and specific categories.
3.  **First Filing Logic**: Checks historical data (e.g., last 2 years) to determine if the current announcement is the first occurrence of that type for the stock.
4.  **Data Enrichment**:
    - **Symbol Resolution**: Maps Scrip Codes to Symbols (BSE) or uses NSE Symbols.
    - **Market Data**: Adds Current Price, Price at Announcement, and Market Cap using `yfinance`.
5.  **Output**: Generates structured JSON files per exchange (e.g., `bse_output.json`, `nse_sme_output.json`).

## Tech Stack
-   **Python 3.12+**: Core language.
-   **Dependencies**:
    -   `click`: CLI interface.
    -   `yfinance`: Market data.
    -   `tenacity`: Robust retry logic.
    -   `bse`: BSE data fetching.
    -   `nse`: NSE data fetching (Local/PyPI).
-   **Tooling**: `uv` (Package Management), `pytest` (Testing), `ruff` (Linting).
