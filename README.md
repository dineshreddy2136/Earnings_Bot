# 📈 Earnings Bot Dashboard

A comprehensive Python application with a **Streamlit web interface** that fetches upcoming earnings data for companies using the yfinance API and stores the data in a SQLite database for easy viewing and analysis.

## ✨ Features

### 🖥️ **Streamlit Web Dashboard**
- **Interactive Dashboard** - Beautiful web interface for viewing earnings data
- **Real-time Data Fetching** - Fetch latest earnings with progress tracking
- **Advanced Filtering** - Filter by date range, sector, and company
- **Search Functionality** - Search by ticker symbol or company name
- **Database Statistics** - View comprehensive database analytics
- **CSV Export** - Download filtered data as CSV files

### 📊 **Data Management**
- **SQLite Database** - Persistent storage of earnings data
- **Custom Ticker Lists** - Load your own ticker symbols from JSON file
- **Multiple Data Sources** - Earnings dates, EPS estimates, company info
- **Automatic Updates** - Insert/update earnings records automatically

### 📈 **Company Information**
- Company name, sector, and industry
- Market capitalization and current stock price
- Earnings dates and EPS estimates
- Analyst recommendations (when available)

## 🚀 Quick Start

### Installation

1. **Clone or download** this repository
2. **Install dependencies**:
   ```bash
   pip install yfinance pandas requests beautifulsoup4 python-dateutil streamlit plotly
   ```

### Launch the Dashboard

**Option 1: Using the launch script**
```bash
python launch.py
```

**Option 2: Direct streamlit command**
```bash
streamlit run streamlit_app.py
```

The dashboard will automatically open in your web browser at `http://localhost:8501`

### Adding Your Tickers

1. **Edit the `a.json` file** with your ticker symbols
2. **Use the "Fetch New Data" tab** in the dashboard to update the database
3. **View results** in the various dashboard tabs

## 📱 Dashboard Features

### 🏠 **Dashboard Tab**
- Overview metrics (total companies, earnings records, upcoming earnings)
- This week's earnings calendar
- Charts showing upcoming earnings distribution
- Top companies by market cap with upcoming earnings

### 🔄 **Fetch New Data Tab**
- Real-time progress tracking while fetching data
- Processes all tickers from your `a.json` file
- Updates database with latest information
- Shows summary of fetch results

### 📋 **View All Earnings Tab**
- Complete table of all earnings data
- Filter by date range and sector
- Sort by various criteria
- Download filtered data as CSV

### 🔍 **Search & Filter Tab**
- Search by company name or ticker symbol
- Quick filter buttons (this week's earnings, high market cap)
- Detailed company information in expandable cards

### 📊 **Database Stats Tab**
- Database overview and metrics
- Sector distribution pie chart
- Database management tools
- Storage information

## 💻 Command Line Usage (Optional)

You can still use the earnings bot from the command line:

```bash
python earnings_bot.py
```

### Programmatic Usage
```python
from earnings_bot import EarningsBot
from database import EarningsDatabase

# Create bot and database instances
bot = EarningsBot()
db = EarningsDatabase()

# Fetch earnings data
earnings_data = bot.fetch_weekly_earnings()

# Query database
upcoming_earnings = db.get_upcoming_earnings(30)  # Next 30 days
weekly_earnings = db.get_earnings_by_week('2025-10-27', '2025-11-02')
```

## Output Format

The script generates a JSON file with the following structure:

```json
{
  "week_start": "2024-01-15",
  "week_end": "2024-01-21",
  "total_companies_checked": 50,
  "companies_with_earnings_data": 25,
  "companies_with_earnings_this_week": 5,
  "last_updated": "2024-01-15 10:30:00",
  "earnings_data": [
    {
      "symbol": "AAPL",
      "company_name": "Apple Inc.",
      "earnings_date": "2024-01-18",
      "sector": "Technology",
      "industry": "Consumer Electronics",
      "market_cap": 3000000000000,
      "current_price": 185.50,
      "eps_estimate": 2.11
    }
  ]
}
```

## Data Fields

- **symbol**: Stock ticker symbol (e.g., "AAPL")
- **company_name**: Full company name
- **earnings_date**: Date of earnings announcement (YYYY-MM-DD)
- **sector**: Industry sector
- **industry**: Specific industry within sector
- **market_cap**: Market capitalization in USD
- **current_price**: Current stock price
- **eps_estimate**: Earnings per share estimate (if available)

## Limitations

- Currently limited to S&P 500 companies (first 50 for performance)
- Depends on yfinance API availability
- Some earnings dates may not be available for all companies
- Rate limiting may apply for large numbers of requests

## Customization

You can modify the script to:
- Include different stock universes (not just S&P 500)
- Change the number of companies to check
- Add additional data fields from yfinance
- Implement different filtering criteria

## Error Handling

The script includes error handling for:
- Network connectivity issues
- Missing earnings data
- Invalid stock symbols
- File I/O errors

## Requirements

- Python 3.7+
- yfinance
- pandas
- requests
- beautifulsoup4
- python-dateutil

## License

MIT License