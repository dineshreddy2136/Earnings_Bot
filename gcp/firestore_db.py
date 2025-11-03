"""
Firestore Database Operations - Earnings Bot

Handles all Firestore interactions for storing and retrieving:
- Earnings data
- Options IV data
"""

from google.cloud import firestore
from datetime import datetime, timedelta, date
import logging
from typing import List, Dict, Optional
import pytz

logger = logging.getLogger(__name__)


class FirestoreDB:
    """Firestore database operations"""
    
    def __init__(self):
        """Initialize Firestore client"""
        self.db = firestore.Client()
        self.earnings_collection = self.db.collection('earnings')
        self.options_collection = self.db.collection('options_data')
        logger.info("✅ Firestore client initialized")
    
    # ==================== EARNINGS DATA ====================
    
    def upsert_earnings(self, earnings_list: List[Dict]) -> Dict:
        """
        Insert or update earnings data in Firestore
        
        Args:
            earnings_list: List of earnings dictionaries
            
        Returns:
            dict: Summary of operation (new, updated, errors)
        """
        new_count = 0
        updated_count = 0
        error_count = 0
        
        for earning in earnings_list:
            try:
                symbol = earning.get('symbol')
                earnings_date = earning.get('earnings_date')
                
                if not symbol or earnings_date == 'N/A':
                    continue
                
                # Document ID: symbol_date (e.g., AAPL_2025-11-05)
                doc_id = f"{symbol}_{earnings_date}"
                
                # Add timestamp
                earning['last_updated'] = firestore.SERVER_TIMESTAMP
                
                # Check if document exists
                doc_ref = self.earnings_collection.document(doc_id)
                doc = doc_ref.get()
                
                if doc.exists:
                    # Update existing
                    doc_ref.update(earning)
                    updated_count += 1
                else:
                    # Create new
                    earning['created_at'] = firestore.SERVER_TIMESTAMP
                    doc_ref.set(earning)
                    new_count += 1
                    
            except Exception as e:
                logger.error(f"Error upserting {earning.get('symbol', 'unknown')}: {e}")
                error_count += 1
        
        logger.info(f"Earnings upsert: {new_count} new, {updated_count} updated, {error_count} errors")
        
        return {
            'new_records': new_count,
            'updated_records': updated_count,
            'errors': error_count,
            'total': new_count + updated_count
        }
    
    def get_earnings_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Get earnings data for a date range
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            list: List of earnings dictionaries
        """
        try:
            docs = self.earnings_collection \
                .where('earnings_date', '>=', start_date) \
                .where('earnings_date', '<=', end_date) \
                .order_by('earnings_date') \
                .stream()
            
            earnings = []
            for doc in docs:
                data = doc.to_dict()
                earnings.append(data)
            
            logger.info(f"Retrieved {len(earnings)} earnings for {start_date} to {end_date}")
            return earnings
            
        except Exception as e:
            logger.error(f"Error getting earnings by date range: {e}")
            return []
    
    def get_earnings_this_week(self) -> List[Dict]:
        """
        Get earnings for current week (Monday-Sunday)
        
        Returns:
            list: List of earnings dictionaries
        """
        today = date.today()
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        sunday = monday + timedelta(days=6)
        
        return self.get_earnings_by_date_range(
            monday.strftime('%Y-%m-%d'),
            sunday.strftime('%Y-%m-%d')
        )
    
    def get_upcoming_earnings(self, days_ahead: int = 30) -> List[Dict]:
        """
        Get upcoming earnings within specified days
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            list: List of earnings dictionaries
        """
        today = date.today()
        future_date = today + timedelta(days=days_ahead)
        
        return self.get_earnings_by_date_range(
            today.strftime('%Y-%m-%d'),
            future_date.strftime('%Y-%m-%d')
        )
    
    def get_earnings_by_symbol(self, symbol: str) -> List[Dict]:
        """
        Get all earnings data for a specific symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            list: List of earnings dictionaries
        """
        try:
            docs = self.earnings_collection \
                .where('symbol', '==', symbol) \
                .order_by('earnings_date', direction=firestore.Query.DESCENDING) \
                .stream()
            
            earnings = [doc.to_dict() for doc in docs]
            return earnings
            
        except Exception as e:
            logger.error(f"Error getting earnings for {symbol}: {e}")
            return []
    
    # ==================== OPTIONS DATA ====================
    
    def upsert_options_data(self, options_list: List[Dict]) -> Dict:
        """
        Insert or update options IV data
        
        Args:
            options_list: List of options data dictionaries
            
        Returns:
            dict: Summary of operation
        """
        new_count = 0
        updated_count = 0
        error_count = 0
        
        for options in options_list:
            try:
                symbol = options.get('symbol')
                
                if not symbol:
                    continue
                
                # Document ID: symbol (latest data per symbol)
                doc_id = symbol
                
                # Add timestamp
                options['last_updated'] = firestore.SERVER_TIMESTAMP
                
                # Check if exists
                doc_ref = self.options_collection.document(doc_id)
                doc = doc_ref.get()
                
                if doc.exists:
                    doc_ref.update(options)
                    updated_count += 1
                else:
                    options['created_at'] = firestore.SERVER_TIMESTAMP
                    doc_ref.set(options)
                    new_count += 1
                    
            except Exception as e:
                logger.error(f"Error upserting options for {options.get('symbol', 'unknown')}: {e}")
                error_count += 1
        
        logger.info(f"Options upsert: {new_count} new, {updated_count} updated, {error_count} errors")
        
        return {
            'new_records': new_count,
            'updated_records': updated_count,
            'errors': error_count,
            'total': new_count + updated_count
        }
    
    def get_options_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Get options data for multiple symbols
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            dict: Dictionary with symbol as key and options data as value
        """
        options_dict = {}
        
        try:
            for symbol in symbols:
                doc = self.options_collection.document(symbol).get()
                if doc.exists:
                    options_dict[symbol] = doc.to_dict()
            
            logger.info(f"Retrieved options data for {len(options_dict)} symbols")
            
        except Exception as e:
            logger.error(f"Error getting options data: {e}")
        
        return options_dict
    
    def get_all_options_data(self) -> List[Dict]:
        """
        Get all options data
        
        Returns:
            list: List of options data dictionaries
        """
        try:
            docs = self.options_collection.stream()
            options = [doc.to_dict() for doc in docs]
            logger.info(f"Retrieved {len(options)} options records")
            return options
            
        except Exception as e:
            logger.error(f"Error getting all options data: {e}")
            return []
    
    # ==================== UTILITY ====================
    
    def get_database_stats(self) -> Dict:
        """
        Get database statistics
        
        Returns:
            dict: Database stats
        """
        try:
            # Count earnings documents
            earnings_docs = list(self.earnings_collection.stream())
            earnings_count = len(earnings_docs)
            
            # Count options documents
            options_docs = list(self.options_collection.stream())
            options_count = len(options_docs)
            
            # Get upcoming earnings count
            upcoming = self.get_upcoming_earnings(30)
            upcoming_count = len(upcoming)
            
            return {
                'total_earnings_records': earnings_count,
                'total_options_records': options_count,
                'upcoming_earnings_30days': upcoming_count,
                'last_checked': datetime.now(pytz.timezone('US/Eastern')).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def cleanup_old_earnings(self, days_old: int = 90):
        """
        Delete earnings data older than specified days
        
        Args:
            days_old: Delete records older than this many days
            
        Returns:
            int: Number of records deleted
        """
        try:
            cutoff_date = (date.today() - timedelta(days=days_old)).strftime('%Y-%m-%d')
            
            docs = self.earnings_collection \
                .where('earnings_date', '<', cutoff_date) \
                .stream()
            
            deleted_count = 0
            for doc in docs:
                doc.reference.delete()
                deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} old earnings records (older than {days_old} days)")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old earnings: {e}")
            return 0
