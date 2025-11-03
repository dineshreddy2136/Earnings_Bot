"""
Earnings Data Sync - Earnings Bot

Fetches earnings and options data from yfinance and syncs to Firestore
"""

import yfinance as yf
from datetime import datetime, timedelta
import logging
import time
import numpy as np
from typing import List, Dict, Optional
from firestore_db import FirestoreDB

logger = logging.getLogger(__name__)


class EarningsSync:
    """Sync earnings and options data from yfinance to Firestore"""
    
    def __init__(self, db: FirestoreDB):
        """
        Initialize earnings sync
        
        Args:
            db: FirestoreDB instance
        """
        self.db = db
        
        # Major tickers to sync (you can expand this list)
        self.major_tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'AMD',
            'NFLX', 'DIS', 'COST', 'WMT', 'JPM', 'BAC', 'V', 'MA',
            'JNJ', 'PG', 'KO', 'PEP', 'MCD', 'NKE', 'SBUX', 'HD',
            'BA', 'CAT', 'GE', 'MMM', '3M', 'HON', 'UNP', 'UPS'
        ]
    
    def sync_all_earnings(self) -> Dict:
        """
        Sync earnings data for all major tickers
        
        Returns:
            dict: Sync summary
        """
        logger.info(f"Starting sync for {len(self.major_tickers)} tickers...")
        
        earnings_data = []
        errors = 0
        
        for i, symbol in enumerate(self.major_tickers):
            try:
                logger.info(f"[{i+1}/{len(self.major_tickers)}] Fetching {symbol}...")
                
                earnings_info = self.get_earnings_for_symbol(symbol)
                
                if earnings_info:
                    earnings_data.append(earnings_info)
                    logger.info(f"  ✅ {symbol}: {earnings_info.get('earnings_date', 'N/A')}")
                else:
                    logger.warning(f"  ⚠️ {symbol}: No data")
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"  ❌ {symbol}: {str(e)}")
                errors += 1
        
        # Upsert to Firestore
        if earnings_data:
            result = self.db.upsert_earnings(earnings_data)
            result['errors'] += errors
            return {
                'total_synced': result['total'],
                'new_records': result['new_records'],
                'updated_records': result['updated_records'],
                'errors': result['errors']
            }
        
        return {
            'total_synced': 0,
            'new_records': 0,
            'updated_records': 0,
            'errors': errors
        }
    
    def get_earnings_for_symbol(self, symbol: str) -> Optional[Dict]:
        """
        Get earnings information for a specific symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            dict: Earnings info or None
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or 'symbol' not in info:
                return None
            
            company_name = info.get('longName', info.get('shortName', symbol))
            earnings_date = 'N/A'
            earnings_time = 'N/A'
            eps_estimate = None
            revenue_estimate = None
            
            # Get earnings date and timing
            try:
                earnings_dates_df = ticker.earnings_dates
                if earnings_dates_df is not None and not earnings_dates_df.empty:
                    import pandas as pd
                    now = pd.Timestamp.now(tz='America/New_York')
                    future_earnings = earnings_dates_df[earnings_dates_df.index >= now]
                    
                    if not future_earnings.empty:
                        next_earnings_timestamp = future_earnings.index[0]
                        earnings_date = next_earnings_timestamp.strftime('%Y-%m-%d')
                        
                        # Determine timing (BMO/AMC)
                        hour = next_earnings_timestamp.hour
                        if hour < 9:
                            earnings_time = 'BMO'
                        elif hour >= 16:
                            earnings_time = 'AMC'
                        else:
                            earnings_time = 'Market Hours'
                        
                        # Get EPS estimate
                        if 'EPS Estimate' in future_earnings.columns:
                            eps_est = future_earnings.iloc[0]['EPS Estimate']
                            if pd.notna(eps_est):
                                eps_estimate = float(eps_est)
            except Exception as e:
                logger.debug(f"Could not get earnings_dates for {symbol}: {e}")
            
            # Try calendar as fallback
            try:
                earnings_calendar = ticker.calendar
                if earnings_calendar is not None and isinstance(earnings_calendar, dict):
                    if earnings_date == 'N/A':
                        earnings_dates = earnings_calendar.get('Earnings Date', [])
                        if earnings_dates and len(earnings_dates) > 0:
                            next_date = earnings_dates[0]
                            if hasattr(next_date, 'strftime'):
                                earnings_date = next_date.strftime('%Y-%m-%d')
                    
                    if eps_estimate is None:
                        eps_estimate = earnings_calendar.get('Earnings Average')
                    
                    revenue_estimate = earnings_calendar.get('Revenue Average')
            except:
                pass
            
            return {
                'symbol': symbol,
                'company_name': company_name,
                'earnings_date': earnings_date,
                'earnings_time': earnings_time,
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap'),
                'current_price': info.get('currentPrice', info.get('regularMarketPrice')),
                'eps_estimate': eps_estimate,
                'revenue_estimate': revenue_estimate
            }
            
        except Exception as e:
            logger.error(f"Error getting earnings for {symbol}: {e}")
            return None
    
    def sync_options_data(self, days_ahead: int = 60) -> Dict:
        """
        Sync options IV data for upcoming earnings
        
        Args:
            days_ahead: Sync options for earnings within this many days
            
        Returns:
            dict: Sync summary
        """
        logger.info(f"Syncing options data for upcoming earnings ({days_ahead} days)...")
        
        # Get upcoming earnings
        upcoming = self.db.get_upcoming_earnings(days_ahead)
        symbols = [e['symbol'] for e in upcoming]
        
        logger.info(f"Found {len(symbols)} symbols with upcoming earnings")
        
        options_data = []
        errors = 0
        
        for i, symbol in enumerate(symbols):
            try:
                logger.info(f"[{i+1}/{len(symbols)}] Fetching options for {symbol}...")
                
                iv_data = self.get_options_iv_data(symbol)
                
                if iv_data:
                    options_data.append(iv_data)
                    logger.info(f"  ✅ {symbol}: IV={iv_data.get('implied_volatility', 'N/A')}%")
                else:
                    logger.warning(f"  ⚠️ {symbol}: No options data")
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"  ❌ {symbol}: {str(e)}")
                errors += 1
        
        # Upsert to Firestore
        if options_data:
            result = self.db.upsert_options_data(options_data)
            result['errors'] += errors
            return {
                'total_synced': result['total'],
                'errors': result['errors']
            }
        
        return {
            'total_synced': 0,
            'errors': errors
        }
    
    def get_options_iv_data(self, symbol: str) -> Optional[Dict]:
        """
        Get implied volatility and expected move data
        
        Args:
            symbol: Stock symbol
            
        Returns:
            dict: IV data or None
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice'))
            
            if not current_price:
                return None
            
            # Get options expiration dates
            exp_dates = ticker.options
            if not exp_dates:
                return None
            
            # Use nearest expiration
            nearest_exp = exp_dates[0]
            
            # Get options chain
            options_chain = ticker.option_chain(nearest_exp)
            calls = options_chain.calls
            puts = options_chain.puts
            
            if calls.empty or puts.empty:
                return None
            
            # Find ATM options
            atm_call = calls.iloc[(calls['strike'] - current_price).abs().argsort()[:1]]
            atm_put = puts.iloc[(puts['strike'] - current_price).abs().argsort()[:1]]
            
            if atm_call.empty or atm_put.empty:
                return None
            
            # Get implied volatilities
            call_iv = atm_call['impliedVolatility'].iloc[0] * 100
            put_iv = atm_put['impliedVolatility'].iloc[0] * 100
            avg_iv = (call_iv + put_iv) / 2
            
            # Calculate expected move
            call_price = atm_call['lastPrice'].iloc[0]
            put_price = atm_put['lastPrice'].iloc[0]
            straddle_price = call_price + put_price
            
            expected_move_percent = (straddle_price / current_price) * 100
            expected_move_dollar = straddle_price
            
            # Calculate days to expiration
            exp_dt = datetime.strptime(nearest_exp, '%Y-%m-%d')
            days_to_exp = (exp_dt - datetime.now()).days
            
            # Get IV percentile (simplified - using 30-day historical vol as proxy)
            try:
                hist_data = ticker.history(period="1y")
                if not hist_data.empty:
                    returns = hist_data['Close'].pct_change().dropna()
                    rolling_vol = returns.rolling(window=30).std() * np.sqrt(252) * 100
                    rolling_vol = rolling_vol.dropna()
                    
                    if len(rolling_vol) > 0:
                        iv_percentile = (rolling_vol < avg_iv).sum() / len(rolling_vol) * 100
                    else:
                        iv_percentile = None
                else:
                    iv_percentile = None
            except:
                iv_percentile = None
            
            return {
                'symbol': symbol,
                'current_price': round(current_price, 2),
                'expiration_date': nearest_exp,
                'days_to_expiration': days_to_exp,
                'implied_volatility': round(avg_iv, 2),
                'call_iv': round(call_iv, 2),
                'put_iv': round(put_iv, 2),
                'iv_percentile': round(iv_percentile, 2) if iv_percentile else None,
                'expected_move_percent': round(expected_move_percent, 2),
                'expected_move_dollar': round(expected_move_dollar, 2),
                'expected_move_up': round(current_price + expected_move_dollar, 2),
                'expected_move_down': round(current_price - expected_move_dollar, 2),
                'straddle_price': round(straddle_price, 2),
                'atm_strike': atm_call['strike'].iloc[0]
            }
            
        except Exception as e:
            logger.error(f"Error getting IV data for {symbol}: {e}")
            return None
