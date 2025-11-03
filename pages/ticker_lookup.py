"""Ticker Lookup Page - Check Expected Moves for Any Symbol"""
import streamlit as st
import pandas as pd
from datetime import datetime
from earnings_bot import EarningsBot
from database import EarningsDatabase
from utils.formatters import format_market_cap


def ticker_lookup():
    """Ticker lookup page - search any ticker for earnings and IV data"""
    st.header("🔍 Ticker Lookup")
    st.markdown("**Search any ticker symbol to get earnings date and options analysis**")
    
    # Initialize session state for ticker
    if 'search_ticker' not in st.session_state:
        st.session_state.search_ticker = ""
    if 'trigger_search' not in st.session_state:
        st.session_state.trigger_search = False
    
    # Initialize bot and database
    bot = EarningsBot()
    db = EarningsDatabase()
    
    # Input section
    col1, col2 = st.columns([3, 1])
    
    with col1:
        ticker_input = st.text_input(
            "Enter Ticker Symbol",
            value=st.session_state.search_ticker,
            placeholder="e.g., AAPL, TSLA, NVDA, GOOGL",
            help="Enter any valid stock ticker symbol",
            key="ticker_input_field"
        ).upper().strip()
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔎 Search", type="primary", use_container_width=True):
            st.session_state.search_ticker = ticker_input
            st.session_state.trigger_search = True
    
    # Quick examples
    st.markdown("**Quick Examples:**")
    example_cols = st.columns(6)
    example_tickers = ["AAPL", "TSLA", "NVDA", "AMZN", "GOOGL", "META"]
    
    for idx, ticker in enumerate(example_tickers):
        with example_cols[idx]:
            if st.button(ticker, use_container_width=True, key=f"example_{ticker}"):
                st.session_state.search_ticker = ticker
                st.session_state.trigger_search = True
                st.rerun()
    
    # Process search
    if st.session_state.trigger_search and st.session_state.search_ticker:
        ticker_to_search = st.session_state.search_ticker
        
        with st.spinner(f"🔄 Fetching data for {ticker_to_search}..."):
            # Fetch earnings data
            earnings_info = bot.get_earnings_for_symbol(ticker_to_search)
            
            if not earnings_info:
                st.error(f"❌ Could not find data for ticker: {ticker_to_search}")
                st.info("💡 Make sure the ticker symbol is valid and listed on a major exchange.")
                st.session_state.trigger_search = False
                return
            
            # Display company information
            st.markdown("---")
            st.subheader(f"📊 {earnings_info['company_name']} ({ticker_to_search})")
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Current Price",
                    f"${earnings_info['current_price']:.2f}" if earnings_info['current_price'] != 'N/A' else 'N/A'
                )
            
            with col2:
                st.metric(
                    "Earnings Date",
                    earnings_info['earnings_date'] if earnings_info['earnings_date'] != 'N/A' else 'Not Available'
                )
            
            with col3:
                st.metric(
                    "Earnings Time",
                    earnings_info.get('earnings_time', 'N/A')
                )
            
            with col4:
                st.metric(
                    "Market Cap",
                    format_market_cap(earnings_info['market_cap']) if earnings_info['market_cap'] != 'N/A' else 'N/A'
                )
            
            # Company details
            with st.expander("📋 Company Details", expanded=True):
                details_col1, details_col2 = st.columns(2)
                
                with details_col1:
                    st.write(f"**Sector:** {earnings_info.get('sector', 'N/A')}")
                    st.write(f"**Industry:** {earnings_info.get('industry', 'N/A')}")
                
                with details_col2:
                    st.write(f"**EPS Estimate:** ${earnings_info['eps_estimate']:.2f}" if earnings_info['eps_estimate'] != 'N/A' else "**EPS Estimate:** N/A")
                    st.write(f"**Revenue Estimate:** {earnings_info['revenue_estimate']}" if earnings_info['revenue_estimate'] != 'N/A' else "**Revenue Estimate:** N/A")
            
            # Fetch options IV data
            st.markdown("---")
            st.subheader("📈 Options Analysis & Expected Move")
            
            with st.spinner("🔄 Calculating implied volatility and expected moves..."):
                iv_data = bot.get_options_iv_data(ticker_input)
                
                if not iv_data:
                    st.warning(f"⚠️ No options data available for {ticker_input}")
                    st.info("This could mean:")
                    st.markdown("""
                    - The stock doesn't have listed options
                    - Options data is not available from the data provider
                    - The ticker might be an ETF, index, or foreign stock without US options
                    """)
                    return
                
                # Display IV metrics
                st.markdown("### 🎯 Expected Move Through Earnings")
                
                move_col1, move_col2, move_col3, move_col4 = st.columns(4)
                
                with move_col1:
                    st.metric(
                        "Expected Move %",
                        f"±{iv_data['expected_move_percent']:.2f}%",
                        help="Options market's prediction of stock movement through earnings"
                    )
                
                with move_col2:
                    st.metric(
                        "Expected Move $",
                        f"±${iv_data['expected_move_dollar']:.2f}",
                        help="Dollar amount of expected price movement"
                    )
                
                with move_col3:
                    st.metric(
                        "Upside Target",
                        f"${iv_data['expected_move_up']:.2f}",
                        delta=f"+${iv_data['expected_move_dollar']:.2f}",
                        help="Upper range of expected move"
                    )
                
                with move_col4:
                    st.metric(
                        "Downside Target",
                        f"${iv_data['expected_move_down']:.2f}",
                        delta=f"-${iv_data['expected_move_dollar']:.2f}",
                        delta_color="inverse",
                        help="Lower range of expected move"
                    )
                
                # IV Rank and Percentile
                st.markdown("### 📊 Implied Volatility Analysis")
                
                iv_col1, iv_col2, iv_col3, iv_col4 = st.columns(4)
                
                with iv_col1:
                    current_iv = iv_data['implied_volatility']
                    st.metric(
                        "Current IV",
                        f"{current_iv:.2f}%",
                        help="Average of call and put implied volatility"
                    )
                
                with iv_col2:
                    iv_rank = iv_data.get('iv_rank_52week')
                    if iv_rank is not None:
                        st.metric(
                            "IV Rank (52-week)",
                            f"{iv_rank:.1f}%",
                            help="Where current IV sits in the 52-week range (0-100%)"
                        )
                    else:
                        st.metric("IV Rank (52-week)", "N/A")
                
                with iv_col3:
                    iv_percentile = iv_data.get('iv_percentile')
                    if iv_percentile is not None:
                        st.metric(
                            "IV Percentile",
                            f"{iv_percentile:.1f}%",
                            help="% of days IV was below current level in past year"
                        )
                    else:
                        st.metric("IV Percentile", "N/A")
                
                with iv_col4:
                    hist_vol = iv_data.get('historical_volatility')
                    if hist_vol:
                        st.metric(
                            "Historical Vol (30d)",
                            f"{hist_vol:.2f}%",
                            help="30-day historical volatility (annualized)"
                        )
                    else:
                        st.metric("Historical Vol (30d)", "N/A")
                
                # IV Range
                if iv_data.get('iv_52week_high') and iv_data.get('iv_52week_low'):
                    st.markdown("### 📈 52-Week IV Range")
                    
                    iv_low = iv_data['iv_52week_low']
                    iv_high = iv_data['iv_52week_high']
                    iv_current = iv_data['implied_volatility']
                    
                    # Calculate position in range (clamp between 0 and 100)
                    if iv_high > iv_low:
                        iv_position = ((iv_current - iv_low) / (iv_high - iv_low)) * 100
                        iv_position = max(0, min(100, iv_position))  # Clamp to [0, 100]
                    else:
                        iv_position = 50
                    
                    range_col1, range_col2, range_col3 = st.columns(3)
                    
                    with range_col1:
                        st.metric("52-Week Low", f"{iv_low:.2f}%")
                    
                    with range_col2:
                        st.metric("Current IV", f"{iv_current:.2f}%")
                    
                    with range_col3:
                        st.metric("52-Week High", f"{iv_high:.2f}%")
                    
                    # Progress bar showing IV position (value must be between 0.0 and 1.0)
                    st.progress(iv_position / 100)
                    
                    # Interpretation
                    if iv_position > 75:
                        st.info("🔴 **High IV:** Current IV is in the top 25% of its 52-week range. Options are relatively expensive.")
                    elif iv_position > 50:
                        st.info("🟡 **Medium-High IV:** Current IV is above the median of its 52-week range.")
                    elif iv_position > 25:
                        st.info("🟢 **Medium-Low IV:** Current IV is below the median of its 52-week range.")
                    else:
                        st.info("🟢 **Low IV:** Current IV is in the bottom 25% of its 52-week range. Options are relatively cheap.")
                
                # Detailed options data
                with st.expander("📊 Detailed Options Data"):
                    detail_col1, detail_col2 = st.columns(2)
                    
                    with detail_col1:
                        st.write(f"**Expiration Date:** {iv_data['expiration_date']}")
                        st.write(f"**Days to Expiration:** {iv_data['days_to_expiration']}")
                        st.write(f"**ATM Strike:** ${iv_data['atm_strike']:.2f}")
                        st.write(f"**Call IV:** {iv_data['call_iv']:.2f}%")
                    
                    with detail_col2:
                        st.write(f"**Put IV:** {iv_data['put_iv']:.2f}%")
                        st.write(f"**Straddle Price:** ${iv_data['straddle_price']:.2f}")
                        st.write(f"**Current Price:** ${iv_data['current_price']:.2f}")
                        st.write(f"**Earnings Date:** {iv_data.get('earnings_date', 'N/A')}")
                
                # Save to database option
                st.markdown("---")
                if st.button("💾 Save to Database", use_container_width=True):
                    try:
                        # Save earnings data
                        inserted = db.insert_earnings_data([earnings_info])
                        
                        # Save options data
                        options_inserted = db.insert_options_data([iv_data])
                        
                        st.success(f"✅ Successfully saved {ticker_to_search} data to database!")
                        st.info(f"📊 Earnings data: {inserted} record(s) | Options data: {options_inserted} record(s)")
                    except Exception as e:
                        st.error(f"❌ Error saving to database: {str(e)}")
        
        # Reset trigger after processing
        st.session_state.trigger_search = False
    
    # Tips section
    st.markdown("---")
    with st.expander("💡 Tips & Information"):
        st.markdown("""
        ### How to Use This Tool
        
        1. **Enter any ticker symbol** in the search box (e.g., AAPL, TSLA, NVDA)
        2. Click **Search** or press Enter
        3. View **earnings date** and **company information**
        4. Analyze **expected move** and **IV metrics**
        5. Optionally **save to database** for future reference
        
        ### Understanding the Metrics
        
        **Expected Move:**
        - Calculated from options prices (ATM straddle)
        - Represents ±1 standard deviation move through earnings
        - Shows the range the market expects the stock to move
        
        **IV Rank:**
        - Where current IV sits in the 52-week range (0-100%)
        - High IV Rank (>75%): Options are expensive
        - Low IV Rank (<25%): Options are cheap
        
        **IV Percentile:**
        - Percentage of days IV was below current level
        - More robust than IV Rank for comparing across stocks
        
        **Historical Volatility:**
        - Actual price movement over past 30 days
        - Compare with IV to see if options are over/under-priced
        
        ### What Tickers Work?
        
        ✅ **Works for:**
        - US-listed stocks with options (NYSE, NASDAQ)
        - Most stocks in major indices (S&P 500, NASDAQ 100)
        - ETFs with active options markets
        
        ❌ **May not work for:**
        - Stocks without listed options
        - Foreign stocks (non-US)
        - Very small cap stocks
        - Newly listed IPOs
        """)


if __name__ == "__main__":
    ticker_lookup()
