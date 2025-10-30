#!/usr/bin/env python3
"""
Database handler for Earnings Bot - SQLite operations
"""

import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import os


class EarningsDatabase:
    def __init__(self, db_path='earnings.db'):
        """Initialize database connection and create tables if they don't exist"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create the earnings table if it doesn't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create earnings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS earnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    company_name TEXT,
                    earnings_date TEXT,
                    earnings_time TEXT,
                    sector TEXT,
                    industry TEXT,
                    market_cap INTEGER,
                    current_price REAL,
                    eps_estimate REAL,
                    revenue_estimate REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, earnings_date)
                )
            ''')
            
            # Check if revenue_estimate column exists, if not add it (for existing databases)
            try:
                cursor.execute("SELECT revenue_estimate FROM earnings LIMIT 1")
            except sqlite3.OperationalError:
                # Column doesn't exist, add it
                cursor.execute("ALTER TABLE earnings ADD COLUMN revenue_estimate REAL")
                print("Added revenue_estimate column to existing database")
            
            # Check if earnings_time column exists, if not add it (for existing databases)
            try:
                cursor.execute("SELECT earnings_time FROM earnings LIMIT 1")
            except sqlite3.OperationalError:
                # Column doesn't exist, add it
                cursor.execute("ALTER TABLE earnings ADD COLUMN earnings_time TEXT")
                print("Added earnings_time column to existing database")
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_earnings_date 
                ON earnings(earnings_date)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_symbol 
                ON earnings(symbol)
            ''')
            
            # Create options table for IV data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS options_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    current_price REAL,
                    expiration_date TEXT,
                    days_to_expiration INTEGER,
                    implied_volatility REAL,
                    call_iv REAL,
                    put_iv REAL,
                    historical_volatility REAL,
                    iv_rank REAL,
                    expected_move_percent REAL,
                    expected_move_dollar REAL,
                    expected_move_up REAL,
                    expected_move_down REAL,
                    straddle_price REAL,
                    atm_strike REAL,
                    iv_crush_percent REAL,
                    estimated_option_value_loss REAL,
                    earnings_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, expiration_date)
                )
            ''')
            
            # Create index for options table
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_options_symbol 
                ON options_data(symbol)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_options_exp_date 
                ON options_data(expiration_date)
            ''')
            
            conn.commit()
    
    def insert_earnings_data(self, earnings_list: List[Dict]) -> int:
        """
        Insert or update earnings data
        
        Args:
            earnings_list: List of earnings dictionaries
            
        Returns:
            Number of records inserted/updated
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            inserted_count = 0
            
            for earning in earnings_list:
                try:
                    # Convert market_cap to integer if it's not 'N/A'
                    market_cap = None
                    if earning.get('market_cap') != 'N/A' and earning.get('market_cap') is not None:
                        try:
                            market_cap = int(earning['market_cap'])
                        except (ValueError, TypeError):
                            market_cap = None
                    
                    # Convert current_price to float if it's not 'N/A'
                    current_price = None
                    if earning.get('current_price') != 'N/A' and earning.get('current_price') is not None:
                        try:
                            current_price = float(earning['current_price'])
                        except (ValueError, TypeError):
                            current_price = None
                    
                    # Convert eps_estimate to float if it's not 'N/A'
                    eps_estimate = None
                    if earning.get('eps_estimate') != 'N/A' and earning.get('eps_estimate') is not None:
                        try:
                            eps_estimate = float(earning['eps_estimate'])
                        except (ValueError, TypeError):
                            eps_estimate = None
                    
                    # Convert revenue_estimate to float if it's not 'N/A'
                    revenue_estimate = None
                    if earning.get('revenue_estimate') != 'N/A' and earning.get('revenue_estimate') is not None:
                        try:
                            revenue_estimate = float(earning['revenue_estimate'])
                        except (ValueError, TypeError):
                            revenue_estimate = None
                    
                    # Allow entries with 'N/A' earnings dates for company info storage
                    # if earning.get('earnings_date') == 'N/A':
                    #     continue
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO earnings 
                        (symbol, company_name, earnings_date, earnings_time, sector, industry, 
                         market_cap, current_price, eps_estimate, revenue_estimate, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (
                        earning.get('symbol'),
                        earning.get('company_name'),
                        earning.get('earnings_date'),
                        earning.get('earnings_time'),
                        earning.get('sector'),
                        earning.get('industry'),
                        market_cap,
                        current_price,
                        eps_estimate,
                        revenue_estimate
                    ))
                    
                    inserted_count += 1
                    
                except Exception as e:
                    print(f"Error inserting data for {earning.get('symbol', 'unknown')}: {e}")
                    continue
            
            conn.commit()
            return inserted_count
    
    def get_earnings_by_date_range(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Get earnings data for a specific date range
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            DataFrame with earnings data
        """
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT symbol, company_name, earnings_date, earnings_time, sector, industry,
                       market_cap, current_price, eps_estimate, revenue_estimate, updated_at
                FROM earnings 
                WHERE earnings_date BETWEEN ? AND ?
                ORDER BY earnings_date, symbol
            '''
            return pd.read_sql_query(query, conn, params=(start_date, end_date))
    
    def get_earnings_by_week(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Get earnings data for a specific week
        
        Args:
            start_date: Week start date (YYYY-MM-DD)
            end_date: Week end date (YYYY-MM-DD)
            
        Returns:
            DataFrame with earnings data
        """
        return self.get_earnings_by_date_range(start_date, end_date)
    
    def get_all_earnings(self) -> pd.DataFrame:
        """Get all earnings data"""
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT symbol, company_name, earnings_date, earnings_time, sector, industry,
                       market_cap, current_price, eps_estimate, revenue_estimate, updated_at
                FROM earnings 
                ORDER BY CASE WHEN earnings_date = 'N/A' THEN 1 ELSE 0 END, earnings_date DESC, symbol
            '''
            return pd.read_sql_query(query, conn)
    
    def get_earnings_by_symbol(self, symbol: str) -> pd.DataFrame:
        """
        Get earnings data for a specific symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            DataFrame with earnings data for the symbol
        """
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT symbol, company_name, earnings_date, earnings_time, sector, industry,
                       market_cap, current_price, eps_estimate, revenue_estimate, updated_at
                FROM earnings 
                WHERE symbol = ?
                ORDER BY earnings_date DESC
            '''
            return pd.read_sql_query(query, conn, params=(symbol,))
    
    def get_upcoming_earnings(self, days_ahead: int = 30) -> pd.DataFrame:
        """
        Get upcoming earnings within specified days
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            DataFrame with upcoming earnings
        """
        from datetime import date, timedelta
        
        today = date.today()
        future_date = today + timedelta(days=days_ahead)
        
        return self.get_earnings_by_date_range(
            today.strftime('%Y-%m-%d'),
            future_date.strftime('%Y-%m-%d')
        )
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total companies
            cursor.execute('SELECT COUNT(DISTINCT symbol) FROM earnings')
            total_companies = cursor.fetchone()[0]
            
            # Total earnings records
            cursor.execute('SELECT COUNT(*) FROM earnings WHERE earnings_date != "N/A"')
            total_earnings = cursor.fetchone()[0]
            
            # Companies with upcoming earnings (next 30 days)
            from datetime import date, timedelta
            today = date.today()
            future_date = today + timedelta(days=30)
            
            cursor.execute('''
                SELECT COUNT(DISTINCT symbol) FROM earnings 
                WHERE earnings_date BETWEEN ? AND ?
            ''', (today.strftime('%Y-%m-%d'), future_date.strftime('%Y-%m-%d')))
            upcoming_companies = cursor.fetchone()[0]
            
            # Last update
            cursor.execute('SELECT MAX(updated_at) FROM earnings')
            last_update = cursor.fetchone()[0]
            
            # Sectors
            cursor.execute('''
                SELECT sector, COUNT(DISTINCT symbol) as count 
                FROM earnings 
                WHERE sector != 'N/A' AND sector IS NOT NULL
                GROUP BY sector 
                ORDER BY count DESC
            ''')
            sectors = cursor.fetchall()
            
            return {
                'total_companies': total_companies,
                'total_earnings_records': total_earnings,
                'upcoming_companies': upcoming_companies,
                'last_update': last_update,
                'sectors': sectors
            }
    
    def clear_all_data(self):
        """Clear all earnings data from the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM earnings')
            conn.commit()
    
    def get_database_size(self) -> str:
        """Get database file size"""
        if os.path.exists(self.db_path):
            size = os.path.getsize(self.db_path)
            # Convert bytes to human readable format
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        return "0 B"
    
    def insert_options_data(self, options_data_list: List[Dict]) -> int:
        """
        Insert options IV data into database
        
        Args:
            options_data_list: List of options data dictionaries
            
        Returns:
            int: Number of records inserted
        """
        if not options_data_list:
            return 0
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            inserted_count = 0
            
            for data in options_data_list:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO options_data 
                        (symbol, current_price, expiration_date, days_to_expiration,
                         implied_volatility, call_iv, put_iv, historical_volatility,
                         iv_rank, expected_move_percent, expected_move_dollar,
                         expected_move_up, expected_move_down, straddle_price,
                         atm_strike, iv_crush_percent, estimated_option_value_loss,
                         earnings_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        data['symbol'], data.get('current_price'), data.get('expiration_date'),
                        data.get('days_to_expiration'), data.get('implied_volatility'),
                        data.get('call_iv'), data.get('put_iv'), data.get('historical_volatility'),
                        data.get('iv_rank'), data.get('expected_move_percent'),
                        data.get('expected_move_dollar'), data.get('expected_move_up'),
                        data.get('expected_move_down'), data.get('straddle_price'),
                        data.get('atm_strike'), data.get('iv_crush_percent'),
                        data.get('estimated_option_value_loss'), data.get('earnings_date')
                    ))
                    inserted_count += 1
                except Exception as e:
                    print(f"Error inserting options data for {data.get('symbol', 'unknown')}: {e}")
            
            conn.commit()
            return inserted_count
    
    def get_all_options_data(self) -> pd.DataFrame:
        """Get all options data from database"""
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT o.*, e.company_name, e.sector
                FROM options_data o
                LEFT JOIN earnings e ON o.symbol = e.symbol
                ORDER BY o.expected_move_percent DESC
            '''
            return pd.read_sql_query(query, conn)
    
    def get_options_by_symbol(self, symbol: str) -> pd.DataFrame:
        """Get options data for a specific symbol"""
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT * FROM options_data 
                WHERE symbol = ?
                ORDER BY expiration_date
            '''
            return pd.read_sql_query(query, conn, params=(symbol,))
    
    def get_high_iv_options(self, min_iv: float = 50.0) -> pd.DataFrame:
        """Get options with high implied volatility"""
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT o.*, e.company_name, e.sector
                FROM options_data o
                LEFT JOIN earnings e ON o.symbol = e.symbol
                WHERE o.implied_volatility >= ?
                ORDER BY o.implied_volatility DESC
            '''
            return pd.read_sql_query(query, conn, params=(min_iv,))