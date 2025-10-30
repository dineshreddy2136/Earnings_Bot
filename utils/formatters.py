"""Formatting utilities for display"""
import pandas as pd


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


def format_revenue_estimate(value):
    """Format revenue estimate for display"""
    if pd.isna(value) or value == 0 or value == 'N/A':
        return "N/A"
    if value >= 1e9:
        return f"${value/1e9:.1f}B"
    elif value >= 1e6:
        return f"${value/1e6:.1f}M"
    else:
        return f"${value/1e3:.1f}K"
