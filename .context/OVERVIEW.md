# Project Overview

## Purpose
`FirstFilingsBSE` is a tool designed to identify and alert on the "first filing" of specific types (like Analyst Calls, Press Releases, Presentations) for companies listed on the BSE (Bombay Stock Exchange). It helps investors spot new developments that might indicate a change in company communication or strategy.

## Core Features
1.  **Announcement Fetching**: Scrapes/fetches announcements from BSE for specified categories.
2.  **First Filing Detection**: Checks if a specific filing type is the first one in a configurable lookback period (default 15 years).
3.  **Filering**: Filters by subcategories like "Analyst / Investor Meet", "Press Release", "Investor Presentation".
4.  **CLI Interface**: specific date ranges (WTD, MTD, QTD) via command line arguments.

## Technology Stack
-   **Python**: Core logic.
-   **bse**: Third-party library for interacting with BSE data.
-   **uv**: Dependency management.
