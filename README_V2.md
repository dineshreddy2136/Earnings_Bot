# 📈 Earnings Bot Dashboard - Version 2.0

A comprehensive Python application with a **Streamlit web interface** that fetches upcoming earnings data for companies using the yfinance API and stores the data in a SQLite database for easy viewing and analysis.

## ✨ What's New in Version 2.0

### 🎯 Advanced Volatility Analysis
- **IV Rank (52-week)** - Industry-standard volatility ranking
- **IV Percentile** - Where current IV stands vs. historical range
- **Professional-grade metrics** used by institutional traders
- **Visual analysis tools** with quadrant charts

### 📅 Economic Calendar
- Track **FOMC meetings**, **CPI reports**, and other major economic events
- See market-wide volatility drivers alongside earnings
- Impact level indicators (High/Medium/Low)
- Educational content about each economic indicator

### ⚙️ Better Configuration Management
- Centralized `config.yaml` for easy customization
- No more hardcoded values in source code
- Simple to modify settings without touching code

### 📦 Proper Dependency Management
- Complete `requirements.txt` file
- Easy environment setup
- Version-controlled dependencies

---

## ✨ Core Features

### 🖥️ **Streamlit Web Dashboard**
- **Weekly Earnings Calendar** - View earnings by day with timing (BMO/AMC)
- **All Tickers View** - Master table with filtering and sorting
- **Options IV Analysis** - Professional volatility analysis tools
- **Economic Calendar** - Major market-moving events
- **Analytics Dashboard** - Visualizations and insights
- **Data Sync** - Fetch latest data with progress tracking
- **CSV Export** - Download data for offline analysis

### 📊 **Advanced Options Analysis**
- **Implied Volatility (IV)** tracking and analysis
- **Expected Move** calculations from option straddles
- **IV Rank** - 52-week volatility ranking
- **IV Percentile** - Historical volatility context
- **IV Crush** estimation post-earnings
- **Visual charts** with quadrant analysis
- **Trading insights** based on volatility levels

### 🗓️ **Economic Calendar Integration**
- **FOMC Meetings** - Federal Reserve decisions
- **CPI Reports** - Inflation data
- **Unemployment Data** - Job market health
- **GDP Reports** - Economic growth
- **Retail Sales** - Consumer spending
- Organized by date, category, and impact level

### 📈 **Company Information**
- Company name, sector, and industry
- Market capitalization and current stock price
- Earnings dates and timing (Before/After Market)
- EPS and Revenue estimates
- Historical performance tracking

---

## 🚀 Quick Start

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Earnings_Bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your settings** (optional)
   - Edit `config.yaml` to customize tickers, thresholds, etc.

4. **Add your ticker symbols**
   - Edit `a.json` with the stocks you want to track

### Launch the Dashboard

**Using Streamlit:**
```bash
streamlit run streamlit_app.py
```

The dashboard will automatically open in your web browser at `http://localhost:8501`

---

## 📱 Dashboard Pages

### 📅 **Weekly Earnings Calendar**
- View earnings organized by day of the week
- See timing (Before Market Open / After Market Close)
- Quick metrics: EPS estimate, revenue estimate, sector
- Week navigation (previous/current/future weeks)
- Summary statistics for the week

### 📊 **All Tickers Data**
- Complete list of all tracked tickers
- Filter by sector
- Sort by symbol, date, market cap, etc.
- Download as CSV
- Shows sync status and missing data

### 🔄 **Sync Data**
- **Full Sync** - Process all tickers from `a.json`
- **Quick Sync** - Process top 20 major companies
- Real-time progress tracking
- Success/failure reporting
- Database statistics

### 📈 **Analytics**
- Total companies and upcoming earnings count
- Sector distribution charts
- Market cap distribution
- Company search functionality
- Visual insights

### 📊 **Options IV Analysis** ⭐ NEW FEATURES
- **IV Rank & Percentile** - Professional volatility metrics
- Filter by IV, expected move, sector, price
- Time range selection (This Week, Next 7/14/30 Days)
- **Charts:**
  - IV Rank vs IV Percentile (quadrant analysis)
  - Expected Move vs Stock Price
  - Top 10 Biggest Movers
- Trading insights based on volatility levels
- Detailed metrics: Call/Put IV, Historical Vol, Expected Move ranges

### 📅 **Economic Calendar** ⭐ NEW
- View upcoming major economic events
- Filter by time range
- Organized by category and date
- Impact level indicators
- Educational content about each event type
- Metrics: Total events, high-impact count, FOMC/CPI counts

---

## ⚙️ Configuration

Edit `config.yaml` to customize:

```yaml
sync:
  major_tickers:  # Quick sync ticker list
    - AAPL
    - MSFT
    # ... add your favorites
  max_workers: 10  # Parallel processing threads

options:
  high_iv_threshold: 50.0  # IV threshold for "high volatility"
  iv_history_days: 252  # Trading days for IV calculations

economic_calendar:
  lookback_days: 30
  lookahead_days: 60
```

