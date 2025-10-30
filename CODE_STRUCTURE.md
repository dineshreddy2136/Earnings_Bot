# Earnings Dashboard - Code Structure

## Overview
The Earnings Dashboard has been refactored into a modular architecture for better maintainability and scalability.

## Directory Structure

```
Earnings_Bot/
├── streamlit_app.py          # Main application entry point (120 lines)
├── database.py                # Database operations
├── earnings_bot.py            # Data fetching from yfinance
│
├── pages/                     # Page modules
│   ├── __init__.py
│   ├── weekly_calendar.py    # Weekly Earnings Calendar page
│   ├── all_tickers.py         # All Tickers Data page
│   ├── sync_page.py           # Data Synchronization page
│   ├── analytics_page.py      # Analytics & Insights page
│   └── options_iv.py          # Options IV Analysis page
│
├── utils/                     # Utility functions
│   ├── __init__.py
│   ├── data_access.py         # Database access with caching
│   ├── formatters.py          # Display formatting utilities
│   └── date_helpers.py        # Date/time utilities
│
├── components/                # Reusable UI components
│   ├── __init__.py
│   └── options_sync.py        # Options data sync component
│
└── streamlit_app_backup.py    # Original monolithic file (for reference)
```

## Module Descriptions

### Main Application (`streamlit_app.py`)
- Entry point for the application
- Handles page routing and navigation
- Configures sidebar controls
- **Lines: ~120** (down from ~900)

### Pages Module (`pages/`)
Each page is a self-contained module with its own logic and UI:

- **`weekly_calendar.py`**: Displays earnings grouped by day of week
- **`all_tickers.py`**: Shows comprehensive ticker data from database
- **`sync_page.py`**: Handles data synchronization with yfinance
- **`analytics_page.py`**: Provides data analysis and visualizations
- **`options_iv.py`**: Options IV analysis and expected move calculations

### Utils Module (`utils/`)
Reusable utility functions:

- **`data_access.py`**: Cached database queries
- **`formatters.py`**: Display formatting (market cap, revenue, etc.)
- **`date_helpers.py`**: Date calculation and formatting helpers

### Components Module (`components/`)
Reusable UI components:

- **`options_sync.py`**: Options data synchronization workflow

## Benefits of This Structure

1. **Maintainability**: Each module has a single responsibility
2. **Readability**: Smaller files are easier to understand
3. **Reusability**: Common functions are extracted and can be reused
4. **Testability**: Individual modules can be tested independently
5. **Scalability**: Easy to add new pages or features
6. **Collaboration**: Multiple developers can work on different modules

## Adding a New Page

1. Create a new file in `pages/` (e.g., `pages/new_feature.py`)
2. Define your page function:
   ```python
   import streamlit as st
   
   def new_feature():
       st.header("New Feature")
       # Your page logic here
   ```
3. Import and add to routing in `streamlit_app.py`:
   ```python
   from pages.new_feature import new_feature
   
   # In route_to_page():
   elif page == "🆕 New Feature":
       new_feature()
   ```

## Code Quality Improvements

- **Before**: 1 file, ~900 lines
- **After**: 15 files, average ~100 lines each
- **Main app**: Reduced from 900 to 120 lines (87% reduction)
- **Function complexity**: Broken down into focused, single-purpose functions

## Dependencies Between Modules

```
streamlit_app.py
    ├── pages/*           (imports all page modules)
    ├── utils/*           (used by pages)
    └── components/*      (used by pages)

pages/*
    ├── utils.data_access
    ├── utils.formatters
    ├── utils.date_helpers
    └── components.*

components/*
    ├── utils.data_access
    └── earnings_bot
```

## Migration Notes

- The original `streamlit_app.py` has been backed up as `streamlit_app_backup.py`
- All functionality has been preserved
- No changes to database schema or external dependencies
- Timestamps are now handled in EST as requested

## Future Improvements

Consider adding:
- Unit tests for utility functions
- Integration tests for page modules
- Configuration file for app settings
- Logging module for better debugging
- Error handling middleware
