"""Data access utilities with caching"""
import streamlit as st
from database import EarningsDatabase


@st.cache_resource
def init_database():
    """Initialize database connection"""
    return EarningsDatabase()


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_weekly_earnings_data(week_start, week_end):
    """Get earnings data for a specific week from database"""
    db = init_database()
    return db.get_earnings_by_week(week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d'))


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_all_earnings_data():
    """Get all earnings data from database with revenue estimates"""
    db = init_database()
    return db.get_all_earnings()


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_database_stats():
    """Get database statistics"""
    db = init_database()
    return db.get_database_stats()
