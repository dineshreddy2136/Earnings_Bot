"""Options IV Analysis Page"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from utils.data_access import init_database
from components.options_sync import sync_options_data


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
    
    # Filter out stocks with past earnings dates
    options_df = _filter_future_earnings(options_df)
    
    if options_df.empty:
        st.info("📅 No stocks with upcoming earnings found in options data. Please sync data for stocks with future earnings dates.")
        return
    
    # Display metrics
    _display_metrics(options_df)
    
    # Filters
    filtered_df = _display_filters_and_apply(options_df)
    
    if filtered_df.empty:
        st.warning("No data matches your filters. Try adjusting the filter criteria.")
        return
    
    # Display data table
    _display_options_table(filtered_df)
    
    # Display charts
    _display_charts(filtered_df)


def _filter_future_earnings(options_df):
    """Filter out stocks with past earnings dates"""
    today = datetime.now().date().strftime('%Y-%m-%d')
    
    future_earnings_df = options_df[
        (options_df['earnings_date'] == 'N/A') | 
        (options_df['earnings_date'] >= today)
    ].copy()
    
    # Show warning if we filtered out past earnings
    past_earnings_count = len(options_df) - len(future_earnings_df)
    if past_earnings_count > 0:
        st.warning(f"⚠️ Filtered out {past_earnings_count} stocks with past earnings dates. Expected move analysis is only relevant for today's and upcoming earnings.")
    
    return future_earnings_df


def _display_metrics(options_df):
    """Display key metrics"""
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


def _display_filters_and_apply(options_df):
    """Display filter controls and apply them"""
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
    filter_start, filter_end = _display_time_range_filter()
    
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
    if filter_start and filter_end:
        filter_start_str = filter_start.strftime('%Y-%m-%d')
        filter_end_str = filter_end.strftime('%Y-%m-%d')
        
        filtered_df = filtered_df[
            (filtered_df['earnings_date'] != 'N/A') &
            (filtered_df['earnings_date'] >= filter_start_str) &
            (filtered_df['earnings_date'] <= filter_end_str)
        ]
    
    return filtered_df


def _display_time_range_filter():
    """Display time range filter controls"""
    st.markdown("### 📅 Time Range Filter")
    col1, col2 = st.columns(2)
    
    with col1:
        time_filter = st.selectbox(
            "Show upcoming earnings for:",
            ["This Week", "Next 7 Days", "Next 14 Days", "This Month", "Next 30 Days", "Next 60 Days", "Custom Date Range"],
            help="Select time period for upcoming earnings (past earnings filtered out)"
        )
    
    custom_start = None
    custom_end = None
    
    with col2:
        if time_filter == "Custom Date Range":
            custom_start = st.date_input("Start Date", datetime.now().date())
            custom_end = st.date_input("End Date", datetime.now().date() + timedelta(days=7))
    
    # Calculate date range
    today = datetime.now().date()
    
    if time_filter == "This Week":
        days_until_sunday = 6 - today.weekday()
        filter_start, filter_end = today, today + timedelta(days=days_until_sunday)
    elif time_filter == "Next 7 Days":
        filter_start, filter_end = today, today + timedelta(days=7)
    elif time_filter == "Next 14 Days":
        filter_start, filter_end = today, today + timedelta(days=14)
    elif time_filter == "This Month":
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
    else:
        filter_start, filter_end = today, today + timedelta(days=365)
    
    st.info(f"📅 Showing upcoming earnings: {filter_start.strftime('%B %d')} - {filter_end.strftime('%B %d, %Y')}")
    
    return filter_start, filter_end


def _display_options_table(filtered_df):
    """Display the options data table"""
    st.markdown(f"## 📋 Options Data ({len(filtered_df)} symbols shown)")
    
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


def _display_charts(filtered_df):
    """Display analysis charts"""
    st.markdown("## 📈 IV Analysis Charts")
    
    # Expected Move $ vs Stock Price (expanded full width)
    st.markdown("### 💰 Expected Move $ vs Stock Price")
    fig_move_price = px.scatter(
        filtered_df,
        x='current_price',
        y='expected_move_dollar',
        color='implied_volatility',
        size='expected_move_percent',
        hover_data=['symbol', 'company_name', 'earnings_date', 'expected_move_up', 'expected_move_down'],
        title='Expected Move $ vs Stock Price (sized by Expected Move %)',
        labels={
            'current_price': 'Stock Price ($)',
            'expected_move_dollar': 'Expected Move ($)',
            'implied_volatility': 'IV (%)',
            'expected_move_percent': 'Expected Move %'
        }
    )
    fig_move_price.update_layout(height=500)
    st.plotly_chart(fig_move_price, use_container_width=True)
    
    # Third row: Top 10 Biggest Expected Moves
    st.markdown("### 🚀 Top Movers")
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
