#!/usr/bin/env python3
"""
Complete Earnings Dashboard - All-in-one Streamlit App
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import time
import yfinance as yf
from database import EarningsDatabase
from earnings_bot import EarningsBot
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Complete Earnings Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .earnings-card {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stDataFrame {
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
@st.cache_resource
def init_database():
    return EarningsDatabase()

db = init_database()

# Helper functions
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_weekly_earnings_data(week_start, week_end):
    """Get earnings data for a specific week from database"""
    return db.get_earnings_by_week(week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d'))

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_all_earnings_data():
    """Get all earnings data from database with revenue estimates"""
    return db.get_all_earnings()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_database_stats():
    """Get database statistics"""
    return db.get_database_stats()

def format_market_cap(market_cap):
    """Format market cap for display"""
    if pd.isna(market_cap) or market_cap == 0:
        return "N/A"
    
    if market_cap >= 1e12:
        return f"${market_cap/1e12:.2f}T"
    elif market_cap >= 1e9:
        return f"${market_cap/1e9:.2f}B"
    elif market_cap >= 1e6:
        return f"${market_cap/1e6:.2f}M"
    else:
        return f"${market_cap:,.0f}"

def get_week_dates(week_offset=0):
    """Get start and end dates for a specific week"""
    today = date.today()
    current_week_start = today - timedelta(days=today.weekday())
    target_week_start = current_week_start + timedelta(weeks=week_offset)
    target_week_end = target_week_start + timedelta(days=6)
    return target_week_start, target_week_end

# Main App
def main():
    st.title("📊 Complete Earnings Dashboard")
    st.markdown("**Your comprehensive earnings tracking and analysis platform**")
    
    # Initialize session state for week navigation
    if 'week_offset' not in st.session_state:
        st.session_state.week_offset = 0
    
    # Sidebar navigation
    st.sidebar.title("📊 Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["📅 Weekly Earnings Calendar", "📊 All Tickers Data", "🔄 Sync Data", "📈 Analytics", "📊 Options IV Analysis"]
    )
    
    # Week navigation in sidebar (for calendar page)
    if page == "📅 Weekly Earnings Calendar":
        st.sidebar.markdown("---")
        st.sidebar.subheader("📅 Week Navigation")
        
        col1, col2, col3 = st.sidebar.columns(3)
        with col1:
            if st.button("⬅️"):
                st.session_state.week_offset -= 1
                st.rerun()
        
        with col2:
            if st.button("📍"):
                st.session_state.week_offset = 0
                st.rerun()
        
        with col3:
            if st.button("➡️"):
                st.session_state.week_offset += 1
                st.rerun()
        
        # Show current week info
        week_start, week_end = get_week_dates(st.session_state.week_offset)
        if st.session_state.week_offset == 0:
            week_label = "Current Week"
        elif st.session_state.week_offset > 0:
            week_label = f"{st.session_state.week_offset} Week{'s' if st.session_state.week_offset > 1 else ''} Ahead"
        else:
            week_label = f"{abs(st.session_state.week_offset)} Week{'s' if abs(st.session_state.week_offset) > 1 else ''} Ago"
        
        st.sidebar.info(f"**{week_label}**\n{week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}")
        
        # Quick sync button in sidebar
        if st.sidebar.button("🔄 Sync Data", help="Refresh earnings data"):
            st.sidebar.info("Navigate to 'Sync Data' tab for synchronization options")

    # Page content
    if page == "📅 Weekly Earnings Calendar":
        weekly_earnings_calendar()
    elif page == "📊 All Tickers Data":
        all_tickers_data()
    elif page == "🔄 Sync Data":
        sync_data()
    elif page == "📈 Analytics":
        analytics()
    
    elif page == "📊 Options IV Analysis":
        options_iv_analysis()

def weekly_earnings_calendar():
    """Weekly earnings calendar page"""
    st.header("📅 Weekly Earnings Calendar")
    
    # Get current week dates
    week_start, week_end = get_week_dates(st.session_state.week_offset)
    
    # Week label
    if st.session_state.week_offset == 0:
        week_label = "Current Week"
    elif st.session_state.week_offset > 0:
        week_label = f"{st.session_state.week_offset} Week{'s' if st.session_state.week_offset > 1 else ''} Ahead"
    else:
        week_label = f"{abs(st.session_state.week_offset)} Week{'s' if abs(st.session_state.week_offset) > 1 else ''} Ago"
    
    st.subheader(f"{week_label}: {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}")
    
    # Get weekly earnings data
    weekly_earnings = get_weekly_earnings_data(week_start, week_end)
    
    if not weekly_earnings.empty:
        # Group by day of week
        daily_earnings = {}
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for _, row in weekly_earnings.iterrows():
            if pd.notna(row['earnings_date']):
                try:
                    earnings_date = datetime.strptime(row['earnings_date'], '%Y-%m-%d').date()
                    day_name = earnings_date.strftime('%A')
                    if day_name not in daily_earnings:
                        daily_earnings[day_name] = []
                    daily_earnings[day_name].append(row)
                except:
                    continue
        
        # Display earnings by day
        for day in days:
            day_date = week_start + timedelta(days=days.index(day))
            st.markdown(f"### {day}, {day_date.strftime('%B %d')}")
            
            if day in daily_earnings:
                companies = daily_earnings[day]
                
                # Create columns for companies
                cols = st.columns(min(len(companies), 4))
                for i, company in enumerate(companies):
                    with cols[i % 4]:
                        eps_display = f"{company['eps_estimate']:.2f}" if pd.notna(company['eps_estimate']) and company['eps_estimate'] != 'N/A' else 'N/A'
                        
                        # Format revenue estimate (convert to millions/billions)
                        revenue_display = 'N/A'
                        revenue_estimate = company.get('revenue_estimate', 'N/A')
                        if pd.notna(revenue_estimate) and revenue_estimate != 'N/A' and revenue_estimate != 0:
                            revenue = revenue_estimate
                            if revenue >= 1e9:
                                revenue_display = f"${revenue/1e9:.1f}B"
                            elif revenue >= 1e6:
                                revenue_display = f"${revenue/1e6:.1f}M"
                            else:
                                revenue_display = f"${revenue/1e3:.1f}K"
                        
                        # Get earnings timing info
                        timing_display = company.get('earnings_time', 'N/A')
                        timing_icon = "🌅" if timing_display == "BMO" else "🌙" if timing_display == "AMC" else "❓"
                        
                        st.markdown(f"""
                        **{company['symbol']}**  
                        {company['company_name']}  
                        {timing_icon} {timing_display}  
                        💰 EPS Est: {eps_display}  
                        📊 Rev Est: {revenue_display}  
                        🏢 {company['sector'] if pd.notna(company['sector']) else 'N/A'}
                        """)
            else:
                st.info("No earnings scheduled")
            
            st.markdown("---")
        
        # Summary metrics
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Companies", len(weekly_earnings))
        
        with col2:
            avg_market_cap = weekly_earnings['market_cap'].mean()
            st.metric("Avg Market Cap", format_market_cap(avg_market_cap) if pd.notna(avg_market_cap) else "N/A")
        
        with col3:
            sectors = weekly_earnings['sector'].value_counts()
            top_sector = sectors.index[0] if len(sectors) > 0 else "N/A"
            st.metric("Top Sector", top_sector)
        
        with col4:
            companies_with_estimates = weekly_earnings['eps_estimate'].notna().sum()
            st.metric("With EPS Est.", f"{companies_with_estimates}/{len(weekly_earnings)}")
    
    else:
        st.info(f"📭 No earnings scheduled for {week_label.lower()}")
        st.markdown("Try navigating to a different week using the sidebar controls.")

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
        
        # Filter to only show tickers from a.json
        if not all_earnings_data.empty:
            # Create a dataframe with all symbols from a.json
            symbols_df = pd.DataFrame({'symbol': all_symbols})
            
            # Merge with earnings data to get all tickers (even those without earnings data)
            combined_data = symbols_df.merge(all_earnings_data, on='symbol', how='left')
            
            # Fill missing values
            combined_data['earnings_date'] = combined_data['earnings_date'].fillna('N/A')
            combined_data['company_name'] = combined_data['company_name'].fillna('N/A')
            combined_data['sector'] = combined_data['sector'].fillna('N/A')
            combined_data['current_price'] = combined_data['current_price'].fillna(0)
            combined_data['market_cap'] = combined_data['market_cap'].fillna(0)
            combined_data['eps_estimate'] = combined_data['eps_estimate'].fillna(0)
            
            # Handle revenue_estimate column (might not exist in older data)
            if 'revenue_estimate' not in combined_data.columns:
                combined_data['revenue_estimate'] = 0
            else:
                combined_data['revenue_estimate'] = combined_data['revenue_estimate'].fillna(0)
            
            # Handle earnings_time column (might not exist in older data)
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
        
        # Apply sector filter
        if selected_sector != 'All':
            filtered_data = combined_data[combined_data['sector'] == selected_sector]
        else:
            filtered_data = combined_data.copy()
        
        # Sort data
        if sort_by == 'Symbol':
            filtered_data = filtered_data.sort_values('symbol')
        elif sort_by == 'Earnings Date':
            # Sort by earnings date, putting N/A at the end
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
        
        # Main data table
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
        
        # Format revenue estimate
        def format_revenue_estimate(value):
            if pd.isna(value) or value == 0 or value == 'N/A':
                return "N/A"
            if value >= 1e9:
                return f"${value/1e9:.1f}B"
            elif value >= 1e6:
                return f"${value/1e6:.1f}M"
            else:
                return f"${value/1e3:.1f}K"
        
        # Add revenue_estimate column if it doesn't exist
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
        
        # Summary stats
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
            sync_needed = total_tickers - max(with_earnings, with_prices)
            st.metric("Need Sync", sync_needed)
        
        # Download option
        csv = filtered_data.to_csv(index=False)
        st.download_button(
            label="📥 Download All Data as CSV",
            data=csv,
            file_name=f"all_tickers_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
        
        # Data status message
        if len(all_earnings_data) == 0:
            st.warning("📭 No data found in database. Use the 'Sync Data' tab to fetch earnings data from yfinance.")
        elif len(filtered_data[filtered_data['earnings_date'] != 'N/A']) < len(all_symbols) * 0.5:
            st.info("ℹ️ Many tickers are missing earnings data. Consider running a full sync in the 'Sync Data' tab.")
    
    else:
        st.error("No tickers found in a.json file. Please check the file exists and contains ticker symbols.")

def sync_data():
    """Data synchronization page"""
    st.header("🔄 Data Synchronization Center")
    st.markdown("Keep your earnings data up-to-date with the latest information from yfinance")
    
    # Current data status
    stats = get_database_stats()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Companies", stats['total_companies'])
    with col2:
        st.metric("Earnings Records", stats['total_earnings_records'])
    with col3:
        last_update = stats['last_update'] or "Never"
        st.metric("Last Update", last_update)
    
    st.markdown("---")
    
    # Sync options
    st.subheader("🔄 Sync Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚀 Full Data Sync")
        st.info("Process all 301 tickers from a.json file and update the database with latest earnings data.")
        
        if st.button("🚀 Start Full Sync", type="primary"):
            with st.spinner("Syncing all earnings data... This may take several minutes."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    bot = EarningsBot()
                    symbols = bot.load_tickers_from_json()
                    total_symbols = len(symbols)
                    processed_data = []
                    
                    for i, symbol in enumerate(symbols):
                        progress = (i + 1) / total_symbols
                        progress_bar.progress(progress)
                        status_text.text(f"Processing {symbol} ({i+1}/{total_symbols})")
                        
                        earnings_info = bot.get_earnings_for_symbol(symbol)
                        if earnings_info:
                            processed_data.append(earnings_info)
                    
                    if processed_data:
                        inserted_count = bot.db.insert_earnings_data(processed_data)
                        st.success(f"✅ Sync completed! Processed {len(processed_data)} companies, updated {inserted_count} records.")
                    else:
                        st.warning("⚠️ No data was retrieved. Please check your internet connection.")
                        
                except Exception as e:
                    st.error(f"❌ Sync failed: {str(e)}")
    
    with col2:
        st.markdown("### ⚡ Quick Sync")
        st.info("Process top 20 major companies for quick testing and immediate results.")
        major_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD', 'INTC', 
                        'CRM', 'ORCL', 'ADBE', 'PYPL', 'UBER', 'ABNB', 'COIN', 'SQ', 'ROKU', 'ZOOM']
        
        if st.button("⚡ Quick Sync (20 tickers)", type="secondary"):
            with st.spinner("Quick sync in progress..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    bot = EarningsBot()
                    processed_data = []
                    
                    for i, symbol in enumerate(major_tickers):
                        progress = (i + 1) / len(major_tickers)
                        progress_bar.progress(progress)
                        status_text.text(f"Processing {symbol} ({i+1}/{len(major_tickers)})")
                        
                        earnings_info = bot.get_earnings_for_symbol(symbol)
                        if earnings_info:
                            processed_data.append(earnings_info)
                    
                    if processed_data:
                        inserted_count = bot.db.insert_earnings_data(processed_data)
                        st.success(f"✅ Quick sync completed! Processed {len(processed_data)} companies, updated {inserted_count} records.")
                    else:
                        st.warning("⚠️ No data was retrieved. Please check your internet connection.")
                        
                except Exception as e:
                    st.error(f"❌ Quick sync failed: {str(e)}")

def analytics():
    """Analytics page"""
    st.header("📈 Analytics & Insights")
    st.markdown("Data analysis and visualization of earnings information")
    
    # Get all data for analytics
    all_data = get_all_earnings_data()
    
    if all_data.empty:
        st.warning("📭 No data available for analytics. Please sync data first.")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Companies", len(all_data))
    
    with col2:
        upcoming_earnings = len(all_data[all_data['earnings_date'] > datetime.now().strftime('%Y-%m-%d')])
        st.metric("Upcoming Earnings", upcoming_earnings)
    
    with col3:
        sectors = all_data['sector'].nunique()
        st.metric("Sectors Covered", sectors)
    
    with col4:
        avg_market_cap = all_data['market_cap'].mean()
        st.metric("Avg Market Cap", format_market_cap(avg_market_cap))
    
    st.markdown("---")
    
    # Sector analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Companies by Sector")
        sector_counts = all_data['sector'].value_counts().head(10)
        if not sector_counts.empty:
            fig = px.bar(
                x=sector_counts.values,
                y=sector_counts.index,
                orientation='h',
                title="Top 10 Sectors by Company Count"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("💰 Market Cap Distribution")
        market_cap_data = all_data[all_data['market_cap'] > 0]['market_cap']
        if not market_cap_data.empty:
            fig = px.histogram(
                market_cap_data,
                nbins=20,
                title="Market Cap Distribution"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Search and filter
    st.markdown("---")
    st.subheader("🔍 Company Search")
    
    search_term = st.text_input("Search by company name or symbol:")
    if search_term:
        filtered = all_data[
            all_data['symbol'].str.contains(search_term, case=False, na=False) |
            all_data['company_name'].str.contains(search_term, case=False, na=False)
        ]
        
        if not filtered.empty:
            # Ensure earnings_time column exists for display
            if 'earnings_time' not in filtered.columns:
                filtered['earnings_time'] = 'N/A'
            
            st.dataframe(
                filtered[['symbol', 'company_name', 'earnings_date', 'earnings_time', 'sector', 'market_cap']],
                use_container_width=True
            )
        else:
            st.info("No companies found matching your search.")

def options_iv_analysis():
    """Options IV Analysis page"""
    st.markdown("# 📊 Options IV Analysis")
    st.markdown("**Implied volatility and expected move analysis for upcoming earnings plays**")
    st.markdown("💡 *Only showing stocks with today's and future earnings dates - past earnings IV data is not relevant*")
    
    # Add sync options data section
    with st.expander("🔧 Sync Options Data", expanded=False):
        st.markdown("*Fetch IV data for stocks with upcoming earnings only*")
        sync_options_data()
    
    # Get options data from database
    database = init_database()
    options_df = database.get_all_options_data()
    
    if options_df.empty:
        st.warning("No options data available. Please sync data first using the button above.")
        return
    
    # Filter out stocks with past earnings dates (CRITICAL FIX)
    from datetime import datetime
    today = datetime.now().date().strftime('%Y-%m-%d')
    
    # Only show stocks with future earnings (including today) or no earnings date
    future_earnings_df = options_df[
        (options_df['earnings_date'] == 'N/A') | 
        (options_df['earnings_date'] >= today)
    ].copy()
    
    # Show warning if we filtered out past earnings
    past_earnings_count = len(options_df) - len(future_earnings_df)
    if past_earnings_count > 0:
        st.warning(f"⚠️ Filtered out {past_earnings_count} stocks with past earnings dates. Expected move analysis is only relevant for today's and upcoming earnings.")
    
    if future_earnings_df.empty:
        st.info("📅 No stocks with upcoming earnings found in options data. Please sync data for stocks with future earnings dates.")
        return
    
    # Use filtered data for the rest of the analysis
    options_df = future_earnings_df
    
    # Metrics (only for upcoming earnings)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Upcoming Earnings", len(options_df))
    with col2:
        avg_iv = options_df['implied_volatility'].mean()
        st.metric("Average IV", f"{avg_iv:.1f}%", help="Average implied volatility for upcoming earnings")
    with col3:
        avg_expected_move = options_df['expected_move_percent'].mean()
        st.metric("Avg Expected Move", f"{avg_expected_move:.1f}%", help="Average expected move for upcoming earnings")
    with col4:
        high_iv_count = len(options_df[options_df['implied_volatility'] > 50])
        st.metric("High IV (>50%)", high_iv_count, help="High volatility upcoming earnings")
    
    # Filters
    st.markdown("## 🎛️ Filters")
    col1, col2, col3 = st.columns(3)
    with col1:
        min_iv = st.slider("Minimum IV%", 0.0, 100.0, 0.0, 5.0, help="Filter by minimum implied volatility")
        max_days = st.slider("Max Days to Expiration", 1, 60, 30, help="Maximum days until options expire")
    with col2:
        sectors = ['All'] + sorted(list(options_df['sector'].dropna().unique()))
        selected_sector = st.selectbox("Filter by Sector", sectors)
        min_expected_move = st.slider("Min Expected Move%", 0.0, 20.0, 0.0, 0.5, help="Minimum expected percentage move")
    with col3:
        min_price = st.slider("Min Stock Price", 0.0, 500.0, 0.0, 10.0, help="Minimum stock price filter")
        
    # Time range selection
    st.markdown("### 📅 Time Range Filter")
    col1, col2 = st.columns(2)
    
    with col1:
        time_filter = st.selectbox(
            "Show upcoming earnings for:",
            ["This Week", "Next 7 Days", "Next 14 Days", "This Month", "Next 30 Days", "Next 60 Days", "Custom Date Range"],
            help="Select time period for upcoming earnings (past earnings filtered out)"
        )
    
    with col2:
        if time_filter == "Custom Date Range":
            custom_start = st.date_input("Start Date", datetime.now().date())
            custom_end = st.date_input("End Date", datetime.now().date() + timedelta(days=7))
    
    # Calculate date range based on selection (all future-focused)
    from datetime import datetime, timedelta 
    today = datetime.now().date()
    
    if time_filter == "This Week":
        # From today to end of current week (Sunday)
        days_until_sunday = 6 - today.weekday()  # weekday() returns 0=Monday, 6=Sunday
        filter_start, filter_end = today, today + timedelta(days=days_until_sunday)
        
    elif time_filter == "Next 7 Days":
        filter_start, filter_end = today, today + timedelta(days=7)
        
    elif time_filter == "Next 14 Days":
        filter_start, filter_end = today, today + timedelta(days=14)
        
    elif time_filter == "This Month":
        # From today to end of current month
        if today.month == 12:
            end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        filter_start, filter_end = today, end_of_month
        
    elif time_filter == "Next 30 Days":
        filter_start, filter_end = today, today + timedelta(days=30)
        
    elif time_filter == "Next 60 Days":
        filter_start, filter_end = today, today + timedelta(days=60)
        
    elif time_filter == "Custom Date Range":
        filter_start, filter_end = custom_start, custom_end
        
    else:  # Default fallback
        filter_start, filter_end = today, today + timedelta(days=365)
    
    # Show selected date range
    st.info(f"📅 Showing upcoming earnings: {filter_start.strftime('%B %d')} - {filter_end.strftime('%B %d, %Y')}")
    
    # Apply filters
    filtered_df = options_df[
        (options_df['implied_volatility'] >= min_iv) & 
        (options_df['days_to_expiration'] <= max_days) &
        (options_df['expected_move_percent'] >= min_expected_move) &
        (options_df['current_price'] >= min_price)
    ]
    
    if selected_sector != 'All':
        filtered_df = filtered_df[filtered_df['sector'] == selected_sector]
    
    # Apply time range filter
    if time_filter != "All Upcoming":
        filter_start_str = filter_start.strftime('%Y-%m-%d')
        filter_end_str = filter_end.strftime('%Y-%m-%d')
        
        filtered_df = filtered_df[
            (filtered_df['earnings_date'] != 'N/A') &
            (filtered_df['earnings_date'] >= filter_start_str) &
            (filtered_df['earnings_date'] <= filter_end_str)
        ]
    else:
        # For "All Upcoming", just filter out N/A dates and past dates
        today_str = today.strftime('%Y-%m-%d')
        filtered_df = filtered_df[
            (filtered_df['earnings_date'] != 'N/A') &
            (filtered_df['earnings_date'] >= today_str)
        ]
    st.write(filtered_df)
    # Summary after filters
    st.markdown(f"## 📋 Options Data ({len(filtered_df)} symbols shown)")
    
    if filtered_df.empty:
        st.warning("No data matches your filters. Try adjusting the filter criteria.")
        return
    
    # Display options data table
    display_columns = [
        'symbol', 'company_name', 'current_price', 'earnings_date', 'days_to_expiration',
        'implied_volatility', 'expected_move_percent', 'expected_move_dollar',
        'expected_move_up', 'expected_move_down', 'sector'
    ]
    
    # Ensure all columns exist
    for col in display_columns:
        if col not in filtered_df.columns:
            filtered_df[col] = 'N/A'
    
    st.dataframe(
        filtered_df[display_columns].sort_values('expected_move_percent', ascending=False),
        use_container_width=True,
        column_config={
            "symbol": st.column_config.TextColumn("Symbol", width="small"),
            "company_name": st.column_config.TextColumn("Company", width="medium"),
            "current_price": st.column_config.NumberColumn("Price", format="$%.2f", width="small"),
            "earnings_date": st.column_config.TextColumn("Earnings Date", width="medium"),
            "days_to_expiration": st.column_config.NumberColumn("Days to Exp", width="small"),
            "implied_volatility": st.column_config.NumberColumn("IV%", format="%.1f%%", width="small"),
            "expected_move_percent": st.column_config.NumberColumn("Expected Move%", format="%.1f%%", width="small"),
            "expected_move_dollar": st.column_config.NumberColumn("Expected Move $", format="$%.2f", width="small"),
            "expected_move_up": st.column_config.NumberColumn("Expected Up", format="$%.2f", width="small"),
            "expected_move_down": st.column_config.NumberColumn("Expected Down", format="$%.2f", width="small"),
            "sector": st.column_config.TextColumn("Sector", width="medium")
        }
    )
    
    # Charts
    st.markdown("## 📈 IV Analysis Charts")
    
    col1, col2 = st.columns(2)
    with col1:
        # IV vs Expected Move scatter plot
        import plotly.express as px
        fig_scatter = px.scatter(
            filtered_df,
            x='implied_volatility',
            y='expected_move_percent',
            color='sector',
            size='current_price',
            hover_data=['symbol', 'company_name', 'earnings_date'],
            title='IV vs Expected Move',
            labels={
                'implied_volatility': 'Implied Volatility (%)',
                'expected_move_percent': 'Expected Move (%)'
            }
        )
        fig_scatter.update_layout(height=400)
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    with col2:
        # IV Distribution histogram
        fig_hist = px.histogram(
            filtered_df,
            x='implied_volatility',
            nbins=20,
            title='IV Distribution',
            labels={'implied_volatility': 'Implied Volatility (%)', 'count': 'Number of Stocks'}
        )
        fig_hist.update_layout(height=400)
        st.plotly_chart(fig_hist, use_container_width=True)
    
    # Additional analysis
    col1, col2 = st.columns(2)
    with col1:
        # Expected Move vs Current Price
        fig_move_price = px.scatter(
            filtered_df,
            x='current_price',
            y='expected_move_dollar',
            color='implied_volatility',
            hover_data=['symbol', 'company_name'],
            title='Expected Move $ vs Stock Price',
            labels={
                'current_price': 'Stock Price ($)',
                'expected_move_dollar': 'Expected Move ($)',
                'implied_volatility': 'IV (%)'
            }
        )
        fig_move_price.update_layout(height=400)
        st.plotly_chart(fig_move_price, use_container_width=True)
    
    with col2:
        # Expected Move Range Analysis
        fig_range = px.bar(
            filtered_df.nlargest(10, 'expected_move_percent'),
            x='symbol',
            y='expected_move_percent',
            title='Top 10 Biggest Expected Moves',
            labels={'expected_move_percent': 'Expected Move (%)'},
            hover_data=['expected_move_up', 'expected_move_down', 'company_name', 'earnings_date']
        )
        fig_range.update_layout(height=400)
        st.plotly_chart(fig_range, use_container_width=True)

def sync_options_data():
    """Sync options IV data for stocks with upcoming earnings only"""
    from earnings_bot import EarningsBot
    from datetime import datetime, timedelta
    
    st.markdown("**⚠️ Important**: Options IV analysis is only meaningful for stocks with upcoming earnings (not past earnings)")

    # --- Step 1: Selection UI ---
    sync_option = st.radio(
        "Sync IV data for stocks with earnings:",
        ["This Week", "Next 7 Days", "Next 14 Days", "Next 30 Days", "Custom Selection"],
        horizontal=True,
        key="sync_option_radio",
        help="Only upcoming earnings are relevant for options analysis"
    )

    today = datetime.now().date()
    symbols_to_sync = []
    period_name = ""

    if sync_option == "Custom Selection":
        all_symbols = EarningsBot().load_tickers_from_json()
        selected_symbols = st.multiselect(
            "Select specific symbols (only those with upcoming earnings are useful):",
            all_symbols,
            default=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA"],
            key="custom_symbols_select"
        )
        if selected_symbols:
            symbols_to_sync = selected_symbols
            period_name = f"{len(symbols_to_sync)} selected symbols"
    else:
        if sync_option == "This Week":
            start_date, end_date = today, today + timedelta(days=6 - today.weekday())
            period_name = "this week"
        elif sync_option == "Next 7 Days":
            start_date, end_date = today, today + timedelta(days=7)
            period_name = "the next 7 days"
        elif sync_option == "Next 14 Days":
            start_date, end_date = today, today + timedelta(days=14)
            period_name = "the next 14 days"
        else: # "Next 30 Days"
            start_date, end_date = today, today + timedelta(days=30)
            period_name = "the next 30 days"
        
        st.info(f"📅 Selected period: {start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}")
        database = init_database()
        earnings_data = database.get_earnings_by_week(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        
        # Filter out past earnings from the selection
        earnings_data = earnings_data[earnings_data['earnings_date'] >= today.strftime('%Y-%m-%d')]

        if not earnings_data.empty:
            symbols_to_sync = earnings_data['symbol'].unique().tolist()

    # --- Step 2: Confirmation and Execution ---
    if not symbols_to_sync:
        st.warning("No symbols selected or found for the chosen period. Please adjust your selection.")
        return

    st.markdown("---")
    st.subheader(f"Step 2: Confirm and Sync for {period_name}")
    
    st.info(f"Found {len(symbols_to_sync)} stocks to sync: `{', '.join(symbols_to_sync[:20])}{'...' if len(symbols_to_sync) > 20 else ''}`")

    proceed_to_sync = True
    if len(symbols_to_sync) > 40:
        st.warning(f"⚠️ This is a large sync operation with {len(symbols_to_sync)} stocks. It may take several minutes.")
        if not st.checkbox(f"I understand and want to proceed with syncing {len(symbols_to_sync)} stocks.", key="large_sync_confirm"):
            proceed_to_sync = False

    if not proceed_to_sync:
        st.info("Sync cancelled. Please confirm above to proceed with a large sync.")
        return

    if st.button(f"🚀 Run Sync for {len(symbols_to_sync)} Stocks", type="primary"):
        database = init_database()
        with st.spinner("Fetching FRESH options data from the market..."):
            bot = EarningsBot()
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            options_data = []
            for i, symbol in enumerate(symbols_to_sync):
                status_text.text(f"Processing {symbol} ({i+1}/{len(symbols_to_sync)})")
                
                # Fetch fresh IV data from the market
                iv_data = bot.get_options_iv_data(symbol)
                if iv_data:
                    # Get IV crush estimate
                    crush_data = bot.get_iv_crush_estimate(symbol)
                    if crush_data:
                        iv_data.update(crush_data)
                    options_data.append(iv_data)
                
                progress_bar.progress((i + 1) / len(symbols_to_sync))

            # Insert into database
            if options_data:
                count = database.insert_options_data(options_data)
                st.success(f"✅ Successfully synced {count} options records!")
            else:
                st.warning("No relevant options data could be fetched. The selected stocks may not have active options chains.")
            
            progress_bar.empty()
            status_text.empty()
            
            # Refresh the page to show new data
            st.rerun()

if __name__ == "__main__":
    main()