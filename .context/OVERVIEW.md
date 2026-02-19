# Project Overview

## Purpose
`FirstFilings` is a tool designed to identify and alert on the "first filing" of specific types (like Analyst Calls, Press Releases, Presentations) for companies listed on the BSE (Bombay Stock Exchange). It helps investors spot new developments that might indicate a change in company communication or strategy.

## Core Features
1.  **Announcement Fetching**: Scrapes/fetches announcements from BSE for specified categories.
2.  **First Filing Detection**: Checks if a specific filing type is the first one in a configurable lookback period (default 15 years).
3.  **Data Enrichment**: Adds Symbol, Historical Price, and Current Market Cap (in Crores) using `yfinance`.
4.  **CLI Interface**: Standardized CLI with options for date, period, and lookback years.
5.  **Output**: Detailed JSON saved to disk, minimal summary printed to stdout.

## Technology Stack
-   **Python**: Core logic (3.12+).
-   **click**: Command Line Interface.
-   **tenacity**: Retry logic with exponential backoff.
-   **bse**: Third-party library for interacting with BSE data.
-   **yfinance**: For fetching market data (Price, Market Cap).
