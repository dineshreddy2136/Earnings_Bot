"""Weekly Earnings Calendar Page"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.data_access import get_weekly_earnings_data
from utils.date_helpers import get_week_dates, get_week_label
from utils.formatters import format_market_cap, format_revenue_estimate


def weekly_earnings_calendar(week_offset):
    """Weekly earnings calendar page"""
    st.header("📅 Weekly Earnings Calendar")
    
    # Get current week dates
    week_start, week_end = get_week_dates(week_offset)
    week_label = get_week_label(week_offset)
    
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
                        
                        # Format revenue estimate
                        revenue_display = format_revenue_estimate(company.get('revenue_estimate', 'N/A'))
                        
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
