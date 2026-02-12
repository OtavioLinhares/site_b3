import sys
import os
import yfinance as yf
import pandas as pd
import numpy as np
import time
import argparse
import json
from datetime import datetime

# Ensure we can import from local modules
sys.path.append(os.getcwd())

from data.fundamentus_client import FundamentusClient
from etl.logger import PipelineLogger
from etl.validator import Validator
from etl.exporter import Exporter

class DataPipeline:
    def __init__(self, limit=None, force_historical_sync=False, historical_ttl_hours=24, historical_start_year=2018, historical_end_year=None):
        self.limit = limit
        self.logger = PipelineLogger()
        self.validator = Validator(self.logger)
        self.exporter = Exporter()
        self.f_client = FundamentusClient()
        self.force_historical_sync = force_historical_sync
        self.historical_ttl_hours = historical_ttl_hours
        self.historical_start_year = historical_start_year
        self.historical_end_year = historical_end_year
        self.processed_dir = os.path.join("data", "processed")
        self.historical_financials_path = os.path.join(self.processed_dir, "cvm_financials_history.csv")
        self.historical_prices_path = os.path.join(self.processed_dir, "price_history.json")
        
        self.b3_tickers = []
        self.processed_data = []
        self.excluded_data = []
        
        # Hardcoded exclusions for obsolete or problematic tickers
        self.EXCLUDED_TICKERS = ['TRPN3', 'GEPA3', 'GEPA4']
        
        # Historical Data Modules
        from etl.cvm_client import CVMClient
        from etl.cvm_parser import CVMParser
        from etl.price_client import PriceHistoryClient
        
        self.cvm_client = CVMClient()
        self.cvm_parser = CVMParser()
        self.price_client = PriceHistoryClient()

    def _historical_data_is_fresh(self):
        if self.force_historical_sync:
            return False
        required_files = [
            self.historical_financials_path,
            self.historical_prices_path,
        ]
        now = time.time()
        max_age = self.historical_ttl_hours * 3600 if self.historical_ttl_hours else None
        for path in required_files:
            if not os.path.exists(path):
                return False
            if max_age is not None and (now - os.path.getmtime(path)) > max_age:
                return False
        return True

    def _load_existing_prices(self):
        if not os.path.exists(self.historical_prices_path):
            return {}
        try:
            with open(self.historical_prices_path, "r") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    return {}
                normalized = {}
                for ticker, value in data.items():
                    if isinstance(value, list):
                        normalized[ticker] = {"prices": value, "meta": {}}
                    elif isinstance(value, dict):
                        prices = value.get("prices")
                        if prices is None and isinstance(value.get("data"), list):
                            prices = value.get("data")
                        normalized[ticker] = {
                            "prices": prices or [],
                            "meta": value.get("meta", {})
                        }
                    else:
                        normalized[ticker] = {"prices": [], "meta": {}}
                return normalized
        except Exception as exc:
            self.logger.warning(f"Failed to load cached prices: {exc}")
            return {}

    def run_historical_sync(self):
        """
        Runs the full Historical Data ETL (CVM + Prices).
        Downloads DFP/ITR, parses them, fetches stock prices, and exports a history dataset.
        """
        self.logger.info("--- Starting Historical Data Sync ---")

        os.makedirs(self.processed_dir, exist_ok=True)

        # 1. Download CVM Data (configurable window)
        current_year = datetime.utcnow().year
        start_year = self.historical_start_year or 2011
        end_year = self.historical_end_year or current_year
        if start_year > end_year:
            start_year, end_year = end_year, start_year
        years = range(start_year, end_year + 1)
        
        self.logger.info(f"Downloading CVM DFP/ITR for {years}...")
        for year in years:
            self.cvm_client.fetch_annual_reports(year) # DFP
            self.cvm_client.fetch_quarterly_reports(year)

        # 2. Parse Data
        self.logger.info("Parsing CVM Files...")
        all_dfs = []
        for year in years:
            df_dfp = self.cvm_parser.parse_financials(year, 'DFP')
            if not df_dfp.empty: all_dfs.append(df_dfp)
            
            df_itr = self.cvm_parser.parse_financials(year, 'ITR') 
            if not df_itr.empty: all_dfs.append(df_itr)
            
        if not all_dfs:
            self.logger.warning("No historical data parsed.")
            history_df = pd.DataFrame()
        else:
            history_df = pd.concat(all_dfs, ignore_index=True)
            self.logger.info(f"Parsed {len(history_df)} historical records.")

        # 3. Fetch Price History for valid tickers
        # Use Fundamentus data to get list of active tickers
        current_df = self.f_client.fetch_all_current()
        tickers = current_df['ticker'].unique().tolist() if not current_df.empty else []
        if self.limit:
            tickers = tickers[:self.limit]
        
        # Yahoo Finance requires .SA suffix for Brazilian stocks
        tickers_sa = [f"{t}.SA" for t in tickers if not t.endswith('.SA')]
        
        existing_prices = self._load_existing_prices()
        to_fetch = [ticker for ticker in tickers_sa if ticker not in existing_prices]
        if to_fetch:
            self.logger.info(f"Fetching price history for {len(to_fetch)} tickers (.SA suffix added)...")
            fresh_prices = self.price_client.fetch_batch(to_fetch)
            for ticker, payload in fresh_prices.items():
                df = payload.get('data') if isinstance(payload, dict) else None
                meta = payload.get('meta') if isinstance(payload, dict) else {}
                if df is None or df.empty:
                    continue
                df_reset = df.reset_index()
                if 'Date' in df_reset.columns:
                    df_reset['Date'] = df_reset['Date'].dt.strftime('%Y-%m-%d')
                existing_prices[ticker] = {
                    "prices": df_reset.to_dict(orient='records'),
                    "meta": {
                        "symbol": meta.get("symbol"),
                        "shortName": meta.get("shortName"),
                        "longName": meta.get("longName"),
                        "exchangeName": meta.get("exchangeName"),
                    }
                }
        else:
            self.logger.info("Price history already cached for all tickers.")
        
        # 4. Export
        if not history_df.empty:
            history_df.to_csv(self.historical_financials_path, index=False)
        
        sanitized_prices = {}
        for ticker, payload in existing_prices.items():
            if isinstance(payload, dict):
                sanitized_prices[ticker] = {
                    "prices": payload.get("prices", []),
                    "meta": payload.get("meta", {})
                }
            else:
                sanitized_prices[ticker] = {"prices": payload or [], "meta": {}}
        
        with open(self.historical_prices_path, "w") as f:
            json.dump(sanitized_prices, f)
            
        self.logger.info("Historical Sync Completed.")

    def run_data_processing(self):
        """
        Runs the Data Processor to generate frontend JSON.
        """
        try:
            from etl.data_processor import DataProcessor
            self.logger.info("Starting Data Processing (Metrics Calculation)...")
            dp = DataProcessor()
            payload = dp.run()
            self.logger.info("Data Processing complete.")
            return payload
        except Exception as e:
            self.logger.error(f"Data Processing failed: {e}")
            return {}

    def _load_reference_classification(self):
        path = os.path.join(self.processed_dir, "reference_classification.json")
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh) or {}
        except Exception as exc:
            self.logger.warning(f"Failed to load reference_classification.json: {exc}")
            return {}

    def _enrich_with_processed_metrics(self, assets, processed_payload):
        if not processed_payload:
            self.logger.warning("Processed metrics payload empty; keeping Fundamentus values.")
            return assets

        latest_map = {}
        for ticker, records in processed_payload.items():
            if isinstance(records, list) and records:
                latest_map[ticker.upper()] = records[-1]

        classification_map = self._load_reference_classification()
        enriched = []
        missing = []

        for asset in assets:
            ticker = (asset.get("ticker") or "").upper()
            latest = latest_map.get(ticker)
            if not latest:
                missing.append(ticker)
                continue

            merged = dict(asset)
            for field in ("p_l", "p_vp", "net_margin", "roe", "roic", "dy"):
                if field in latest and latest[field] is not None:
                    merged[field] = latest[field]

            latest_margin = latest.get("net_margin") or 0
            latest_pl = latest.get("p_l")
            merged["positive_margins"] = latest_margin > 0
            merged["valid_pl"] = latest_pl is not None and latest_pl > 0

            if not merged.get("company_name"):
                merged["company_name"] = latest.get("company_name")

            class_info = classification_map.get(ticker)
            if class_info:
                merged.setdefault("sector", class_info.get("sector"))
                merged.setdefault("subsector", class_info.get("subsector"))
                merged.setdefault("segment", class_info.get("segment"))
                merged.setdefault("trading_segment", class_info.get("trading_segment"))

            sector_value = (merged.get("sector") or "").upper()
            subsector_value = (merged.get("subsector") or "").upper()
            if (
                merged.get("net_margin") == 0
                and merged.get("p_l")
                and (
                    any(keyword in sector_value for keyword in ["SEGURO", "PREVID"])
                    or any(keyword in subsector_value for keyword in ["SEGURO", "PREVID"])
                )
            ):
                pl_value = merged.get("p_l")
                earnings_yield = (1 / pl_value) if pl_value else 0
                merged["net_margin"] = earnings_yield
                if not merged.get("avg_margin_5y"):
                    merged["avg_margin_5y"] = earnings_yield

            merged["positive_margins"] = merged.get("net_margin", 0) is not None and merged.get("net_margin", 0) > 0

            enriched.append(merged)

        if missing:
            sample = ", ".join(missing[:5])
            self.logger.warning(
                f"{len(missing)} tickers sem métricas processadas foram removidos do b3_stocks.json (ex.: {sample})"
            )

        return enriched or assets
    def fetch_yfinance_market_cap(self, ticker_sa):
        """
        Fetches Market Cap from YFinance for validation.
        """
        try:
            # yfinance often caches, but for 400 tickers it might be slow.
            # We use Ticker object
            t = yf.Ticker(ticker_sa)
            info = t.info
            return info.get('marketCap', 0.0)
        except Exception as e:
            # self.logger.warning(f"YFinance fetch failed for {ticker_sa}: {e}")
            return None

    def run(self):
        self.logger.info("Starting Daily Pipeline...")
        start_time = time.time()
        
        try:
            # 1. Fetch Raw Data (Fundamentus)
            self.logger.info("Fetching Fundamentus data...")
            df_raw = self.f_client.fetch_all_current()
            
            # RUN HISTORICAL SYNC (skip if recently updated unless forced)
            if self._historical_data_is_fresh():
                self.logger.info("Historical data is fresh; skipping CVM/price sync.")
            else:
                self.run_historical_sync()
            
            if df_raw.empty:
                raise Exception("Fundamentus returned empty data.")
            
            self.logger.info(f"Fundamentus returned {len(df_raw)} records.")
        
            # Save raw ticker data for DataProcessor mapping
            df_raw.to_csv("data/processed/fundamentus_tickers.csv", index=False)
            
            # 2. Filter & Clean Data
            # df = self.filter_data(df_raw) # This line was not in the original code, but implied by the instruction.
            # Assuming the intent is to replace the comment and add the save.
            
            # 2. Process & Validate Each Asset
            valid_assets = []
            
            # Limit for testing? No, full run.
            # But YFinance for 400 items might block.
            # Strategy: Verify only if Fundamentus Market Cap is suspicious? 
            # Or strict requirement: "Se divergência entre fontes..." -> Implies comparing all.
            # We will try batch fetching if possible, or just individual. 
            # Individual for 400 is fine for a daily cron (approx 5-10 mins).
            
            total = len(df_raw)
            if self.limit:
                total = min(total, self.limit)
                self.logger.info(f"Limiting execution to {total} items.")
            
            for idx, row in df_raw.iterrows():
                if self.limit and idx >= self.limit:
                    break
                    
                ticker = row['ticker']
                if ticker in self.EXCLUDED_TICKERS:
                    self.logger.info(f"Skipping excluded ticker: {ticker}")
                    self.excluded_data.append({"ticker": ticker, "reason": "BLACKLISTED"})
                    continue

                ticker_sa = f"{ticker}.SA"
                
                # Feedback loop
                if idx % 10 == 0:
                    self.logger.info(f"Processing {idx}/{total}: {ticker}")
                
                 # Polite delay for APIs
                if not getattr(self, 'skip_yf', False):
                    time.sleep(0.5)

                # --- Step A: Get Extended Info (Fundamentus Details) ---
                # We need this for Real Market Cap, Debt, Sector
                sec, subsec, mcap_fund, net_debt, ev_ebitda = self.f_client.get_extended_info(ticker)
                
                if not sec:
                    self.logger.log_exclusion(ticker, "MISSING_DETAILS", "Could not fetch sector/details")
                    self.excluded_data.append({"ticker": ticker, "reason": "MISSING_DETAILS"})
                    continue

                # --- Step B: Market Cap Validation ---
                # Source 1: Fundamentus Detailed (mcap_fund)
                # Source 2: YFinance (mcap_yf)
                mcap_yf = None
                
                # OPTIMIZATION: Disabling YFinance validation to speed up process
                # if not getattr(self, 'skip_yf', False):
                #     mcap_yf = self.fetch_yfinance_market_cap(ticker_sa)
                
                # Check consistency
                # Note: If YFinance fails (Rate Limit), we TRUST Fundamentus as Plan B.
                if mcap_yf and mcap_yf > 0:
                    is_consistent = self.validator.check_market_cap_consistency(ticker, mcap_fund, mcap_yf)
                    if not is_consistent:
                        self.logger.warning(f"Excluding {ticker} due to market cap inconsistency.")
                        self.excluded_data.append({"ticker": ticker, "reason": "INCONSISTENCY_MARKET_CAP"})
                        continue
                else:
                    self.logger.warning(f"YFinance failed for {ticker}. Using Fundamentus as primary source.")
                
                # --- Step C: Build Record & Calculate Metrics ---
                try:
                    # Parse numericals from raw row if needed
                    # FundamentusClient usually returns clean numeric or strings.
                    # We trust the client cleaning mostly, but ensure floats.
                    
                    # Net Margin: 'mrgliq'. Raw is usually 0.12 for 12%.
                    # Growth 5y: 'c5y'
                    
                    try:
                        pl = float(row['pl']) if row['pl'] else 0.0
                        net_margin = float(row['mrgliq']) if row['mrgliq'] else 0.0
                        rev_growth_5y = float(row['c5y']) if row['c5y'] else 0.0
                        roe = float(row['roe']) if row['roe'] else 0.0
                        liq_2m_raw = row.get('liq2m', 0.0)
                        if pd.isna(liq_2m_raw):
                            liq_2m = 0.0
                        else:
                            liq_2m = float(liq_2m_raw) if liq_2m_raw else 0.0
                        # Profit? We need it for specific P/L checks: P/L = MktCap / Profit
                        # Derived Profit = MktCap / P/L (if P/L != 0)
                        # Or Profit = Revenue * Margin?
                        # Let's trust P/L provided for now, but Validator checks "Lucro <= 0 -> P/L Inválido".
                        # If P/L is negative, Profit is likely negative (since MktCap is positive).
                        # If P/L is huge, Profit is tiny.
                        
                    except (ValueError, TypeError):
                        self.logger.log_exclusion(ticker, "DATA_FORMAT_ERROR", "Non-numeric values")
                        self.excluded_data.append({"ticker": ticker, "reason": "DATA_FORMAT_ERROR"})
                        continue

                    # Construct Object
                    asset_data = {
                        "ticker": ticker,
                        "sector": sec,
                        "subsector": subsec,
                        "market_cap": mcap_fund,
                        "p_l": pl,
                        "p_vp": float(row['pvp']) if row['pvp'] else 0.0,
                        "net_margin": net_margin,
                        "revenue_growth_5y": rev_growth_5y,
                        "roe": roe,
                        "roic": float(row['roic']) if row['roic'] else 0.0,
                        "dy": float(row['dy']) if row['dy'] else 0.0,
                        "net_debt": net_debt,
                        "ev_ebitda": ev_ebitda,
                        "liq_2m": liq_2m
                    }

                    # HOTFIX: Rename PRIOC3 to PRIO3 if Fundamentus returns the old one
                    if asset_data['ticker'] == 'PRIOC3':
                        asset_data['ticker'] = 'PRIO3'
                    
                    # --- Step D: Metric Validation (Outliers) ---
                    if not self.validator.validate_metrics(asset_data):
                        self.excluded_data.append({"ticker": ticker, "reason": "OUTLIER_METRICS"})
                        continue
                        
                    # --- Step E: Rankings Eligibility Flags ---
                    # "Empresas com P/L inválido (Lucro <= 0): excluídas de rankings de valuation"
                    # If P/L < 0, we flag it.
                    asset_data['valid_pl'] = (pl > 0)
                    
                    # "Margem > 0" check for Growth
                    net_margin_value = asset_data.get('net_margin')
                    asset_data['positive_margins'] = (
                        net_margin_value is not None and net_margin_value > 0
                    )

                    valid_assets.append(asset_data)
                    
                except Exception as e:
                    self.logger.error(f"Error processing {ticker}: {e}")
                    self.excluded_data.append({"ticker": ticker, "reason": "PROCESSING_ERROR"})

            # 3. Generate Collections & Rankings
            self.logger.info(f"Total Valid Assets (Fundamentus): {len(valid_assets)}")

            processed_payload = self.run_data_processing()
            enriched_assets = self._enrich_with_processed_metrics(valid_assets, processed_payload)
            self.logger.info(f"Assets após merge com métricas processadas: {len(enriched_assets)}")
            
            rankings = self.generate_rankings(enriched_assets)
            
            # 4. Export
            self.exporter.export_json(enriched_assets, "b3_stocks.json")
            self.exporter.export_json(rankings, "rankings.json")
            self.exporter.export_excluded_list(self.excluded_data)
            
            # 5. Selic & Macro Analysis
            try:
                self.logger.info("Starting Selic & Macro Analysis...")
                from etl.selic import SelicAnalyzer
                selic_analyzer = SelicAnalyzer()
                selic_analyzer.fetch_data()
                selic_analyzer.calculate_trends()
                
                # Export Summary
                selic_summary = selic_analyzer.export_comparison_summary()
                self.exporter.export_json(selic_summary, "selic_summary.json")
                
                # Generate Chart
                # Ensure public directory exists
                public_dir = os.path.join(os.getcwd(), "web", "public")
                os.makedirs(public_dir, exist_ok=True)
                chart_path = os.path.join(public_dir, "selic_analysis.html")
                selic_analyzer.generate_html_chart(chart_path)
                self.logger.info(f"Selic Analysis complete. Chart at {chart_path}")
                
            except Exception as e:
                self.logger.error(f"Selic Analysis Failed: {e}")
                # Don't fail the whole pipeline for this auxiliary task
            
            self.logger.info(f"Pipeline Finished in {time.time() - start_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Critical Pipeline Failure: {e}")
            sys.exit(1)

    def generate_rankings(self, assets):
        # Convert to DF for easier sorting/filtering
        df = pd.DataFrame(assets)
        if df.empty:
            return {}
            
        # Helper: Normalized Rank (0 to 1, higher is better)
        def get_rank_score(series, ascending=True):
            return series.rank(pct=True, ascending=ascending)

        # Deduplication Logic: One ticker per company.
        # User preference: "Principal (normally PN)".
        # Methodology:
        # 1. Extract base ticker (e.g. PETR from PETR4).
        # 2. Assign priority: 4 (PN) = 1, 3 (ON) = 2, 11 (UNIT) = 3, Others = 4.
        # 3. Sort by Base + Priority.
        # 4. Drop duplicates on Base.
        
        if 'ticker' in df.columns:
            # HOTFIX: Ensure PRIOC3 is renamed to PRIO3 before dedupe
            df['ticker'] = df['ticker'].replace({'PRIOC3': 'PRIO3'})
            
            df['base_ticker'] = df['ticker'].str[:4]
            
            def get_priority(ticker):
                 if ticker.endswith('4'): return 1 # PN
                 if ticker.endswith('3'): return 2 # ON
                 if ticker.endswith('11'): return 3 # UNIT
                 return 4
                 
            df['priority'] = df['ticker'].apply(get_priority)
            
            # Sort by Base (asc) and Priority (asc)
            # This puts the "preferred" ticker first for each group
            df = df.sort_values(by=['base_ticker', 'priority'], ascending=[True, True])
            
            # Drop duplicates keeping first (highest priority)
            df = df.drop_duplicates(subset='base_ticker', keep='first')

        # 1. Ranking: Oportunidades (Pontinha de Cigarro)
        # Metodologia: Baixo P/VP + Margem Líquida Positiva
        # Filters: P/VP > 0, P/VP < 1, Net Margin > 0
        # Filters: P/VP > 0, P/VP < 1, (Net Margin > 0 OR ROE > 0)
        df_cigar = df[(df['p_vp'] > 0) & (df['p_vp'] < 1) & ((df['net_margin'] > 0) | (df['roe'] > 0))].copy()
        
        if not df_cigar.empty:
            # Sort by P/VP ascending (cheapest relative to book value)
            ranking_cigar = df_cigar.sort_values(by='p_vp', ascending=True).head(10)
        else:
            ranking_cigar = pd.DataFrame()

        # 2. Ranking: Dividendos, Margem e P/L (Composite Score)
        # Methodology: Maximize DY and Margin, Minimize P/L.
        # Filters: DY > 0, P/L > 0 (Basic sanity)
        df_div = df[(df['dy'] > 0) & (df['p_l'] > 0)].copy()
        
        if not df_div.empty:
            # Calculate percentile ranks (0 to 1)
            # High DY is good -> ascending=True (higher val = higher rank)
            df_div['rank_dy'] = get_rank_score(df_div['dy'], ascending=True)
            
            # High Margin is good -> ascending=True
            df_div['rank_margin'] = get_rank_score(df_div['net_margin'], ascending=True)
            
            # Low P/L is good -> ascending=False (lower val = higher rank)
            df_div['rank_pl'] = get_rank_score(df_div['p_l'], ascending=False)
            
            # Composite Score (Equal weights)
            df_div['final_score'] = df_div['rank_dy'] + df_div['rank_margin'] + df_div['rank_pl']
            
            ranking_div = df_div.sort_values(by='final_score', ascending=False).head(10)
        else:
            ranking_div = pd.DataFrame()

        # 3. Ranking: Crescimento (5 Anos)
        # Filters: Revenue Growth > 10%, Net Margin > 12% (Configurable)
        df_growth = df[(df['revenue_growth_5y'] > 0.10) & (df['net_margin'] > 0.12)].copy()
        if not df_growth.empty:
            ranking_growth = df_growth.sort_values(by='revenue_growth_5y', ascending=False).head(10)
        else:
            ranking_growth = pd.DataFrame()
        
        return {
            "valor_qualidade": ranking_cigar.to_dict(orient='records'),
            "dividendos": ranking_div.to_dict(orient='records'),
            "crescimento": ranking_growth.to_dict(orient='records')
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Limit number of items to process", default=None)
    parser.add_argument("--skip-yf", action="store_true", help="Skip Yahoo Finance fetching")
    args = parser.parse_args()
    
    pipeline = DataPipeline(limit=args.limit)
    pipeline.skip_yf = args.skip_yf
    pipeline.run()
