"""Analytics Page"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.data_access import get_all_earnings_data
from utils.formatters import format_market_cap


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
    _display_key_metrics(all_data)
    
    st.markdown("---")
    
    # Sector analysis
    _display_sector_analysis(all_data)
    
    # Search and filter
    st.markdown("---")
    _display_company_search(all_data)


def _display_key_metrics(all_data):
    """Display key metrics"""
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


def _display_sector_analysis(all_data):
    """Display sector analysis charts"""
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


def _display_company_search(all_data):
    """Display company search section"""
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
