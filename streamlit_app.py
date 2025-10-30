#!/usr/bin/env python3
"""
Complete Earnings Dashboard - Main Application
Modular and well-organized Streamlit app
"""

import streamlit as st
from utils.date_helpers import get_week_dates, get_week_label
from pages.weekly_calendar import weekly_earnings_calendar
from pages.all_tickers import all_tickers_data
from pages.sync_page import sync_data
from pages.options_iv import options_iv_analysis

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


def main():
    """Main application entry point"""
    st.title("📊 Complete Earnings Dashboard")
    st.markdown("**Your comprehensive earnings tracking and analysis platform**")
    
    # Initialize session state for week navigation
    if 'week_offset' not in st.session_state:
        st.session_state.week_offset = 0
    
    # Sidebar navigation
    page = setup_sidebar()
    
    # Route to appropriate page
    route_to_page(page)


def setup_sidebar():
    """Configure sidebar navigation and controls"""
    st.sidebar.title("📊 Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["📅 Weekly Earnings Calendar", "📊 All Tickers Data", "🔄 Sync Data", "📊 Options IV Analysis"]
    )
    
    # Week navigation controls (only for calendar page)
    if page == "📅 Weekly Earnings Calendar":
        setup_week_navigation()
    
    return page


def setup_week_navigation():
    """Setup week navigation controls in sidebar"""
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
    week_label = get_week_label(st.session_state.week_offset)
    
    st.sidebar.info(f"**{week_label}**\n{week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}")
    
    # Quick sync button in sidebar
    if st.sidebar.button("🔄 Sync Data", help="Refresh earnings data"):
        st.sidebar.info("Navigate to 'Sync Data' tab for synchronization options")


def route_to_page(page):
    """Route to the selected page"""
    if page == "📅 Weekly Earnings Calendar":
        weekly_earnings_calendar(st.session_state.week_offset)
    elif page == "📊 All Tickers Data":
        all_tickers_data()
    elif page == "🔄 Sync Data":
        sync_data()
    elif page == "📊 Options IV Analysis":
        options_iv_analysis()


if __name__ == "__main__":
    main()
