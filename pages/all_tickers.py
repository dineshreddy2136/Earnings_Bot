"""All Tickers Data Page"""
import streamlit as st
import pandas as pd
from datetime import datetime
from earnings_bot import EarningsBot
from utils.data_access import get_all_earnings_data
from utils.formatters import format_market_cap, format_revenue_estimate


def all_tickers_data():
    """All tickers data page - shows data from database"""
    st.header("📊 All Tickers Data")
    st.markdown("Earnings data for all your tickers from a.json - stored in database")
    
    # Load tickers from a.json
    try:
        bot_temp = EarningsBot()
        all_symbols = bot_temp.load_tickers_from_json()
        st.info(f"📋 Showing data for {len(all_symbols)} tickers from a.json")
    except Exception as e:
        st.error(f"Error loading tickers: {e}")
        all_symbols = []
    
    if all_symbols:
        # Get all earnings data from database
        all_earnings_data = get_all_earnings_data()
        
        # Merge with symbols and handle missing data
        combined_data = _merge_and_prepare_data(all_symbols, all_earnings_data)
        
        # Add controls
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Sector filter
            available_sectors = ['All'] + sorted(combined_data[combined_data['sector'] != 'N/A']['sector'].unique().tolist())
            selected_sector = st.selectbox("🏭 Filter by Sector", available_sectors)
        
        with col2:
            # Sort options
            sort_options = ['Symbol', 'Earnings Date', 'Market Cap', 'Company Name', 'Sector']
            sort_by = st.selectbox("📈 Sort by", sort_options)
        
        # Apply filters and sorting
        filtered_data = _filter_and_sort_data(combined_data, selected_sector, sort_by)
        
        # Display data table
        _display_data_table(filtered_data)
        
        # Summary stats
        _display_summary_stats(filtered_data, all_symbols, all_earnings_data)
        
        # Download option
        csv = filtered_data.to_csv(index=False)
        st.download_button(
            label="📥 Download All Data as CSV",
            data=csv,
            file_name=f"all_tickers_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
        
        # Data status message
        _show_data_status_message(all_earnings_data, filtered_data, all_symbols)
    
    else:
        st.error("No tickers found in a.json file. Please check the file exists and contains ticker symbols.")


def _merge_and_prepare_data(all_symbols, all_earnings_data):
    """Merge symbols with earnings data and fill missing values"""
    if not all_earnings_data.empty:
        symbols_df = pd.DataFrame({'symbol': all_symbols})
        combined_data = symbols_df.merge(all_earnings_data, on='symbol', how='left')
        
        # Fill missing values
        combined_data['earnings_date'] = combined_data['earnings_date'].fillna('N/A')
        combined_data['company_name'] = combined_data['company_name'].fillna('N/A')
        combined_data['sector'] = combined_data['sector'].fillna('N/A')
        combined_data['current_price'] = combined_data['current_price'].fillna(0)
        combined_data['market_cap'] = combined_data['market_cap'].fillna(0)
        combined_data['eps_estimate'] = combined_data['eps_estimate'].fillna(0)
        
        # Handle revenue_estimate column
        if 'revenue_estimate' not in combined_data.columns:
            combined_data['revenue_estimate'] = 0
        else:
            combined_data['revenue_estimate'] = combined_data['revenue_estimate'].fillna(0)
        
        # Handle earnings_time column
        if 'earnings_time' not in combined_data.columns:
            combined_data['earnings_time'] = 'N/A'
        else:
            combined_data['earnings_time'] = combined_data['earnings_time'].fillna('N/A')
    else:
        # If no data in database, create empty dataframe with just symbols
        combined_data = pd.DataFrame({
            'symbol': all_symbols,
            'company_name': 'N/A',
            'earnings_date': 'N/A',
            'earnings_time': 'N/A',
            'sector': 'N/A',
            'current_price': 0,
            'market_cap': 0,
            'eps_estimate': 0,
            'revenue_estimate': 0
        })
    
    return combined_data


def _filter_and_sort_data(combined_data, selected_sector, sort_by):
    """Apply sector filter and sorting to data"""
    # Apply sector filter
    if selected_sector != 'All':
        filtered_data = combined_data[combined_data['sector'] == selected_sector]
    else:
        filtered_data = combined_data.copy()
    
    # Sort data
    if sort_by == 'Symbol':
        filtered_data = filtered_data.sort_values('symbol')
    elif sort_by == 'Earnings Date':
        filtered_data['sort_date'] = filtered_data['earnings_date'].apply(
            lambda x: '9999-12-31' if x == 'N/A' else x
        )
        filtered_data = filtered_data.sort_values('sort_date')
        filtered_data = filtered_data.drop('sort_date', axis=1)
    elif sort_by == 'Market Cap':
        filtered_data = filtered_data.sort_values('market_cap', ascending=False)
    elif sort_by == 'Company Name':
        filtered_data = filtered_data.sort_values('company_name')
    elif sort_by == 'Sector':
        filtered_data = filtered_data.sort_values('sector')
    
    return filtered_data


def _display_data_table(filtered_data):
    """Display the main data table with formatting"""
    st.subheader(f"📊 All Tickers ({len(filtered_data)} shown)")
    
    # Prepare display dataframe
    display_df = filtered_data.copy()
    
    # Format columns for display
    display_df['current_price'] = display_df['current_price'].apply(
        lambda x: f"${x:.2f}" if x > 0 else "N/A"
    )
    display_df['market_cap'] = display_df['market_cap'].apply(
        lambda x: format_market_cap(x) if x > 0 else "N/A"
    )
    display_df['eps_estimate'] = display_df['eps_estimate'].apply(
        lambda x: f"{x:.2f}" if pd.notna(x) and x != 0 else "N/A"
    )
    
    if 'revenue_estimate' not in display_df.columns:
        display_df['revenue_estimate'] = 0
    
    display_df['revenue_estimate'] = display_df['revenue_estimate'].apply(format_revenue_estimate)
    
    # Select columns to display
    columns_to_show = [
        'symbol', 'company_name', 'earnings_date', 'earnings_time', 'sector', 
        'current_price', 'market_cap', 'eps_estimate', 'revenue_estimate'
    ]
    
    # Display the data
    st.dataframe(
        display_df[columns_to_show],
        use_container_width=True,
        column_config={
            "symbol": st.column_config.TextColumn("Symbol", width="small"),
            "company_name": st.column_config.TextColumn("Company Name", width="large"),
            "earnings_date": st.column_config.TextColumn("Earnings Date", width="medium"),
            "earnings_time": st.column_config.TextColumn("Timing", width="small"),
            "sector": st.column_config.TextColumn("Sector", width="medium"),
            "current_price": st.column_config.TextColumn("Current Price", width="small"),
            "market_cap": st.column_config.TextColumn("Market Cap", width="small"),
            "eps_estimate": st.column_config.TextColumn("EPS Est.", width="small"),
            "revenue_estimate": st.column_config.TextColumn("Revenue Est.", width="small")
        }
    )


def _display_summary_stats(filtered_data, all_symbols, all_earnings_data):
    """Display summary statistics"""
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_tickers = len(filtered_data)
        st.metric("Total Tickers", total_tickers)
    
    with col2:
        with_earnings = len(filtered_data[filtered_data['earnings_date'] != 'N/A'])
        st.metric("With Earnings Data", with_earnings)
    
    with col3:
        with_prices = len(filtered_data[filtered_data['current_price'] != "N/A"])
        st.metric("With Price Data", with_prices)
    
    with col4:
        sync_needed = len(filtered_data) - max(with_earnings, with_prices)
        st.metric("Need Sync", sync_needed)


def _show_data_status_message(all_earnings_data, filtered_data, all_symbols):
    """Show appropriate data status message"""
    if len(all_earnings_data) == 0:
        st.warning("📭 No data found in database. Use the 'Sync Data' tab to fetch earnings data from yfinance.")
    elif len(filtered_data[filtered_data['earnings_date'] != 'N/A']) < len(all_symbols) * 0.5:
        st.info("ℹ️ Many tickers are missing earnings data. Consider running a full sync in the 'Sync Data' tab.")
