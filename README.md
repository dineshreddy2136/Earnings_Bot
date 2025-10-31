# � Earnings Bot - Professional Earnings Intelligence Platform

A comprehensive **Streamlit-based** earnings tracking and analysis platform with advanced volatility metrics, options analysis, and email alerts. Track company earnings, analyze IV Rank/Percentile, and receive earnings reports directly in your inbox.

## ✨ Key Features

### � **Earnings Calendar**
- **Weekly Calendar View** - Navigate through weeks to see upcoming earnings
- **Time-based Filtering** - BMO (Before Market Open) and AMC (After Market Close)
- **Company Details** - Sector, price, EPS estimates, and more
- **Quick Navigation** - Previous/Next week buttons, return to current week

### 📊 **Options IV Analysis**  
- **IV Rank (52-week)** - Percentile ranking of current IV vs 52-week range
- **IV Percentile** - Percentage of days IV was below current level
- **Expected Move** - Options-implied price movement prediction
- **Visual Charts** - IV Rank vs Percentile quadrant analysis
- **Color-coded Indicators** - Instant visual classification (High/Medium/Low)

### 📧 **Email Alerts**
- **Automated Reports** - Send earnings summaries via email
- **Flexible Scheduling** - Tomorrow, This Week, Next Week, or Custom ranges
- **Rich HTML Format** - Professional gradient design with color-coded metrics
- **Plain Text Option** - Clean table format for all email clients
- **Multiple Recipients** - Send to unlimited recipients
- **Secure Credentials** - Email config stored in `.env` file (never committed)

### � **Data Synchronization**
- **Major Tickers** - Quick sync for top companies (AAPL, MSFT, GOOGL, etc.)
- **All Tickers** - Comprehensive sync from ticker list
- **Parallel Processing** - Multi-threaded data fetching
- **Progress Tracking** - Real-time sync status and completion metrics
- **Auto-retry** - Intelligent retry logic for failed requests

### 📈 **All Tickers View**
- **Complete Database** - View all earnings records
- **Advanced Filtering** - By date, sector, price range
- **Search** - Quick symbol and company name search
- **Export** - Download filtered data as CSV
- **Sorting** - Multi-column sorting capabilities

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/dineshreddy2136/Earnings_Bot.git
cd Earnings_Bot

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Email Setup (Optional)

For email alerts functionality:

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use any text editor
```

See [EMAIL_SETUP.md](EMAIL_SETUP.md) for detailed email configuration instructions.

### 3. Launch Application

```bash
streamlit run streamlit_app.py
```

The dashboard will open at `http://localhost:8501`

## 📱 Dashboard Navigation

### 📅 Weekly Earnings Calendar
- View earnings for current week
- Navigate between weeks
- See company details inline
- Filter by time (BMO/AMC)

### � All Tickers Data  
- Browse complete earnings database
- Filter by date range and sector
- Search by symbol or company name
- Export filtered results

### 🔄 Sync Data
- **Major Tickers Sync** - Quick sync for top 20 companies
- **All Tickers Sync** - Full database sync
- Real-time progress tracking
- Sync statistics and error reporting

### 📊 Options IV Analysis
- View IV Rank and IV Percentile for all stocks
- Expected move calculations
- IV Rank vs Percentile quadrant chart
- Filter by IV levels
- Educational content on IV metrics

### � Email Alerts
- Select time period (Tomorrow/This Week/Next Week)
- Preview companies before sending
- Choose HTML or Plain Text format
- Include/exclude options IV data
- Send to multiple recipients

## 🔧 Configuration

### config.yaml

Main configuration file for the application:

```yaml
# Major tickers for quick sync
sync:
  major_tickers:
    - AAPL
    - MSFT
    - GOOGL
    # ... add more

# Options analysis settings
options:
  high_iv_threshold: 50.0
  max_days_to_expiration: 60
  iv_history_days: 252  # ~1 year

# Email settings (use .env for credentials)
email:
  use_env_file: true
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
```

### .env File (Email Credentials)

**Never commit this file to git!**

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_16_char_app_password
RECIPIENT_EMAILS=recipient1@example.com,recipient2@example.com
```

## 📊 Data Structure

### Database Schema

**earnings table:**
- symbol, company_name, earnings_date, earnings_time
- sector, industry, market_cap, current_price
- eps_estimate, revenue_estimate
- last_updated

**options_data table:**
- symbol, earnings_date, current_price
- iv_rank_52week, iv_percentile
- iv_52week_high, iv_52week_low
- expected_move_percent, expected_move_up, expected_move_down
- last_updated

## 🎨 Email Templates

### HTML Email Features
- Dark gradient header
- Stats bar with key metrics
- Card-based company rows
- Color-coded IV Rank badges (High/Medium/Low)
- BMO/AMC time badges
- Responsive mobile design
- Professional footer

### Plain Text Email Features
- Clean table format
- Pipe-separated columns
- IV status indicators
- Aligned data presentation
- Universal compatibility

## 🔐 Security

### Credentials Management
- ✅ Email credentials in `.env` file
- ✅ `.env` automatically in `.gitignore`
- ✅ Template file (`.env.example`) for setup
- ✅ No hardcoded secrets in code
- ✅ Secure SMTP with TLS

### Best Practices
- Use App Passwords (not regular passwords)
- Keep `.env` file secure
- Never commit `.env` to repository
- Rotate credentials periodically

## 📚 Documentation

- **EMAIL_SETUP.md** - Complete email configuration guide
- **requirements.txt** - Python dependencies
- **.env.example** - Email configuration template

## 🛠️ Technical Stack

### Backend
- **Python 3.7+** - Core language
- **yfinance** - Financial data API
- **SQLite** - Local database
- **pandas** - Data manipulation
- **numpy** - Numerical calculations

### Frontend
- **Streamlit** - Web framework
- **Plotly** - Interactive charts
- **Custom CSS** - Enhanced styling

### Email
- **SMTP/TLS** - Secure email delivery
- **MIME** - Multi-part email support
- **HTML/Text** - Dual format emails

## 📈 IV Metrics Explained

### IV Rank (52-week)
Percentile ranking of current IV compared to 52-week range:
- **Formula**: `(Current IV - 52w Low) / (52w High - 52w Low) × 100`
- **High (>75%)**: Current IV in top quartile - volatility expensive
- **Medium (50-75%)**: Current IV above median
- **Low (<50%)**: Current IV below median - volatility cheap

### IV Percentile
Percentage of days over past year where IV was below current level:
- **High Percentile**: Current IV higher than most historical days
- **Low Percentile**: Current IV lower than most historical days

### Expected Move
Options market's prediction of stock price movement through earnings:
- Calculated from at-the-money option prices
- Represents ±1 standard deviation move
- Includes specific price targets (high/low)

## 🤝 Contributing

Feel free to:
- Report bugs or issues
- Suggest new features
- Submit pull requests
- Improve documentation

## 📄 License

MIT License - Feel free to use and modify as needed.

## ⚠️ Disclaimer

This tool is for informational purposes only and does not constitute financial advice. All data is sourced from public markets and may contain inaccuracies. Always conduct your own research and consult with a qualified financial advisor before making investment decisions.

## 📞 Support

For issues or questions:
1. Check existing documentation
2. Review configuration files
3. Verify email setup (if using alerts)
4. Check application logs

---

**Built with ❤️ for traders and investors**

*Last Updated: October 2025*