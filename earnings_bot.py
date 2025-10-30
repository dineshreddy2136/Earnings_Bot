#!/usr/bin/env python3
"""
Earnings Bot - Fetches upcoming earnings data for companies using yfinance
"""

import json
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import concurrent.futures
import threading
import time
import numpy as np
from database import EarningsDatabase


class EarningsBot:
    def __init__(self):
        """Initialize the Earnings Bot"""
        self.earnings_data = []
        self.db = EarningsDatabase()
        self.lock = threading.Lock()  # For thread-safe operations
        
    def get_week_range(self, target_date=None):
        """
        Get the start and end dates for a given week
        
        Args:
            target_date: datetime object or None (defaults to current date)
            
        Returns:
            tuple: (start_date, end_date) for the week
        """
        if target_date is None:
            target_date = datetime.now()
            
        # Get Monday of the current week
        days_since_monday = target_date.weekday()
        start_date = target_date - timedelta(days=days_since_monday)
        end_date = start_date + timedelta(days=6)
        
        return start_date, end_date
    
    def load_tickers_from_json(self, filename='a.json'):
        """
        Load ticker symbols from JSON file (supports both old and new formats)
        
        Args:
            filename: JSON file containing ticker symbols
            
        Returns:
            list: List of stock symbols
        """
        try:
            with open(filename, 'r') as f:
                content = f.read().strip()
            
            # Try to parse as proper JSON first (new format)
            try:
                import json
                data = json.loads(content)
                
                # New organized format with categories
                if 'tickers' in data and isinstance(data['tickers'], dict):
                    all_symbols = []
                    for category, symbols in data['tickers'].items():
                        if isinstance(symbols, list):
                            all_symbols.extend(symbols)
                    
                    # Remove duplicates while preserving order
                    seen = set()
                    cleaned_symbols = []
                    for symbol in all_symbols:
                        symbol = symbol.upper().strip()
                        if symbol not in seen and re.match(r'^[A-Z0-9.]{1,6}$', symbol):
                            seen.add(symbol)
                            cleaned_symbols.append(symbol)
                    
                    print(f"Loaded {len(cleaned_symbols)} ticker symbols from organized {filename}")
                    return cleaned_symbols
                
                # Simple array format
                elif 'tickers' in data and isinstance(data['tickers'], list):
                    symbols = data['tickers']
                    cleaned_symbols = []
                    for symbol in symbols:
                        symbol = symbol.upper().strip()
                        if re.match(r'^[A-Z0-9.]{1,6}$', symbol):
                            cleaned_symbols.append(symbol)
                    
                    print(f"Loaded {len(cleaned_symbols)} ticker symbols from {filename}")
                    return cleaned_symbols
                    
            except json.JSONDecodeError:
                # Fall back to old text format parsing
                content = content.replace('{', '').replace('}', '')
                symbols = [symbol.strip() for symbol in content.split() if symbol.strip()]
                
                # Clean up symbols
                cleaned_symbols = []
                for symbol in symbols:
                    symbol = symbol.upper().strip()
                    # Support tickers with dots (like BRK.B)
                    if re.match(r'^[A-Z0-9.]{1,6}$', symbol):
                        cleaned_symbols.append(symbol)
                
                print(f"Loaded {len(cleaned_symbols)} ticker symbols from legacy {filename}")
                return cleaned_symbols
            
        except FileNotFoundError:
            print(f"File {filename} not found. Using fallback symbols.")
            return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
        except Exception as e:
            print(f"Error loading tickers from {filename}: {e}")
            return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
    
    def get_earnings_for_symbol(self, symbol):
        """
        Get earnings information for a specific stock symbol
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            
        Returns:
            dict: Earnings information or None if not available
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Get company info first
            info = ticker.info
            if not info or 'symbol' not in info:
                return None
                
            company_name = info.get('longName', info.get('shortName', symbol))
            
            # Try to get earnings calendar and timing
            earnings_calendar = None
            earnings_date = 'N/A'
            eps_estimate = 'N/A'
            revenue_estimate = 'N/A'
            earnings_time = 'N/A'  # Before Market Open (BMO) or After Market Close (AMC)
            
            # First try to get timing from earnings_dates (most reliable)
            try:
                earnings_dates_df = ticker.earnings_dates
                if earnings_dates_df is not None and not earnings_dates_df.empty:
                    # Get the most recent future earnings date
                    now = pd.Timestamp.now(tz='America/New_York')  # Match the timezone of earnings data
                    future_earnings = earnings_dates_df[earnings_dates_df.index >= now]
                    if not future_earnings.empty:
                        next_earnings_timestamp = future_earnings.index[0]
                        earnings_date = next_earnings_timestamp.strftime('%Y-%m-%d')
                        
                        # Extract timing from timestamp hour
                        hour = next_earnings_timestamp.hour
                        if hour < 9:  # Before 9 AM EST
                            earnings_time = 'BMO'  # Before Market Open
                        elif hour >= 16:  # 4 PM EST or later
                            earnings_time = 'AMC'  # After Market Close
                        else:
                            earnings_time = 'Market Hours'
                        
                        # Get EPS estimate
                        if 'EPS Estimate' in future_earnings.columns:
                            eps_est = future_earnings.iloc[0]['EPS Estimate']
                            if pd.notna(eps_est):
                                eps_estimate = float(eps_est)
                    
                    # If no future earnings, try the most recent past earnings for timing pattern
                    elif not earnings_dates_df.empty:
                        recent_earnings = earnings_dates_df.iloc[0]  # Most recent
                        recent_timestamp = earnings_dates_df.index[0]
                        hour = recent_timestamp.hour
                        if hour < 9:
                            earnings_time = 'BMO'
                        elif hour >= 16:
                            earnings_time = 'AMC'
                        else:
                            earnings_time = 'Market Hours'
            except Exception as e:
                print(f"Could not get earnings_dates for {symbol}: {e}")
            
            # Fallback to calendar method
            try:
                earnings_calendar = ticker.calendar
                
                # Handle different calendar formats - only as fallback
                if earnings_calendar is not None:
                    # Check if it's a dictionary (new format)
                    if isinstance(earnings_calendar, dict):
                        earnings_dates = earnings_calendar.get('Earnings Date', [])
                        if earnings_dates and len(earnings_dates) > 0 and earnings_date == 'N/A':
                            # Get the first/next earnings date only if we don't have one
                            next_date = earnings_dates[0]
                            if hasattr(next_date, 'strftime'):
                                earnings_date = next_date.strftime('%Y-%m-%d')
                            else:
                                earnings_date = str(next_date)
                        
                        # Always try to get EPS and Revenue estimates from calendar
                        if eps_estimate == 'N/A':
                            eps_estimate = earnings_calendar.get('Earnings Average', 'N/A')
                        revenue_estimate = earnings_calendar.get('Revenue Average', 'N/A')
                    
                    # Check if it's a DataFrame (old format) - only as fallback
                    elif hasattr(earnings_calendar, 'empty') and not earnings_calendar.empty:
                        next_earnings_date = earnings_calendar.index[0] if len(earnings_calendar.index) > 0 else None
                        if next_earnings_date and earnings_date == 'N/A':
                            earnings_date = next_earnings_date.strftime('%Y-%m-%d')
                        
                        # Try to get EPS and Revenue estimates from DataFrame
                        try:
                            if len(earnings_calendar.columns) > 0 and len(earnings_calendar) > 0:
                                # EPS estimate (usually first column)
                                if eps_estimate == 'N/A':
                                    eps_est = earnings_calendar.iloc[0, 0]
                                    if pd.notna(eps_est):
                                        eps_estimate = float(eps_est)
                                
                                # Revenue estimate (usually second column if available)
                                if len(earnings_calendar.columns) > 1:
                                    rev_est = earnings_calendar.iloc[0, 1]
                                    if pd.notna(rev_est):
                                        revenue_estimate = float(rev_est)
                        except:
                            pass
                
            except Exception as cal_error:
                print(f"No earnings calendar available for {symbol}: {cal_error}")
            
            # Try to get additional estimates and timing from info
            try:
                # Get revenue estimate from analyst estimates if available
                if revenue_estimate == 'N/A':
                    analysts = info.get('financialData', {})
                    revenue_growth = analysts.get('revenueGrowth')
                    current_revenue = info.get('totalRevenue')
                    if revenue_growth and current_revenue:
                        estimated_revenue = current_revenue * (1 + revenue_growth)
                        revenue_estimate = estimated_revenue
            except:
                pass
            
            # Create earnings info regardless of whether we have earnings date
            earnings_info = {
                'symbol': symbol,
                'company_name': company_name,
                'earnings_date': earnings_date,
                'earnings_time': earnings_time,
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 'N/A'),
                'current_price': info.get('currentPrice', info.get('regularMarketPrice', 'N/A')),
                'eps_estimate': eps_estimate,
                'revenue_estimate': revenue_estimate
            }
            
            return earnings_info
                    
        except Exception as e:
            print(f"Error getting data for {symbol}: {e}")
            
        return None
    
    def get_earnings_for_symbol_with_retry(self, symbol, max_retries=3, delay=1):
        """
        Get earnings information with retry logic and rate limiting
        
        Args:
            symbol: Stock symbol
            max_retries: Maximum number of retries
            delay: Delay between retries in seconds
            
        Returns:
            dict: Earnings information or None
        """
        for attempt in range(max_retries):
            try:
                # Add small delay to avoid rate limiting
                if attempt > 0:
                    time.sleep(delay * attempt)
                
                result = self.get_earnings_for_symbol(symbol)
                return result
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for {symbol}: {e}")
                if attempt == max_retries - 1:
                    print(f"All attempts failed for {symbol}")
                    return None
                time.sleep(delay)
        
        return None
    
    def fetch_earnings_parallel(self, symbols, max_workers=10, progress_callback=None):
        """
        Fetch earnings data for multiple symbols in parallel
        
        Args:
            symbols: List of stock symbols
            max_workers: Maximum number of concurrent threads
            progress_callback: Optional callback function for progress updates
            
        Returns:
            list: List of earnings data
        """
        earnings_data = []
        completed_count = 0
        total_count = len(symbols)
        
        print(f"Starting parallel processing of {total_count} symbols with {max_workers} workers...")
        
        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_symbol = {
                executor.submit(self.get_earnings_for_symbol_with_retry, symbol): symbol 
                for symbol in symbols
            }
            
            # Process completed tasks
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                completed_count += 1
                
                try:
                    result = future.result(timeout=30)  # 30 second timeout per request
                    if result:
                        with self.lock:  # Thread-safe append
                            earnings_data.append(result)
                        
                        print(f"✅ {symbol} ({completed_count}/{total_count}) - Success")
                    else:
                        print(f"❌ {symbol} ({completed_count}/{total_count}) - No data")
                    
                    # Call progress callback if provided
                    if progress_callback:
                        progress_callback(completed_count, total_count, symbol)
                        
                except Exception as e:
                    print(f"❌ {symbol} ({completed_count}/{total_count}) - Error: {e}")
        
        print(f"Parallel processing complete! Got data for {len(earnings_data)} out of {total_count} symbols")
        return earnings_data
    
    def get_next_earnings_date(self, symbol):
        """Helper method to get next earnings date for a symbol"""
        try:
            earnings_info = self.get_earnings_for_symbol(symbol)
            return earnings_info.get('earnings_date', 'N/A') if earnings_info else 'N/A'
        except:
            return 'N/A'
    
    def get_options_iv_data(self, symbol):
        """
        Get implied volatility and expected move data for earnings plays
        
        Args:
            symbol: Stock symbol
            
        Returns:
            dict: IV data including expected move
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Get current stock price
            info = ticker.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice'))
            if not current_price:
                return None
                
            # Get options expiration dates
            exp_dates = ticker.options
            if not exp_dates:
                return None
                
            # Find the closest expiration after earnings date
            earnings_date = self.get_next_earnings_date(symbol)
            if earnings_date == 'N/A':
                # Use the nearest expiration
                nearest_exp = exp_dates[0]
            else:
                earnings_dt = datetime.strptime(earnings_date, '%Y-%m-%d')
                
                # Check if earnings date is in the past
                today = datetime.now().date()
                if earnings_dt.date() <= today:
                    print(f"Warning: {symbol} has past earnings date ({earnings_date}). IV analysis not relevant for completed earnings.")
                    # Still continue processing but with warning
                nearest_exp = None
                for exp_date in exp_dates:
                    exp_dt = datetime.strptime(exp_date, '%Y-%m-%d')
                    if exp_dt >= earnings_dt:
                        nearest_exp = exp_date
                        break
                if not nearest_exp:
                    nearest_exp = exp_dates[0]
            
            # Get options chain for the expiration
            options_chain = ticker.option_chain(nearest_exp)
            calls = options_chain.calls
            puts = options_chain.puts
            
            if calls.empty or puts.empty:
                return None
                
            # Find At-The-Money (ATM) options
            atm_call = calls.iloc[(calls['strike'] - current_price).abs().argsort()[:1]]
            atm_put = puts.iloc[(puts['strike'] - current_price).abs().argsort()[:1]]
            
            if atm_call.empty or atm_put.empty:
                return None
                
            # Get implied volatilities
            call_iv = atm_call['impliedVolatility'].iloc[0] * 100  # Convert to percentage
            put_iv = atm_put['impliedVolatility'].iloc[0] * 100
            avg_iv = (call_iv + put_iv) / 2
            
            # Calculate expected move using straddle pricing
            call_price = atm_call['lastPrice'].iloc[0]
            put_price = atm_put['lastPrice'].iloc[0]
            straddle_price = call_price + put_price
            
            # Expected move = Straddle price / Stock price * 100
            expected_move_percent = (straddle_price / current_price) * 100
            expected_move_dollar = straddle_price
            
            # Calculate days to expiration
            exp_dt = datetime.strptime(nearest_exp, '%Y-%m-%d')
            days_to_exp = (exp_dt - datetime.now()).days
            
            # Get historical volatility for comparison
            hist_data = ticker.history(period="30d")
            if not hist_data.empty:
                returns = hist_data['Close'].pct_change().dropna()
                historical_vol = returns.std() * np.sqrt(252) * 100  # Annualized
            else:
                historical_vol = None
                
            return {
                'symbol': symbol,
                'current_price': round(current_price, 2),
                'expiration_date': nearest_exp,
                'days_to_expiration': days_to_exp,
                'implied_volatility': round(avg_iv, 2),
                'call_iv': round(call_iv, 2),
                'put_iv': round(put_iv, 2),
                'historical_volatility': round(historical_vol, 2) if historical_vol else None,
                'iv_rank': round((avg_iv - historical_vol), 2) if historical_vol else None,
                'expected_move_percent': round(expected_move_percent, 2),
                'expected_move_dollar': round(expected_move_dollar, 2),
                'expected_move_up': round(current_price + expected_move_dollar, 2),
                'expected_move_down': round(current_price - expected_move_dollar, 2),
                'straddle_price': round(straddle_price, 2),
                'atm_strike': atm_call['strike'].iloc[0],
                'earnings_date': earnings_date
            }
            
        except Exception as e:
            print(f"Error getting IV data for {symbol}: {e}")
            return None

    def get_iv_crush_estimate(self, symbol):
        """
        Estimate potential IV crush after earnings
        
        Args:
            symbol: Stock symbol
            
        Returns:
            dict: IV crush estimates
        """
        try:
            # Get current IV data
            iv_data = self.get_options_iv_data(symbol)
            if not iv_data:
                return None
                
            current_iv = iv_data['implied_volatility']
            historical_vol = iv_data['historical_volatility']
            
            if not historical_vol:
                # Use industry average if no historical data
                historical_vol = 25  # Rough market average
                
            # Estimate post-earnings IV (typically drops to near historical vol)
            post_earnings_iv = historical_vol * 1.1  # Usually slightly above historical
            
            # Calculate IV crush
            iv_crush_percent = ((current_iv - post_earnings_iv) / current_iv) * 100
            
            # Estimate option value impact (rough approximation)
            # Options typically lose 20-50% of value due to IV crush
            option_value_loss = min(50, max(20, iv_crush_percent * 0.8))
            
            return {
                'symbol': symbol,
                'pre_earnings_iv': round(current_iv, 2),
                'estimated_post_earnings_iv': round(post_earnings_iv, 2),
                'iv_crush_percent': round(iv_crush_percent, 2),
                'estimated_option_value_loss': round(option_value_loss, 2)
            }
            
        except Exception as e:
            print(f"Error calculating IV crush for {symbol}: {e}")
            return None
    
    def filter_earnings_by_week(self, start_date, end_date):
        """
        Filter earnings data to only include companies with earnings in the specified week
        
        Args:
            start_date: Start date of the week
            end_date: End date of the week
            
        Returns:
            list: Filtered earnings data
        """
        filtered_earnings = []
        
        for earning in self.earnings_data:
            try:
                if earning['earnings_date'] == 'N/A':
                    continue  # Skip companies without earnings dates
                    
                earnings_date = datetime.strptime(earning['earnings_date'], '%Y-%m-%d')
                if start_date.date() <= earnings_date.date() <= end_date.date():
                    filtered_earnings.append(earning)
            except Exception as e:
                print(f"Error filtering earnings date for {earning.get('symbol', 'unknown')}: {e}")
                
        return filtered_earnings
    
    def fetch_weekly_earnings(self, target_date=None, use_parallel=True, max_workers=10):
        """
        Fetch all companies with earnings for a specific week
        
        Args:
            target_date: datetime object or None (defaults to current week)
            use_parallel: Whether to use parallel processing
            max_workers: Maximum number of concurrent threads
            
        Returns:
            dict: Dictionary with earnings data and metadata
        """
        print("Starting earnings data collection...")
        
        print("Starting earnings data collection...")
        start_time = time.time()
        
        # Get week range
        start_date, end_date = self.get_week_range(target_date)
        print(f"Fetching earnings for week: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Get symbols from JSON file
        symbols = self.load_tickers_from_json()
        print(f"Retrieved {len(symbols)} stock symbols")
        
        # Fetch earnings data (parallel or sequential)
        if use_parallel:
            print(f"Using parallel processing with {max_workers} workers...")
            self.earnings_data = self.fetch_earnings_parallel(symbols, max_workers)
        else:
            print("Using sequential processing...")
            self.earnings_data = []
            for i, symbol in enumerate(symbols):
                print(f"Processing {symbol} ({i+1}/{len(symbols)})")
                earnings_info = self.get_earnings_for_symbol(symbol)
                if earnings_info:
                    self.earnings_data.append(earnings_info)
        
        elapsed_time = time.time() - start_time
        print(f"Data collection completed in {elapsed_time:.2f} seconds")
        
        # Filter by week
        weekly_earnings = self.filter_earnings_by_week(start_date, end_date)
        
        # Prepare final data structure
        result = {
            'week_start': start_date.strftime('%Y-%m-%d'),
            'week_end': end_date.strftime('%Y-%m-%d'),
            'total_companies_checked': len(symbols),
            'companies_with_earnings_data': len(self.earnings_data),
            'companies_with_earnings_this_week': len(weekly_earnings),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'earnings_data': weekly_earnings
        }
        
        return result
    
    def save_to_json(self, data, filename='weekly_earnings.json'):
        """
        Save earnings data to JSON file
        
        Args:
            data: Dictionary containing earnings data
            filename: Output filename
        """
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"Earnings data saved to {filename}")
        except Exception as e:
            print(f"Error saving to JSON: {e}")


def main():
    """Main function to run the earnings bot"""
    bot = EarningsBot()
    
    # Fetch weekly earnings data
    earnings_data = bot.fetch_weekly_earnings()
    
    # Print summary
    print(f"\n=== EARNINGS SUMMARY ===")
    print(f"Week: {earnings_data['week_start']} to {earnings_data['week_end']}")
    print(f"Companies checked: {earnings_data['total_companies_checked']}")
    print(f"Companies with earnings data: {earnings_data['companies_with_earnings_data']}")
    print(f"Companies with earnings this week: {earnings_data['companies_with_earnings_this_week']}")
    
    # Print companies with earnings this week
    if earnings_data['earnings_data']:
        print(f"\nCompanies with earnings this week:")
        for company in earnings_data['earnings_data']:
            print(f"- {company['symbol']} ({company['company_name']}) - {company['earnings_date']}")
    else:
        print("\nNo companies found with earnings this week from the checked symbols.")
    
        # Save to database
        if bot.earnings_data:
            inserted_count = bot.db.insert_earnings_data(bot.earnings_data)
            print(f"Inserted/updated {inserted_count} records in database")
        
        return earnings_data
if __name__ == "__main__":
    main()