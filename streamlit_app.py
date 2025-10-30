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
    """Get all earnings data from database"""
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
        ["📅 Weekly Earnings Calendar", "📊 All Tickers Data", "🔄 Sync Data", "📈 Analytics"]
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
                        st.markdown(f"""
                        **{company['symbol']}**  
                        {company['company_name']}  
                        💰 EPS Est: {company['eps_estimate'] if pd.notna(company['eps_estimate']) else 'N/A'}  
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
        else:
            # If no data in database, create empty dataframe with just symbols
            combined_data = pd.DataFrame({
                'symbol': all_symbols,
                'company_name': 'N/A',
                'earnings_date': 'N/A',
                'sector': 'N/A',
                'current_price': 0,
                'market_cap': 0,
                'eps_estimate': 0
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
        
        # Select columns to display
        columns_to_show = [
            'symbol', 'company_name', 'earnings_date', 'sector', 
            'current_price', 'market_cap', 'eps_estimate'
        ]
        
        # Display the data
        st.dataframe(
            display_df[columns_to_show],
            use_container_width=True,
            column_config={
                "symbol": st.column_config.TextColumn("Symbol", width="small"),
                "company_name": st.column_config.TextColumn("Company Name", width="large"),
                "earnings_date": st.column_config.TextColumn("Earnings Date", width="medium"),
                "sector": st.column_config.TextColumn("Sector", width="medium"),
                "current_price": st.column_config.TextColumn("Current Price", width="small"),
                "market_cap": st.column_config.TextColumn("Market Cap", width="small"),
                "eps_estimate": st.column_config.TextColumn("EPS Estimate", width="small")
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
            st.dataframe(
                filtered[['symbol', 'company_name', 'earnings_date', 'sector', 'market_cap']],
                use_container_width=True
            )
        else:
            st.info("No companies found matching your search.")

if __name__ == "__main__":
    main()