import requests
import pandas as pd
import time
from datetime import datetime
from tqdm import tqdm

class PriceHistoryClient:
    """
    Client to fetch historical price data from Yahoo Finance API directly.
    """
    BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"

    def __init__(self):
        pass

    def fetch_history(self, ticker, period='10y', interval='1d'):
        """
        Fetches OHLCV data for a ticker.
        Returns DataFrame with Date index, Open, High, Low, Close, Adj Close, Volume.
        """
        url = self.BASE_URL.format(ticker=ticker)
        params = {
            'range': period,
            'interval': interval,
            'events': 'div,split'
        }
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; AnalyticsBot/1.0)'}
        
        for attempt in range(3):
            try:
                response = requests.get(url, params=params, headers=headers, timeout=10)
                if response.status_code == 404:
                    print(f"Ticker {ticker} not found (404).")
                    return pd.DataFrame()
                
                response.raise_for_status()
                data = response.json()
                
                if 'chart' not in data or 'result' not in data['chart'] or not data['chart']['result']:
                    return pd.DataFrame()

                result = data['chart']['result'][0]
                meta = result.get('meta', {})
                timestamp = result.get('timestamp', [])
                indicators = result.get('indicators', {})
                quote = indicators.get('quote', [{}])[0]
                adj_close = indicators.get('adjclose', [{}])[0].get('adjclose', [])

                if not timestamp:
                    return pd.DataFrame()

                df = pd.DataFrame({
                    'Date': pd.to_datetime(timestamp, unit='s'),
                    'Open': quote.get('open', []),
                    'High': quote.get('high', []),
                    'Low': quote.get('low', []),
                    'Close': quote.get('close', []),
                    'Volume': quote.get('volume', []),
                    'Adj Close': adj_close if adj_close else quote.get('close', []) # Fallback
                })
                
                df.set_index('Date', inplace=True)
                return df

            except requests.exceptions.HTTPError as e:
                 if response.status_code == 429: # Rate limit
                     time.sleep(2 * (attempt + 1))
                     continue
                 print(f"HTTP Error fetching {ticker}: {e}")
                 break
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
                time.sleep(1)
        
        return pd.DataFrame()

    def fetch_batch(self, tickers):
        """
        Fetches history for a list of tickers with progress bar and rate limiting.
        Returns a dict {ticker: DataFrame}.
        """
        results = {}
        for ticker in tqdm(tickers, desc="Fetching Prices"):
            df = self.fetch_history(ticker)
            if not df.empty:
                results[ticker] = df
            time.sleep(0.5) # Polite delay
        return results

if __name__ == "__main__":
    client = PriceHistoryClient()
    df = client.fetch_history("PETR4.SA", range="5y")
    print(df.tail())