---

## 💻 Programmatic Usage

```python
from earnings_bot import EarningsBot
from database import EarningsDatabase

# Create instances
bot = EarningsBot()
db = EarningsDatabase()

# Fetch earnings data
earnings_data = bot.fetch_weekly_earnings()

# Get options IV data
iv_data = bot.get_options_iv_data('AAPL')
print(f"IV Rank: {iv_data['iv_rank_52week']}%")
print(f"IV Percentile: {iv_data['iv_percentile']}%")

# Query database
upcoming = db.get_upcoming_earnings(30)  # Next 30 days
weekly = db.get_earnings_by_week('2025-10-27', '2025-11-02')
```

---

## 📊 Understanding IV Rank & IV Percentile

### IV Rank (52-week)
- **Formula:** `(Current IV - 52-week Low) / (52-week High - 52-week Low) × 100`
- **0%** = IV at lowest point of the year
- **50%** = IV in middle of range
- **100%** = IV at highest point of the year

### IV Percentile
- Shows what % of days had IV below current level
- **95th percentile** = Current IV higher than 95% of past year
- **50th percentile** = Current IV at median
- **5th percentile** = Current IV lower than 95% of past year

### Trading Insights
- **High IV Rank/Percentile (>75%)** → Volatility expensive → Consider selling premium
- **Low IV Rank/Percentile (<25%)** → Volatility cheap → Consider buying premium
- **Mid-range (25-75%)** → Normal volatility levels

---

## 📁 Project Structure

```
Earnings_Bot/
├── streamlit_app.py           # Main application entry point
├── earnings_bot.py            # Core data fetching logic
├── database.py                # Database operations
├── config.yaml                # Configuration file
├── requirements.txt           # Python dependencies
├── a.json                     # Your ticker symbols
├── pages/                     # Streamlit pages
│   ├── weekly_calendar.py     # Weekly earnings view
│   ├── all_tickers.py         # All tickers table
│   ├── sync_page.py           # Data synchronization
│   ├── analytics_page.py      # Analytics and charts
│   ├── options_iv.py          # Options IV analysis
│   └── economic_calendar.py   # Economic events
├── components/                # Reusable components
│   └── options_sync.py        # Options sync component
└── utils/                     # Utility functions
    ├── data_access.py         # Database queries (cached)
    ├── date_helpers.py        # Date utilities
    ├── formatters.py          # Display formatters
    └── config_loader.py       # Configuration loader
```

---

## 📦 Dependencies

- **streamlit** - Web interface framework
- **pandas** - Data manipulation
- **numpy** - Numerical computing
- **yfinance** - Yahoo Finance API
- **plotly** - Interactive charts
- **beautifulsoup4** - Web scraping
- **requests** - HTTP library
- **pyyaml** - Configuration files
- **pytz** - Timezone support

Install all at once:
```bash
pip install -r requirements.txt
```

---

## 🎯 Use Cases

### For Day Traders
- Track weekly earnings calendar
- See BMO (Before Market Open) vs AMC (After Market Close) timing
- Plan your trading week

### For Options Traders
- Analyze IV Rank before earnings
- Calculate expected moves
- Identify expensive vs cheap volatility
- Plan straddle/strangle strategies
- Estimate IV crush impact

### For Swing Traders
- Track earnings dates to avoid/target
- Monitor sector concentration
- Identify high-volatility opportunities

### For All Traders
- Stay aware of major economic events (FOMC, CPI)
- Combine earnings + macro calendar
- Better risk management

---

## 🔧 Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt
```

### Config not loading
- Ensure `config.yaml` exists in root directory
- Check YAML syntax (indentation matters!)

### Database errors
- Delete `earnings.db` and re-sync data
- Database schema auto-migrates on startup

### Slow data fetching
- Reduce `max_workers` in config.yaml
- Use Quick Sync instead of Full Sync for testing

---

## 🚀 Future Enhancements

Potential additions:
- Live economic calendar API integration
- Historical earnings performance tracking
- Watchlist and alert system
- What-if scenario calculator
- PDF report generation
- Trade journal integration

---

## 📄 License

MIT License - feel free to use and modify for your own purposes.

---

## 🤝 Contributing

Contributions are welcome! Areas to improve:
- Additional data sources
- More chart types
- Enhanced filtering options
- Mobile-responsive design
- API integrations

---

## ⚠️ Disclaimer

This tool is for informational purposes only. Not financial advice. Always do your own research before trading.

---

## 📚 Documentation

- **FEATURE_IMPLEMENTATION_SUMMARY.md** - Detailed feature documentation
- **CODE_STRUCTURE.md** - Architecture and code organization
- **TICKER_GUIDE.md** - How to manage your ticker list

---

*Last Updated: October 30, 2025*  
*Version 2.0 - Now with Advanced IV Analysis & Economic Calendar*
