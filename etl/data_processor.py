
import pandas as pd
import json
import os
import numpy as np
from datetime import datetime
import difflib
import unicodedata
import re

class DataProcessor:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.processed_dir = os.path.join(data_dir, "processed")
        self.cvm_path = os.path.join(self.processed_dir, "cvm_financials_history.csv")
        self.price_path = os.path.join(self.processed_dir, "price_history.json")
        self.fundamentus_path = "data/processed/fundamentus_tickers.csv"
        self.mapping_path = os.path.join(self.processed_dir, "cvm_ticker_map.json")
        self.manual_overrides_path = os.path.join("data", "cvm_ticker_overrides.json")
        self.delistings_path = os.path.join(self.processed_dir, "reference_delistings.json")
        self.classification_path = os.path.join(self.processed_dir, "reference_classification.json")
        self.delistings_map = self._load_delistings_map()
        self.classification_map = self._load_classification_map()
        self.ignore_companies = self._load_ignore_set()
        self.price_meta = {}
        
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
        self.price_meta = {}
        for ticker, data in price_map.items():
            meta = {}
            records = data
            if isinstance(data, dict):
                meta = data.get('meta') or {}
                records = data.get('prices') or data.get('data') or []
            if not records:
                continue
            pdf = pd.DataFrame(records)
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
                base_ticker = ticker.replace('.SA', '')
                self.price_meta[base_ticker] = meta or {}
            
        tickers_df = pd.DataFrame()
        if os.path.exists(self.fundamentus_path):
            tickers_df = pd.read_csv(self.fundamentus_path)
            
        return df_fin, processed_prices, tickers_df

    def _sanitize_text(self, text):
        if text is None:
            return ""
        if not isinstance(text, str):
            text = str(text)
        normalized = unicodedata.normalize('NFKD', text)
        ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
        ascii_text = ascii_text.upper()
        ascii_text = ascii_text.replace('S.A.', ' ').replace('S/A', ' ')
        ascii_text = re.sub(r'[^A-Z0-9 ]', ' ', ascii_text)
        ascii_text = re.sub(r'\s+', ' ', ascii_text)
        replacements = {
            r'\bBCO\b': 'BANCO',
            r'\bCIA\b': 'COMPANHIA',
            r'\bCTEEP\b': 'COMPANHIA TRANSMISSAO ENERGIA ELETRICA PAULISTA',
        }
        for pattern, repl in replacements.items():
            ascii_text = re.sub(pattern, repl, ascii_text)
        return ascii_text.strip()

    def _load_manual_overrides(self):
        if not os.path.exists(self.manual_overrides_path):
            return {}
        try:
            with open(self.manual_overrides_path, 'r') as fh:
                raw = json.load(fh)
                return {str(k): v for k, v in raw.items()}
        except Exception:
            return {}

    def _load_delistings_map(self):
        if not os.path.exists(self.delistings_path):
            return {}
        try:
            with open(self.delistings_path, 'r', encoding='utf-8') as fh:
                raw = json.load(fh)
            return raw or {}
        except Exception:
            return {}

    def _load_classification_map(self):
        if not os.path.exists(self.classification_path):
            return {}
        try:
            with open(self.classification_path, 'r', encoding='utf-8') as fh:
                raw = json.load(fh)
            return raw or {}
        except Exception:
            return {}

    def _load_ignore_set(self):
        ignore_path = os.path.join(self.data_dir, "ignored_cvm_companies.json")
        if not os.path.exists(ignore_path):
            return set()
        try:
            with open(ignore_path, 'r', encoding='utf-8') as fh:
                names = json.load(fh) or []
            sanitized = {self._sanitize_text(name) for name in names if name}
            return sanitized
        except Exception:
            return set()

    def _match_delisting(self, company_name: str):
        if not self.delistings_map:
            return None
        target = self._sanitize_text(company_name)
        best_code = None
        best_info = None
        best_score = 0.0

        for code, info in self.delistings_map.items():
            normalized = info.get('company_name_normalized') or self._sanitize_text(info.get('company_name'))
            if not normalized:
                continue
            score = difflib.SequenceMatcher(None, target, normalized).ratio()
            if score > best_score:
                best_code = code
                best_info = info
                best_score = score

        if best_score >= 0.8 and best_info:
            return best_info
        return None

    def map_cvm_to_tickers(self, df_fin, tickers_df):
        """
        Maps CVM 'DENOM_CIA' to Tickers using Fundamentus data.
        Returns a dict {cvm_name: ticker}
        """
        if tickers_df.empty:
            return {}

        overrides_raw = self._load_manual_overrides()
        overrides_by_cd = {}
        overrides_by_name = {}
        for key, value in overrides_raw.items():
            key_str = str(key)
            if key_str.isdigit():
                overrides_by_cd[key_str] = value
            else:
                overrides_by_name[self._sanitize_text(key_str)] = value
        existing_map = {}
        if os.path.exists(self.mapping_path):
            try:
                with open(self.mapping_path, 'r') as fh:
                    existing_map = json.load(fh) or {}
            except Exception:
                existing_map = {}

        tickers = tickers_df['ticker'].dropna().astype(str).str.upper().unique()
        ticker_aliases = {
            ticker: re.sub(r'[^A-Z]', '', ticker)
            for ticker in tickers
        }

        meta_lookup = {}
        for ticker, meta in self.price_meta.items():
            sanitized_names = set()
            if isinstance(meta, dict):
                short = self._sanitize_text(meta.get('shortName'))
                long = self._sanitize_text(meta.get('longName'))
                if short:
                    sanitized_names.add(short)
                if long:
                    sanitized_names.add(long)
            if sanitized_names:
                meta_lookup[ticker.upper()] = sanitized_names

        result = {}
        unmatched = []

        unique_companies = df_fin[['CD_CVM', 'DENOM_CIA']].drop_duplicates()

        for _, row in unique_companies.iterrows():
            cd_cvm = row.get('CD_CVM')
            name = row.get('DENOM_CIA')
            cd_key = str(int(cd_cvm)) if not pd.isna(cd_cvm) else None
            sanitized_name = self._sanitize_text(name)

            if sanitized_name in self.ignore_companies:
                continue

            ticker = None

            if cd_key and cd_key in overrides_by_cd:
                ticker = overrides_by_cd[cd_key]
            elif sanitized_name in overrides_by_name:
                ticker = overrides_by_name[sanitized_name]
            elif cd_key and cd_key in existing_map:
                ticker = existing_map[cd_key]
            else:
                # Try match via meta lookup (Yahoo names)
                for candidate, names in meta_lookup.items():
                    if sanitized_name in names:
                        ticker = candidate.replace('.SA', '')
                        break
                if ticker is None:
                    for candidate, names in meta_lookup.items():
                        if any(name_fragment in sanitized_name for name_fragment in names):
                            ticker = candidate.replace('.SA', '')
                            break

                if ticker is None:
                    # Match by base prefix (first 4 letters)
                    base_candidate = re.sub(r'[^A-Z]', '', sanitized_name)
                    prefix = base_candidate[:4]
                    if prefix:
                        candidates = [
                            t for t, alias in ticker_aliases.items()
                            if alias.startswith(prefix)
                        ]
                        if candidates:
                            ticker = candidates[0]

                if ticker is None:
                    # Fuzzy match across aliases
                    alias_values = list(ticker_aliases.values())
                    match = difflib.get_close_matches(base_candidate, alias_values, n=1, cutoff=0.75)
                    if match:
                        matched_alias = match[0]
                        for t, alias in ticker_aliases.items():
                            if alias == matched_alias:
                                ticker = t
                                break

                if ticker is None and sanitized_name:
                    best_score = 0.0
                    best_candidate = None
                    for candidate, names in meta_lookup.items():
                        for meta_name in names:
                            score = difflib.SequenceMatcher(None, sanitized_name, meta_name).ratio()
                            if score > 0.8 and score > best_score:
                                best_score = score
                                best_candidate = candidate
                    if best_candidate:
                        ticker = best_candidate.replace('.SA', '')

                if ticker is None and self.classification_map:
                    first_token = sanitized_name.split()[0] if sanitized_name else ""
                    for class_ticker, info in self.classification_map.items():
                        class_name = self._sanitize_text(info.get('trading_name'))
                        if not class_name:
                            continue
                        if first_token and first_token in class_name.split():
                            ticker = class_ticker
                            break
                        score = difflib.SequenceMatcher(None, sanitized_name, class_name).ratio()
                        if score >= 0.8:
                            ticker = class_ticker
                            break

            if ticker:
                normalized_ticker = ticker.replace('.SA', '').upper()
                if normalized_ticker in tickers:
                    result[name] = normalized_ticker
                    if cd_key:
                        existing_map[cd_key] = normalized_ticker
            else:
                unmatched.append(name)

        if existing_map:
            os.makedirs(self.processed_dir, exist_ok=True)
            with open(self.mapping_path, 'w') as fh:
                json.dump(existing_map, fh, indent=2, ensure_ascii=False)

        if unmatched:
            print(f"⚠️  Unmatched CVM companies: {len(unmatched)} (sample: {unmatched[:10]})")

        self.unmatched_companies = unmatched

        return result

    def _build_unmatched_summary(self, df_fin):
        summary = []
        unmatched = getattr(self, "unmatched_companies", [])
        if not unmatched or 'DT_FIM_EXERC' not in df_fin.columns:
            return summary

        df_dates = df_fin[['DENOM_CIA', 'DT_FIM_EXERC']].copy()
        df_dates['DT_FIM_EXERC'] = pd.to_datetime(df_dates['DT_FIM_EXERC'], errors='coerce')

        reference_date = pd.Timestamp("2026-02-11")

        for name in unmatched:
            if self._sanitize_text(name) in self.ignore_companies:
                continue
            subset = df_dates[df_dates['DENOM_CIA'] == name]
            if subset.empty:
                summary.append({
                    "company_name": str(name),
                    "last_report": None,
                    "status": "sem_relatorios",
                    "report_count": 0,
                    "delisting_info": None
                })
                continue

            last_report = subset['DT_FIM_EXERC'].max()
            report_count = subset['DT_FIM_EXERC'].notna().sum()

            if pd.isna(last_report):
                status = "sem_datas_validas"
                iso_date = None
            else:
                iso_date = last_report.strftime('%Y-%m-%d')
                years_diff = (reference_date - last_report).days / 365.25
                if years_diff <= 2:
                    status = "ativo_recente"
                elif years_diff <= 5:
                    status = "possivel_reestruturacao"
                else:
                    status = "historico_antigo_ou_deslistado"

            # Tenta cruzar com a lista oficial de cancelamentos (base four-letter)
            delisting_info = self._match_delisting(str(name))
            if delisting_info:
                status = "registrado_cancelamento"

            summary.append({
                "company_name": str(name),
                "last_report": iso_date,
                "status": status,
                "report_count": int(report_count),
                "delisting_info": delisting_info
            })

        return summary

    def _build_share_class_groups(self, fundamentus_df):
        """Agrupa tickers por base (antes do sufixo numérico)."""
        groups = {}
        if fundamentus_df.empty or 'ticker' not in fundamentus_df.columns:
            return groups

        for raw in fundamentus_df['ticker'].dropna().astype(str):
            ticker = raw.strip().upper()
            if not ticker:
                continue
            base = re.sub(r'\d+$', '', ticker)
            if not base:
                continue
            groups.setdefault(base, set()).add(ticker)
        return groups

    def duplicate_share_classes(self, final_json, price_map, fundamentus_df):
        """
        Duplica métricas para classes PN que possuem preço mas não receberam dados
        fundamentalistas (ex.: ITUB3 -> ITUB4).
        """
        groups = self._build_share_class_groups(fundamentus_df)
        if not groups:
            return final_json

        price_universe = {
            key.replace(".SA", "").upper()
            for key in (price_map.keys() if isinstance(price_map, dict) else [])
        }

        for base, tickers in groups.items():
            existing = [t for t in tickers if t in final_json]
            if not existing:
                continue

            source_ticker = sorted(existing)[0]
            source_records = final_json.get(source_ticker, [])
            if not source_records:
                continue

            for alias in tickers:
                if alias in final_json:
                    continue
                if alias not in price_universe:
                    continue
                cloned = []
                for record in source_records:
                    cloned_record = dict(record)
                    cloned_record['ticker'] = alias
                    cloned.append(cloned_record)
                if cloned:
                    final_json[alias] = cloned

        return final_json

    def _scale_shares(self, ticker: str, raw_shares: float, price: float, revenue_ttm: float, net_income_ttm: float, cache: dict) -> float:
        if not raw_shares or raw_shares <= 0:
            return 0
        scale = 1.0
        market_cap_est = (price * raw_shares) if price else None
        should_upscale = (
            raw_shares is not None
            and raw_shares < 5e7  # less than 50M shares usually indicates missing scale
            and market_cap_est is not None
            and market_cap_est < 1e10
            and (
                (revenue_ttm and revenue_ttm > 2e10)
                or (net_income_ttm and net_income_ttm > 5e8)
            )
        )
        if should_upscale:
            scale = 1000.0
        cache[ticker] = scale
        return raw_shares * scale

    def calculate_multiples(self, df_fin, price_map, mapping, fundamentus_df):
        results = []
        
        fundamentus_map = {}
        fundamentus_pl_map = {}
        fundamentus_margin_map = {}
        fund_df = fundamentus_df.copy() if not fundamentus_df.empty else fundamentus_df
        if not fund_df.empty and 'ticker' in fund_df.columns:
            fund_df['ticker'] = fund_df['ticker'].astype(str).str.upper()

        if not fund_df.empty and {'ticker', 'pvp'}.issubset(set(fund_df.columns)):
            fundamentus_map = (
                fund_df[['ticker', 'pvp']]
                .dropna()
                .drop_duplicates(subset=['ticker'])
                .set_index('ticker')['pvp']
                .to_dict()
            )

        if not fund_df.empty and {'ticker', 'pl'}.issubset(set(fund_df.columns)):
            fundamentus_pl_map = (
                fund_df[['ticker', 'pl']]
                .dropna()
                .drop_duplicates(subset=['ticker'])
                .set_index('ticker')['pl']
                .to_dict()
            )

        if not fund_df.empty and {'ticker', 'mrgliq'}.issubset(set(fund_df.columns)):
            fundamentus_margin_map = (
                fund_df[['ticker', 'mrgliq']]
                .dropna()
                .drop_duplicates(subset=['ticker'])
                .set_index('ticker')['mrgliq']
                .to_dict()
            )

        share_scale_cache = {}
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

            # Trailing metrics (Quarterly contributions + TTM)
            metrics_for_ttm = ['revenue', 'net_income', 'ebit', 'dividends_paid']
            years = group['DT_FIM_EXERC'].dt.year

            for metric in metrics_for_ttm:
                quarter_col = f"{metric}_quarter"
                ttm_col = f"{metric}_ttm"

                group[quarter_col] = group.groupby(years)[metric].diff().fillna(group[metric])

                group[ttm_col] = group[quarter_col].rolling(window=4, min_periods=1).sum()

            revenue_ttm = pd.to_numeric(group['revenue_ttm'], errors='coerce').fillna(0.0)
            net_income_ttm = pd.to_numeric(group['net_income_ttm'], errors='coerce').fillna(0.0)
            with np.errstate(divide='ignore', invalid='ignore'):
                margins = np.where(revenue_ttm != 0, net_income_ttm / revenue_ttm, 0.0)
            group['net_margin_ttm'] = margins.astype(float)

            fallback_margin_value = fundamentus_margin_map.get(ticker)
            if fallback_margin_value is not None:
                mask_margin = (group['revenue_ttm'] == 0) & (group['net_income_ttm'] != 0)
                group.loc[mask_margin, 'net_margin_ttm'] = float(fallback_margin_value)
            group['net_margin_ttm'] = group['net_margin_ttm'].astype(float)
            group['avg_margin_5y'] = group['net_margin_ttm'].rolling(window=5, min_periods=1).mean()
            
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

                net_income_ttm = row.get('net_income_ttm') or 0
                revenue_ttm = row.get('revenue_ttm') or 0
                ebit_ttm = row.get('ebit_ttm') or 0
                dividends_ttm = abs(row.get('dividends_paid_ttm') or 0)
                net_margin = row.get('net_margin_ttm') or 0
                avg_margin = row.get('avg_margin_5y')
                equity = row.get('equity', 0) or 0

                # 1. P/L (Price / Earnings)
                # Need Shares Count. Approximation: EPS is provided by CVM as 'eps'.
                # EPS from CVM is usually reliable but sometimes scaled by 1000 if report is in Thousands.
                # Heuristic: If P/L is extremely low (e.g. < 0.1), try dividing EPS by 1000.
                shares_raw = row.get('shares_outstanding') or 0
                shares_outstanding = self._scale_shares(
                    ticker,
                    shares_raw,
                    price,
                    revenue_ttm,
                    net_income_ttm,
                    share_scale_cache,
                )
                eps_ttm = None
                p_l = 0
                if shares_outstanding:
                    eps_ttm = (net_income_ttm / shares_outstanding) if net_income_ttm is not None else 0
                    if eps_ttm not in (None, 0):
                        p_l = price / eps_ttm
                else:
                    eps_cvm = row.get('eps', 0)
                    if eps_cvm and eps_cvm != 0:
                        raw_pl = price / eps_cvm
                        if 0 < raw_pl < 0.1:
                            eps_cvm = eps_cvm / 1000
                            raw_pl = price / eps_cvm
                        elif -0.1 < raw_pl < 0:
                            eps_cvm = eps_cvm / 1000
                            raw_pl = price / eps_cvm
                        p_l = raw_pl
                        eps_ttm = eps_cvm
                
                # 2. ROE (Return on Equity) = Net Income / Equity
                fundamentus_pvp = fundamentus_map.get(ticker) if fundamentus_map else None
                book_equity_alt = None
                if (
                    fundamentus_pvp
                    and fundamentus_pvp > 0
                    and shares_outstanding
                    and price
                ):
                    book_equity_alt = (price / fundamentus_pvp) * shares_outstanding
                if book_equity_alt:
                    if equity <= 0 or abs(book_equity_alt - equity) / book_equity_alt > 0.5:
                        equity = book_equity_alt
                if equity <= 0 and fundamentus_pvp and fundamentus_pvp > 0 and shares_outstanding and price:
                    equity = book_equity_alt

                roe = (net_income_ttm / equity) if equity and equity != 0 else 0
                
                # 3. ROIC (Return on Invested Capital)
                # ROIC = NOPAT / Invested Capital
                # NOPAT = EBIT * (1 - T)
                # Invested Capital = Equity + Net Debt
                nopat = ebit_ttm * (1 - self.TAX_RATE)
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
                payout = dividends_ttm / net_income_ttm if net_income_ttm and net_income_ttm != 0 else 0
                fallback_pl = fundamentus_pl_map.get(ticker) if fundamentus_pl_map else None
                if (p_l is None or p_l == 0) and fallback_pl is not None and fallback_pl != 0:
                    p_l = fallback_pl

                # Earnings Yield = 1 / P_L
                earnings_yield = (1 / p_l) if p_l and p_l != 0 else 0
                if shares_outstanding and price:
                    dy = (dividends_ttm / shares_outstanding) / price
                else:
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

                class_info = self.classification_map.get(ticker, {})
                sector_value = (class_info.get('sector') or "").upper()
                subsector_value = (class_info.get('subsector') or "").upper()
                cvm_upper = str(cvm_name).upper()

                is_insurer = any(keyword in sector_value for keyword in ["SEGURO", "PREVID"]) or \
                    any(keyword in subsector_value for keyword in ["SEGURO", "PREVID"])

                if net_margin == 0 and is_insurer:
                    net_margin = earnings_yield
                    if not avg_margin:
                        avg_margin = earnings_yield
                elif net_margin == 0 and revenue_ttm == 0 and net_income_ttm != 0:
                    # Holdings and companhias sem receita reconhecida, usar earnings yield
                    net_margin = earnings_yield
                    if not avg_margin:
                        avg_margin = earnings_yield

                p_vp = fundamentus_map.get(ticker)
                if (p_vp is None or p_vp == 0) and p_l and roe:
                    try:
                        p_vp = p_l * roe
                    except Exception:
                        p_vp = 0

                results.append({
                    'ticker': ticker,
                    'company_name': cvm_name,
                    'date': ref_date.strftime('%Y-%m-%d'),
                    'revenue': row.get('revenue'),
                    'net_income': row.get('net_income'),
                    'ebit': row.get('ebit'),
                    'net_margin': net_margin,
                    'avg_margin_5y': avg_margin,
                    'roe': roe,
                    'roic': roic,
                    'p_l': p_l,
                    'p_vp': p_vp or 0,
                    'dy': dy,
                    'net_income_ttm': net_income_ttm,
                    'revenue_ttm': revenue_ttm,
                    'total_return_1y': total_return_1y,
                    'price': price,
                    'adj_close': adj_close,
                    'net_debt': row.get('net_debt'),
                    'equity': equity,
                    'dividends_paid': row.get('dividends_paid'),
                    'shares_outstanding': shares_outstanding,
                    'eps_ttm': eps_ttm if eps_ttm is not None else row.get('eps')
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
        df_results = self.calculate_multiples(df_fin, price_map, mapping, tickers_df)
        
        print(f"Generated {len(df_results)} records.")
        output_path = "web/public/data.json"
        
        # Transform to format suitable for frontend
        # Structure: {ticker: [ {date: ..., p_l: ...}, ... ]}
        final_json = {}
        for ticker, group in df_results.groupby('ticker'):
            group = group.sort_values('date')
            final_json[ticker] = group.to_dict(orient='records')

        final_json = self.duplicate_share_classes(final_json, price_map, tickers_df)
            
        with open(output_path, 'w') as f:
            json.dump(final_json, f, indent=2)
            
        print(f"Data saved to {output_path}")

        unmatched_summary = self._build_unmatched_summary(df_fin)
        if unmatched_summary:
            summary_path = os.path.join(self.processed_dir, "unmatched_companies.json")
            with open(summary_path, 'w') as summary_file:
                json.dump(unmatched_summary, summary_file, indent=2, ensure_ascii=False)
            print(f"Unmatched companies summary saved to {summary_path}")
        else:
            print("No unmatched companies to report.")
        
        return final_json

if __name__ == "__main__":
    dp = DataProcessor()
    dp.run()
