"""
Alpha Vantage API Client for Global Stock Data Collection
Collects fundamental and price data from global exchanges (NYSE, NASDAQ, LSE, etc.)
"""

import requests
import time
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class AlphaVantageClient:
    """Client for fetching stock data from Alpha Vantage API"""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: str):
        """
        Initialize Alpha Vantage client
        
        Args:
            api_key: Alpha Vantage API key
        """
        self.api_key = api_key
        self.session = requests.Session()
        
    def _make_request(self, params: Dict) -> Optional[Dict]:
        """
        Make API request with rate limiting and error handling
        
        Args:
            params: Query parameters for the API
            
        Returns:
            JSON response or None if error
        """
        params['apikey'] = self.api_key
        
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for API error messages
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API Error for {params.get('symbol')}: {data['Error Message']}")
                return None
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage Rate Limit for {params.get('symbol')}: {data['Note']}")
                time.sleep(60)  # Wait 1 minute if rate limited
                return None
                
            if not data:
                logger.error(f"Alpha Vantage returned empty data for {params.get('symbol')}")
                return None

            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
    
    def get_company_overview(self, symbol: str) -> Optional[Dict]:
        """
        Get company fundamental data including P/E, market cap, sector, etc.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
            
        Returns:
            Dictionary with company overview data or None
        """
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        if not data or not data.get('Symbol'):
            return None
            
        try:
            return {
                'symbol': data.get('Symbol'),
                'name': data.get('Name'),
                'exchange': data.get('Exchange'),
                'sector': data.get('Sector'),
                'industry': data.get('Industry'),
                'market_cap': float(data.get('MarketCapitalization', 0)),
                'pe_ratio': float(data.get('PERatio', 0)) if data.get('PERatio') != 'None' else 0,
                'profit_margin': float(data.get('ProfitMargin', 0)) if data.get('ProfitMargin') != 'None' else 0,
                'roe': float(data.get('ReturnOnEquityTTM', 0)) if data.get('ReturnOnEquityTTM') != 'None' else 0,
                'dividend_yield': float(data.get('DividendYield', 0)) if data.get('DividendYield') != 'None' else 0,
                'eps': float(data.get('EPS', 0)) if data.get('EPS') != 'None' else 0,
                'revenue_ttm': float(data.get('RevenueTTM', 0)) if data.get('RevenueTTM') != 'None' else 0,
                'beta': float(data.get('Beta', 0)) if data.get('Beta') != 'None' else 0,
            }
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing overview for {symbol}: {e}")
            return None
    
    def get_global_quote(self, symbol: str) -> Optional[Dict]:
        """
        Get current price and basic quote data
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with quote data or None
        """
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        if not data or 'Global Quote' not in data:
            return None
            
        quote = data['Global Quote']
        if not quote:
            return None
            
        try:
            return {
                'symbol': quote.get('01. symbol'),
                'price': float(quote.get('05. price', 0)),
                'change_percent': float(quote.get('10. change percent', '0').replace('%', '')),
                'volume': int(quote.get('06. volume', 0))
            }
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing quote for {symbol}: {e}")
            return None
