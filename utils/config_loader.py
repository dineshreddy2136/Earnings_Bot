"""Configuration loader utility"""
import yaml
import os
from pathlib import Path


class Config:
    """Configuration loader and accessor"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one config instance"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from config.yaml"""
        config_path = Path(__file__).parent.parent / 'config.yaml'
        
        try:
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: config.yaml not found at {config_path}. Using defaults.")
            self._config = self._get_default_config()
        except Exception as e:
            print(f"Error loading config: {e}. Using defaults.")
            self._config = self._get_default_config()
    
    def _get_default_config(self):
        """Return default configuration if config file is not found"""
        return {
            'sync': {
                'major_tickers': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA'],
                'max_workers': 10,
                'max_retries': 3,
                'retry_delay': 1
            },
            'database': {
                'path': 'earnings.db'
            },
            'cache': {
                'ttl': 300
            },
            'options': {
                'high_iv_threshold': 50.0,
                'max_days_to_expiration': 60,
                'iv_history_days': 252
            },
            'ui': {
                'page_title': 'Complete Earnings Dashboard',
                'page_icon': '📊',
                'layout': 'wide'
            },
            'economic_calendar': {
                'categories': ['FOMC', 'CPI', 'PPI', 'Unemployment', 'GDP', 'Retail Sales', 'PMI'],
                'lookback_days': 30,
                'lookahead_days': 60
            }
        }
    
    def get(self, *keys, default=None):
        """
        Get configuration value using dot notation
        
        Args:
            *keys: Configuration keys (e.g., 'sync', 'major_tickers')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    @property
    def sync_major_tickers(self):
        """Get major tickers for quick sync"""
        return self.get('sync', 'major_tickers', default=[])
    
    @property
    def sync_max_workers(self):
        """Get max workers for parallel processing"""
        return self.get('sync', 'max_workers', default=10)
    
    @property
    def database_path(self):
        """Get database path"""
        return self.get('database', 'path', default='earnings.db')
    
    @property
    def cache_ttl(self):
        """Get cache TTL"""
        return self.get('cache', 'ttl', default=300)
    
    @property
    def options_high_iv_threshold(self):
        """Get high IV threshold"""
        return self.get('options', 'high_iv_threshold', default=50.0)
    
    @property
    def options_iv_history_days(self):
        """Get IV history days for calculations"""
        return self.get('options', 'iv_history_days', default=252)


# Global config instance
config = Config()
