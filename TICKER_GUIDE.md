# 📊 How to Update Your Tickers (a.json)

## 🎯 Easy Maintenance Guide

Your `a.json` file is now organized by categories for easy management!

## 📁 Current Structure

```json
{
  "metadata": {
    "description": "Custom ticker symbols for earnings tracking",
    "last_updated": "2025-10-30",
    "total_count": 295
  },
  "tickers": {
    "mega_cap": [...],      // Top 10 largest companies
    "tech": [...],          // Technology stocks
    "finance": [...],       // Banks and financial services
    "healthcare": [...],    // Healthcare and pharma
    "energy": [...],        // Energy and oil companies
    "consumer": [...],      // Consumer goods and retail
    "industrials": [...],   // Industrial companies
    "etfs": [...],          // Exchange-traded funds
    "crypto_related": [...], // Crypto mining/exchange stocks
    "growth_stocks": [...], // High-growth stocks
    "speculative": [...]    // Speculative/meme stocks
  }
}
```

## ✏️ How to Add New Tickers

### Option 1: Add to Existing Category
1. Open `a.json` in VS Code
2. Find the appropriate category (e.g., "tech", "finance", etc.)
3. Add your ticker to the array: `"NEWTICKER"`
4. Save the file

**Example - Adding SNOWFLAKE to tech:**
```json
"tech": [
  "AMD", "INTC", "NFLX", "ADBE", "CRM", "ORCL",
  "SNOW"  // ← Add here
]
```

### Option 2: Create New Category
```json
"my_custom_stocks": [
  "TICKER1", "TICKER2", "TICKER3"
]
```

## 🔄 Update Metadata
Don't forget to update the metadata when you make changes:
```json
"metadata": {
  "last_updated": "2025-10-30",  // ← Update this date
  "total_count": 300             // ← Update count if needed
}
```

## ✅ Best Practices

1. **Use uppercase** for all ticker symbols
2. **Group logically** - put similar stocks in the same category
3. **Avoid duplicates** - the system will automatically remove them
4. **Update metadata** - keep track of your changes
5. **Test after changes** - restart the app to see your new tickers

## 🎯 Categories Explained

- **mega_cap**: Largest companies by market cap (AAPL, MSFT, etc.)
- **tech**: Technology and software companies
- **finance**: Banks, payment processors, financial services
- **healthcare**: Healthcare, pharmaceuticals, medical devices
- **energy**: Oil, gas, renewable energy, utilities
- **consumer**: Retail, restaurants, consumer goods
- **industrials**: Manufacturing, aerospace, industrial equipment
- **etfs**: Exchange-traded funds (SPY, QQQ, etc.)
- **crypto_related**: Bitcoin miners, crypto exchanges
- **growth_stocks**: High-growth, emerging companies
- **speculative**: Meme stocks, highly volatile stocks

## 🚀 After Making Changes

1. Save the `a.json` file
2. The app will automatically reload your tickers
3. Go to "Sync Data" tab to fetch earnings for new tickers
4. Your new stocks will appear in "All Tickers Data"

That's it! Your organized ticker list makes it super easy to manage and update your stocks! 🎉