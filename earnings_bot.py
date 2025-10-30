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
from database import EarningsDatabase


class EarningsBot:
    def __init__(self):
        """Initialize the Earnings Bot"""
        self.earnings_data = []
        self.db = EarningsDatabase()
        
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
            
            # Try to get earnings calendar
            earnings_calendar = None
            earnings_date = 'N/A'
            eps_estimate = 'N/A'
            revenue_estimate = 'N/A'
            
            try:
                earnings_calendar = ticker.calendar
                
                # Handle different calendar formats
                if earnings_calendar is not None:
                    # Check if it's a dictionary (new format)
                    if isinstance(earnings_calendar, dict):
                        earnings_dates = earnings_calendar.get('Earnings Date', [])
                        if earnings_dates and len(earnings_dates) > 0:
                            # Get the first/next earnings date
                            next_date = earnings_dates[0]
                            if hasattr(next_date, 'strftime'):
                                earnings_date = next_date.strftime('%Y-%m-%d')
                            else:
                                earnings_date = str(next_date)
                            
                            # Try to get EPS and Revenue estimates
                            eps_estimate = earnings_calendar.get('Earnings Average', 'N/A')
                            revenue_estimate = earnings_calendar.get('Revenue Average', 'N/A')
                    
                    # Check if it's a DataFrame (old format)
                    elif hasattr(earnings_calendar, 'empty') and not earnings_calendar.empty:
                        next_earnings_date = earnings_calendar.index[0] if len(earnings_calendar.index) > 0 else None
                        if next_earnings_date:
                            earnings_date = next_earnings_date.strftime('%Y-%m-%d')
                            
                            # Try to get EPS and Revenue estimates from DataFrame
                            try:
                                if len(earnings_calendar.columns) > 0 and len(earnings_calendar) > 0:
                                    # EPS estimate (usually first column)
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
            
            # Try to get additional analyst estimates from info
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
    
    def fetch_weekly_earnings(self, target_date=None):
        """
        Fetch all companies with earnings for a specific week
        
        Args:
            target_date: datetime object or None (defaults to current week)
            
        Returns:
            dict: Dictionary with earnings data and metadata
        """
        print("Starting earnings data collection...")
        
        # Get week range
        start_date, end_date = self.get_week_range(target_date)
        print(f"Fetching earnings for week: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Get symbols from JSON file
        symbols = self.load_tickers_from_json()
        print(f"Retrieved {len(symbols)} stock symbols")
        
        # Fetch earnings data for each symbol
        self.earnings_data = []
        for i, symbol in enumerate(symbols):
            print(f"Processing {symbol} ({i+1}/{len(symbols)})")
            earnings_info = self.get_earnings_for_symbol(symbol)
            if earnings_info:
                self.earnings_data.append(earnings_info)
        
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