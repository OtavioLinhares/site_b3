
import pandas as pd
import json
import os
import numpy as np
from datetime import datetime
import difflib

class DataProcessor:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.processed_dir = os.path.join(data_dir, "processed")
        self.cvm_path = os.path.join(self.processed_dir, "cvm_financials_history.csv")
        self.price_path = os.path.join(self.processed_dir, "price_history.json")
        self.fundamentus_path = "data/processed/fundamentus_tickers.csv"
        
        # Standard Corporate Tax Rate approximation for ROIC
        self.TAX_RATE = 0.34

    def load_data(self):
        """
        Loads the CVM Financials CSV, Price History JSON, and Fundamentus Tickers.
        Returns: (df_financials, price_map, tickers_df)
        """
        if not os.path.exists(self.cvm_path) or not os.path.exists(self.price_path):
            raise FileNotFoundError("Processed data files not found. Run pipeline first.")

        # print(f"Loading Financials from {self.cvm_path}...")
        df_fin = pd.read_csv(self.cvm_path)
        if 'DT_FIM_EXERC' in df_fin.columns:
            df_fin['DT_FIM_EXERC'] = pd.to_datetime(df_fin['DT_FIM_EXERC'])

        # print(f"Loading Prices from {self.price_path}...")
        with open(self.price_path, 'r') as f:
            price_map = json.load(f)
            
        processed_prices = {}
        for ticker, data in price_map.items():
            if not data: continue
            pdf = pd.DataFrame(data)
            # Normalize columns
            pdf.columns = [c.lower().replace(' ', '') for c in pdf.columns]
            
            # Map specific YF names if needed
            # yfinance: Date, Open, High, Low, Close, Adj Close, Volume
            # normalized: date, open, high, low, close, adjclose, volume
            
            if 'date' in pdf.columns:
                pdf['date'] = pd.to_datetime(pdf['date'])
                pdf.set_index('date', inplace=True)
                pdf.sort_index(inplace=True)
                processed_prices[ticker] = pdf
            
        tickers_df = pd.DataFrame()
        if os.path.exists(self.fundamentus_path):
            tickers_df = pd.read_csv(self.fundamentus_path)
            
        return df_fin, processed_prices, tickers_df

    def map_cvm_to_tickers(self, df_fin, tickers_df):
        """
        Maps CVM 'DENOM_CIA' to Tickers using Fundamentus data.
        Returns a dict {cvm_name: ticker}
        """
        if tickers_df.empty:
            return {}

        mapping = {}
        # Fundamentus often has 'Company' column for name (check column names)
        # Usually it is 'name'? Need to check. 
        # In current pipeline we rename 'papel' -> 'ticker'.
        # Assuming there is a name column. Let's inspect columns if possible, but for now checking standard names.
        
        # Standard columns from fundamentus.get_resultado() are usually just metrics.
        # Wait, get_resultado() DOES NOT return Company Name, only Ticker.
        # This is a problem. We need Ticker -> Name map.
        # Use `fundamentus.get_detalhes_papel(ticker)`? Too slow.
        # Or maybe check if our `pipeline.py` adds names?
        
        # Check `fundamentus_client.py`: fetch_all_current() returns `get_resultado()`.
        # `get_resultado()` index is Ticker. Columns are P/L, DY etc. NO NAME.
        
        # FALLBACK: We cannot map by name if we don't have names for tickers.
        # Workaround: Use the fact that CVM Code is sometimes the Ticker prefix? No.
        # Workaround 2: Use a hardcoded list of major companies?
        # Workaround 3: Use `yfinance` to get shortName for tickers? (Available in current `prices` map!)
        
        # AHA! We have `price_history.json`!
        # Do we have names there?
        # Currently `PriceHistoryClient` only saves: date, open, high, low, close, adjclose, volume.
        
        # Back to `pipeline.py`:
        # "History DF has 'company_name' and 'cvm_code', but not Ticker."
        # If we can't map, we can't join.
        
        # Critical strategy shift: 
        # CVM `CD_CVM` is standard. `CVMCodes.csv` exists on CVM site mapping Code -> CNPJ -> Ticker.
        # Since I can't download more stuff easily, I will try to match solely based on "Ticker" appearing in "Company Name".
        # e.g. "PETROBRAS" -> PETR4.
        
        # Better: Use the `valid_assets` list from `pipeline.run` execution if it had names.
        
        # Let's try `difflib` against the list of tickers itself, assuming some correlation?
        # No, Ticker "VALE3" vs Name "VALE S.A.". Matches well.
        # Ticker "PETR4" vs Name "PETROBRAS". Matches poorly.
        
        # Plan B: Just load a small static map for the top 20-30 companies for the demo?
        # Or try to fuzzy match Ticker (minus number) with Name words.
        
        if os.path.exists("data/processed/ticker_names.csv"):
            try:
                names_df = pd.read_csv("data/processed/ticker_names.csv")
                ticker_names_map = []
                for _, row in names_df.iterrows():
                     if pd.notna(row['short_name']):
                         ticker_names_map.append({'ticker': row['ticker'], 'name': str(row['short_name']).upper()})
                     if pd.notna(row['long_name']):
                         ticker_names_map.append({'ticker': row['ticker'], 'name': str(row['long_name']).upper()})
                
                candidates = [x['name'] for x in ticker_names_map]
                tickers = names_df['ticker'].unique()
            except pd.errors.EmptyDataError:
                print("Warning: ticker_names.csv is empty. Using fallback mapping.")
                tickers = tickers_df['ticker'].unique()
                ticker_names_map = []
                candidates = []
        else:
            tickers = tickers_df['ticker'].unique()
            ticker_names_map = []
            candidates = []

        cvm_names = df_fin['DENOM_CIA'].unique()
        
        for name in cvm_names:
            normalized_name = name.upper().replace('S.A.', '').replace('S/A', '').strip()
            
            # Strategy 1: Match against YFinance Names (if available)
            if candidates:
                matches = difflib.get_close_matches(normalized_name, candidates, n=1, cutoff=0.6)
                if matches:
                    matched_name = matches[0]
                    for x in ticker_names_map:
                        if x['name'] == matched_name:
                            mapping[name] = x['ticker']
                            break
                    continue
            
            # Strategy 2: Heuristic (Fallback)
            # Try to find a ticker that starts with the first word of company
            first_word = normalized_name.split()[0]
            if len(first_word) < 3: continue
            
            # Simple match: Ticker starts with first word chars
            matches = [t for t in tickers if t.startswith(first_word[:4])]
            
            # Special Cases (Expanded Top 30)
            if 'PETROBRAS' in normalized_name: matches = ['PETR4', 'PETR3']
            if 'VALE' in normalized_name: matches = ['VALE3']
            if 'ITAU UNIBANCO' in normalized_name: matches = ['ITUB4']
            if 'BRADESCO' in normalized_name: matches = ['BBDC4']
            if 'AMBEV' in normalized_name: matches = ['ABEV3']
            if 'WEG' in normalized_name: matches = ['WEGE3']
            if 'BANCO DO BRASIL' in normalized_name: matches = ['BBAS3']
            if 'BTG PACTUAL' in normalized_name: matches = ['BPAC11']
            if 'ELETROBRAS' in normalized_name: matches = ['ELET3', 'ELET6']
            if 'LOCALIZA' in normalized_name: matches = ['RENT3']
            if 'SUZANO' in normalized_name: matches = ['SUZB3']
            if 'JBS' in normalized_name: matches = ['JBSS3']
            if 'REDE D ORO' in normalized_name or 'D OR' in normalized_name: matches = ['RDOR3']
            if 'RAIA DROGASIL' in normalized_name: matches = ['RADL3']
            if 'PRIO' in normalized_name: matches = ['PRIO3']
            if 'VIBRA' in normalized_name: matches = ['VBBR3']
            if 'ASSAI' in normalized_name: matches = ['ASAI3']
            if 'HAPVIDA' in normalized_name: matches = ['HAPV3']
            if 'RUMO' in normalized_name: matches = ['RAIL3']
            if 'CEMIG' in normalized_name: matches = ['CMIG4']
            if 'LOJAS RENNER' in normalized_name: matches = ['LREN3']
            if 'TELEFONICA' in normalized_name: matches = ['VIVT3']
            if 'GERDAU' in normalized_name: matches = ['GGBR4']
            if 'COSAN' in normalized_name: matches = ['CSAN3']
            if 'METALURGICA GERDAU' in normalized_name: matches = ['GOAU4']
            if 'CCR' in normalized_name: matches = ['CCRO3']
            if 'SABESP' in normalized_name: matches = ['SBSP3']
            if 'KLABIN' in normalized_name: matches = ['KLBN11']
            if 'BRF' in normalized_name: matches = ['BRFS3']
            if 'TIM' in normalized_name: matches = ['TIMS3']
            if 'EQUATORIAL' in normalized_name: matches = ['EQTL3']
            if 'ULTRAPAR' in normalized_name: matches = ['UGPA3']
            if 'TOTVS' in normalized_name: matches = ['TOTS3']
            if 'EMBRAER' in normalized_name: matches = ['EMBR3']
            if 'HYPERA' in normalized_name: matches = ['HYPE3']
            if 'COPEL' in normalized_name: matches = ['CPLE6']
            if 'CSN' in normalized_name or 'SIDERURGICA NACIONAL' in normalized_name: matches = ['CSNA3']
            if 'MAGAZINE LUIZA' in normalized_name: matches = ['MGLU3']
            if 'B3' in normalized_name: matches = ['B3SA3']

            if matches:
                # Prefer preferred (4) or ordinary (3)
                # Sort to get 4 or 3 first
                matches.sort(key=lambda x: x[-1], reverse=True) # 4 before 3
                mapping[name] = matches[0]

        return mapping

    def calculate_multiples(self, df_fin, price_map, mapping):
        results = []
        
        # Process per company
        for cvm_name, group in df_fin.groupby('DENOM_CIA'):
            ticker = mapping.get(cvm_name)
            if not ticker: continue
            
            # Fix ticker for price lookup (add .SA if needed, or remove)
            # Price map keys probably have .SA if pipeline saved them that way
            # Let's check keys in price_map
            price_ticker = ticker
            if ticker not in price_map and f"{ticker}.SA" in price_map:
                price_ticker = f"{ticker}.SA"
            
            if price_ticker not in price_map: continue
            
            prices_df = price_map[price_ticker]
            if prices_df.empty: continue
            
            group = group.sort_values('DT_FIM_EXERC')
            
            # Calculate 5-Year Net Margin Avg
            # Margin = Net Income / Revenue
            # Handle ZeroDivision
            group['net_margin'] = group.apply(lambda row: row['net_income'] / row['revenue'] if row['revenue'] and row['revenue'] != 0 else 0, axis=1)
            group['avg_margin_5y'] = group['net_margin'].rolling(window=5, min_periods=1).mean()
            
            # Iterating rows
            for idx, row in group.iterrows():
                ref_date = row['DT_FIM_EXERC']
                
                # Get Price
                # Use asof or get nearest previous
                try:
                    # Pad ensures we take the last known price if exact date is missing (e.g. weekend)
                    price_idx = prices_df.index.get_indexer([ref_date], method='pad')[0]
                    if price_idx == -1:
                        # Try to look slightly ahead if it's the very beginning?
                        # Or just skip.
                        curr_row = prices_df.iloc[0] if len(prices_df) > 0 else None
                    else:
                        curr_row = prices_df.iloc[price_idx]
                except:
                    curr_row = None
                
                if curr_row is None: continue
                
                price = curr_row['close']
                adj_close = curr_row['adjclose']
                
                # --- METRICS ---
                
                # 1. P/L (Price / Earnings)
                # Need Shares Count. Approximation: EPS is provided by CVM as 'eps'.
                # EPS from CVM is usually reliable but sometimes scaled by 1000 if report is in Thousands.
                # Heuristic: If P/L is extremely low (e.g. < 0.1), try dividing EPS by 1000.
                eps = row.get('eps', 0)
                p_l = 0
                if eps and eps != 0:
                    raw_pl = price / eps
                    if 0 < raw_pl < 0.1:
                        # Likely EPS allows for thousands scale
                        eps = eps / 1000
                        p_l = price / eps
                    elif -0.1 < raw_pl < 0:
                         eps = eps / 1000
                         p_l = price / eps
                    else:
                        p_l = raw_pl
                
                # 2. ROE (Return on Equity) = Net Income / Equity
                equity = row.get('equity', 0)
                roe = (row['net_income'] / equity) if equity and equity != 0 else 0
                
                # 3. ROIC (Return on Invested Capital)
                # ROIC = NOPAT / Invested Capital
                # NOPAT = EBIT * (1 - T)
                # Invested Capital = Equity + Net Debt
                nopat = row.get('ebit', 0) * (1 - self.TAX_RATE)
                net_debt = row.get('net_debt', 0)
                invested_capital = equity + net_debt
                roic = (nopat / invested_capital) if invested_capital and invested_capital != 0 else 0
                
                # 4. DY (Dividend Yield)
                # Dividends Paid (Cash Flow) / Price
                # Note: Dividends Paid is usually negative in CVM (Outflow). Take abs.
                # Also, this is TOTAL dividends. Price is PER SHARE.
                # We need Div Per Share. 
                # Approximation: DivYield = (Total Divs / Net Income) * (Net Income / Market Cap) ?
                # Payout Ratio * (1 / P_L).
                # Payout = Div / Net Income.
                # DY = (Div / Net Income) * (E / P) = Div / (P * Shares) -> Wait.
                # Simpler: DY = (Total Divs / Total Net Income) * (Earnings Yield)
                # Let's calculate Payout Ratio first.
                payout = abs(row.get('dividends_paid', 0)) / row['net_income'] if row['net_income'] and row['net_income'] != 0 else 0
                # Earnings Yield = 1 / P_L
                earnings_yield = (1 / p_l) if p_l and p_l != 0 else 0
                dy = payout * earnings_yield
                
                # 5. Total Return (CAGR) - 1 Year
                # Return from 1 year ago to now
                dt_1y = ref_date - pd.DateOffset(years=1)
                idx_1y = prices_df.index.get_indexer([dt_1y], method='pad')[0]
                total_return_1y = 0.0
                if idx_1y != -1:
                    price_1y = prices_df.iloc[idx_1y]['adjclose']
                    if price_1y > 0:
                        total_return_1y = (adj_close / price_1y) - 1

                results.append({
                    'ticker': ticker,
                    'company_name': cvm_name,
                    'date': ref_date.strftime('%Y-%m-%d'),
                    'revenue': row.get('revenue'),
                    'net_income': row.get('net_income'),
                    'ebit': row.get('ebit'),
                    'net_margin': row['net_margin'],
                    'avg_margin_5y': row['avg_margin_5y'],
                    'roe': roe,
                    'roic': roic,
                    'p_l': p_l,
                    'dy': dy,
                    'total_return_1y': total_return_1y,
                    'price': price,
                    'adj_close': adj_close,
                    'net_debt': row.get('net_debt'),
                    'equity': row.get('equity'),
                    'dividends_paid': row.get('dividends_paid')
                })
        
        return pd.DataFrame(results)

    def run(self):
        """
        Main execution method.
        """
        print("Starting Data Processor...")
        df_fin, price_map, tickers_df = self.load_data()
        
        print("Mapping CVM Companies to Tickers...")
        mapping = self.map_cvm_to_tickers(df_fin, tickers_df)
        print(f"Mapped {len(mapping)} companies.")
        
        print("Calculating Multiples...")
        df_results = self.calculate_multiples(df_fin, price_map, mapping)
        
        print(f"Generated {len(df_results)} records.")
        output_path = "web/public/data.json"
        
        # Transform to format suitable for frontend
        # Structure: {ticker: [ {date: ..., p_l: ...}, ... ]}
        final_json = {}
        for ticker, group in df_results.groupby('ticker'):
            final_json[ticker] = group.to_dict(orient='records')
            
        with open(output_path, 'w') as f:
            json.dump(final_json, f, indent=2)
            
        print(f"Data saved to {output_path}")

if __name__ == "__main__":
    dp = DataProcessor()
    dp.run()
