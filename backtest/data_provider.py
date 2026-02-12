
import pandas as pd
import json
import os
import logging
from datetime import datetime
from collections import defaultdict
import ipeadatapy as ip

# Configure Logging
logger = logging.getLogger("BacktestDataProvider")

class DataProvider:
    def __init__(self, data_path="web/public/data.json", price_path="data/processed/price_history.json"):
        self.data_path = data_path
        self.price_path = price_path
        self.financials_data = {}
        self.prices_data = {}
        self.benchmarks = {}
        self.assets_list = []
        self.price_meta = {}
        self.data_quality_report = {
            "missing": defaultdict(list),
            "zero": defaultdict(list),
            "tickers_without_financials": [],
            "tickers_without_prices": [],
            "tickers_without_prices_history": [],
            "total_financial_tickers": 0,
            "total_price_tickers": 0,
        }
        
    def load_data(self):
        """Loads processed asset data and price history."""
        self.financials_data = {}
        self.prices_data = {}
        self.assets_list = []
        self.price_meta = {}
        # Reset report
        self.data_quality_report = {
            "missing": defaultdict(list),
            "zero": defaultdict(list),
            "tickers_without_financials": [],
            "tickers_without_prices": [],
            "tickers_without_prices_history": [],
            "total_financial_tickers": 0,
            "total_price_tickers": 0,
        }

        indicators_to_track = [
            "p_l",
            "p_vp",
            "roe",
            "roic",
            "dy",
            "net_margin",
            "revenue",
            "net_income",
        ]

        # 1. Load Financials (Quarterly)
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r') as f:
                    loaded = json.load(f)

                if isinstance(loaded, dict):
                    self.financials_data = loaded
                else:
                    logger.error("Unexpected financials format (expected dict by ticker).")
                    self.financials_data = {}

                total_financial = len(self.financials_data)
                self.data_quality_report["total_financial_tickers"] = total_financial

                for ticker, records in self.financials_data.items():
                    if not records:
                        self.data_quality_report["tickers_without_financials"].append(ticker)
                        continue

                    latest = records[-1] if isinstance(records, list) else records
                    for indicator in indicators_to_track:
                        val = latest.get(indicator)
                        if val is None:
                            self.data_quality_report["missing"][indicator].append(ticker)
                        else:
                            try:
                                numeric_val = float(val)
                                if numeric_val == 0:
                                    self.data_quality_report["zero"][indicator].append(ticker)
                            except (TypeError, ValueError):
                                # Non-numeric indicator (e.g., strings) are noted as missing
                                self.data_quality_report["missing"][indicator].append(ticker)

                logger.info(f"Loaded financials for {total_financial} tickers.")
            except Exception as e:
                logger.error(f"Error loading financials: {e}")
        else:
            logger.error(f"Financials file not found: {self.data_path}")

        # 2. Load Prices (Daily)
        if os.path.exists(self.price_path):
            try:
                with open(self.price_path, 'r') as f:
                    raw_prices = json.load(f)

                count = 0
                for ticker, payload in raw_prices.items():
                    records = []
                    meta = {}

                    if isinstance(payload, dict):
                        records = payload.get("prices") or payload.get("data") or payload.get("records") or []
                        meta = payload.get("meta") or {}
                    elif isinstance(payload, list):
                        records = payload
                    else:
                        continue

                    if not records:
                        self.data_quality_report["tickers_without_prices_history"].append(ticker)
                        continue

                    df = pd.DataFrame(records)
                    if df.empty:
                        self.data_quality_report["tickers_without_prices_history"].append(ticker)
                        continue

                    df.columns = [str(c).lower() for c in df.columns]

                    # Normalize datetime column
                    date_column = None
                    if 'date' in df.columns:
                        date_column = 'date'
                    elif 'datetime' in df.columns:
                        date_column = 'datetime'
                    elif 'timestamp' in df.columns:
                        date_column = 'timestamp'

                    if date_column:
                        df[date_column] = pd.to_datetime(df[date_column])
                        df.set_index(date_column, inplace=True)
                        df.sort_index(inplace=True)
                    else:
                        logger.warning(f"{ticker}: price records missing date field.")
                        self.data_quality_report["tickers_without_prices_history"].append(ticker)
                        continue

                    clean_ticker = ticker.replace('.SA', '').upper()
                    self.prices_data[clean_ticker] = df
                    self.price_meta[clean_ticker] = meta
                    count += 1

                self.data_quality_report["total_price_tickers"] = count
                self.assets_list = sorted(self.prices_data.keys())
                logger.info(f"Loaded prices for {count} tickers. Active universe: {len(self.assets_list)}")
            except Exception as e:
                logger.error(f"Error loading prices: {e}")
        else:
            logger.error(f"Price history file not found: {self.price_path}")

        # Match coverage between financials and prices
        if self.financials_data:
            financial_tickers = {ticker.upper() for ticker in self.financials_data.keys()}
        else:
            financial_tickers = set()

        price_tickers = set(self.assets_list)
        missing_prices = sorted(financial_tickers - price_tickers)
        for ticker in missing_prices:
            self.data_quality_report["tickers_without_prices"].append(ticker)

        if missing_prices:
            logger.warning(f"{len(missing_prices)} tickers sem histórico de preços carregado (ex.: {missing_prices[:5]})")
        if self.data_quality_report["tickers_without_financials"]:
            logger.warning(f"{len(self.data_quality_report['tickers_without_financials'])} tickers sem registros financeiros no arquivo processado.")

    def get_price_data(self, ticker):
        """Returns full daily price DataFrame."""
        return self.prices_data.get(ticker, pd.DataFrame())

    def get_financials_data(self, ticker):
        """Returns full financials DataFrame (quarterly)."""
        if not hasattr(self, '_financials_cache'):
            self._financials_cache = {}
            
        if ticker in self._financials_cache:
            return self._financials_cache[ticker]

        if ticker not in self.financials_data:
            return pd.DataFrame()
        
        data = self.financials_data[ticker]
        df = pd.DataFrame(data)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.drop_duplicates(subset=['date'], keep='last', inplace=True)
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            
        self._financials_cache[ticker] = df
        return df

    def get_latest_price_row(self, ticker, date):
        """Returns price row at date (or nearest before)."""
        df = self.get_price_data(ticker)
        if df.empty: return None
        
        # Check exact match first
        if date in df.index:
            return df.loc[date]
            
        # AsOf lookup for latest available price
        # Ensure index is sorted
        idx = df.index.asof(date)
        if pd.isna(idx): return None
        
        # Check staleness? If price is 1 year old, maybe don't return?
        # For backtest, we assume last price holds or system handles gaps.
        return df.loc[idx]

    def get_latest_financials_row(self, ticker, date):
        """Returns metrics from latest financial report strictly BEFORE or ON date."""
        df = self.get_financials_data(ticker)
        if df.empty: return None
        
        idx = df.index.asof(date)
        if pd.isna(idx): return None
        return df.loc[idx]
    
    def get_data_quality_report(self):
        """Returns summary collected during load_data."""
        return self.data_quality_report
        
    def fetch_benchmarks(self):
        """Fetches IBOV, SELIC, and IPCA history."""
        # Reuse logic from SelicAnalyzer or fetch fresh
        # For simplicity and speed in backtest, we might want to cache this too.
        # But let's fetch for now using ipeadatapy as user requested standard.
        
        # 1. SELIC (BM366_TJOVER366) - Daily %
        try:
            selic = ip.timeseries('BM366_TJOVER366')
            cols = [c for c in selic.columns if 'VALUE' in c]
            if cols:
                val_col = cols[0]
                selic.index = pd.to_datetime(selic.index)
                # Selic accumulated: (1+r)^(1/252)
                # Raw value is % a.a. (e.g. 13.75). Divide by 100.
                self.benchmarks['SELIC_Rate'] = selic[val_col] / 100.0
        except:
            logger.warning("Failed to fetch SELIC")

        # 2. IPCA (PRECOS12_IPCAG12) - Monthly %
        try:
            ipca = ip.timeseries('PRECOS12_IPCAG12') # IPCA - Geral - var. % mensal
            cols = [c for c in ipca.columns if 'VALUE' in c]
            if cols:
                val_col = cols[0]
                ipca.index = pd.to_datetime(ipca.index)
                self.benchmarks['IPCA'] = ipca[val_col] / 100.0
        except:
            logger.warning("Failed to fetch IPCA")
            
        # 3. IBOVESPA (GM366_IBVSP366)
        try:
            ibov = ip.timeseries('GM366_IBVSP366')
            cols = [c for c in ibov.columns if 'VALUE' in c]
            if cols:
                val_col = cols[0]
                ibov.index = pd.to_datetime(ibov.index)
                self.benchmarks['IBOV'] = ibov[val_col]
        except:
            logger.warning("Failed to fetch IBOV")

    def get_benchmark_data(self, benchmark_name):
        return self.benchmarks.get(benchmark_name, pd.Series())

    def get_market_timeline(self, start_date, end_date):
        """Returns list of trading days between start and end (inclusive)."""
        # Prefer IBOV index as source of truth for "Market Open"
        ibov = self.benchmarks.get('IBOV')
        
        if ibov is None or ibov.empty:
            # Fallback to B3 calendar logic or just Business Days if IBOV missing
            logger.warning("IBOV data missing for timeline. Using Business Days fallback.")
            return pd.date_range(start=start_date, end=end_date, freq='B')
            
        # Filter IBOV dates
        mask = (ibov.index >= pd.to_datetime(start_date)) & (ibov.index <= pd.to_datetime(end_date))
        timeline = ibov.index[mask].sort_values().tolist()
        
        if timeline:
             # Refine with Stock Data if available
             market_proxy_ticker = next((t for t in ['VALE3', 'PETR4', 'ITUB4'] if t in self.prices_data), None)
             
             if market_proxy_ticker:
                 proxy_df = self.prices_data[market_proxy_ticker]
                 proxy_dates = proxy_df.index
                 
                 # Intersect with current timeline
                 timeline_idx = pd.DatetimeIndex(timeline)
                 valid_idx = timeline_idx.intersection(proxy_dates)
                 
                 timeline = valid_idx.sort_values().tolist()

             # Manual Holiday check (Jan 1st)
             if timeline and timeline[0].month == 1 and timeline[0].day == 1:
                 timeline = [d for d in timeline if not (d.month == 1 and d.day == 1)]
        
        return timeline

    def get_selic_daily(self, date):
        """Returns daily SELIC factor (e.g. 0.0004 for 0.04%) for a given date."""
        selic = self.benchmarks.get('SELIC_Rate')
        if selic is None or selic.empty:
            return 0.0004 # Fallback ~10% a.a.
            
        val = 0.0
        if date in selic.index:
            val = selic.loc[date]
        else:
            # Fallback closest past
            idx = selic.index.asof(date)
            if not pd.isna(idx):
                val = selic.loc[idx]
        
        # Assuming val is annualized rate (e.g. 0.1375)
        # Convert to daily: (1 + r)^(1/252) - 1
        # Check if val is reasonable (e.g. < 1.0 means 100%). If > 1.0 it might be whole number %
        # In fetch_benchmarks we divide by 100. So 13.75 becomes 0.1375.
        if val > 5.0: val = val / 100.0 # Safety check if data is weird
        
        try:
            return (1 + val)**(1/252) - 1
        except:
            return 0.0
