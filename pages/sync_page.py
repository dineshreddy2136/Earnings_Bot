"""Data Synchronization Page"""
import streamlit as st
from earnings_bot import EarningsBot
from utils.data_access import get_database_stats


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
        _full_sync_section()
    
    with col2:
        _quick_sync_section()


def _full_sync_section():
    """Full data sync section"""
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


def _quick_sync_section():
    """Quick sync section"""
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
