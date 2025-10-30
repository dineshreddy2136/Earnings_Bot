"""Options Data Sync Component"""
import streamlit as st
from datetime import datetime, timedelta
from earnings_bot import EarningsBot
from utils.data_access import init_database


def sync_options_data():
    """Sync options IV data for stocks with upcoming earnings only"""
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
        symbols_to_sync, period_name = _custom_selection()
    else:
        symbols_to_sync, period_name = _time_based_selection(sync_option, today)

    # --- Step 2: Confirmation and Execution ---
    if not symbols_to_sync:
        st.warning("No symbols selected or found for the chosen period. Please adjust your selection.")
        return

    _confirmation_and_execution(symbols_to_sync, period_name)


def _custom_selection():
    """Handle custom symbol selection"""
    all_symbols = EarningsBot().load_tickers_from_json()
    selected_symbols = st.multiselect(
        "Select specific symbols (only those with upcoming earnings are useful):",
        all_symbols,
        default=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA"],
        key="custom_symbols_select"
    )
    if selected_symbols:
        return selected_symbols, f"{len(selected_symbols)} selected symbols"
    return [], ""


def _time_based_selection(sync_option, today):
    """Handle time-based selection"""
    if sync_option == "This Week":
        start_date, end_date = today, today + timedelta(days=6 - today.weekday())
        period_name = "this week"
    elif sync_option == "Next 7 Days":
        start_date, end_date = today, today + timedelta(days=7)
        period_name = "the next 7 days"
    elif sync_option == "Next 14 Days":
        start_date, end_date = today, today + timedelta(days=14)
        period_name = "the next 14 days"
    else:  # "Next 30 Days"
        start_date, end_date = today, today + timedelta(days=30)
        period_name = "the next 30 days"
    
    st.info(f"📅 Selected period: {start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}")
    database = init_database()
    earnings_data = database.get_earnings_by_week(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    
    # Filter out past earnings from the selection
    earnings_data = earnings_data[earnings_data['earnings_date'] >= today.strftime('%Y-%m-%d')]

    if not earnings_data.empty:
        symbols_to_sync = earnings_data['symbol'].unique().tolist()
        return symbols_to_sync, period_name
    
    return [], period_name


def _confirmation_and_execution(symbols_to_sync, period_name):
    """Display confirmation and execute sync"""
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
        _execute_sync(symbols_to_sync)


def _execute_sync(symbols_to_sync):
    """Execute the sync operation"""
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
