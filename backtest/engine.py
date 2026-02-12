import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from backtest.domain import StrategyConfigRequest, BacktestResult, CriteriaGroup, CriteriaItem
from backtest.portfolio import Portfolio
from backtest.data_provider import DataProvider

logger = logging.getLogger("BacktestEngine")

class BacktestEngine:
    def __init__(self, data_provider: DataProvider):
        self.data_provider = data_provider
        self.portfolio = None
        self.config: StrategyConfigRequest = None
        
    def run(self, config: StrategyConfigRequest) -> BacktestResult:
        """Executes the backtest simulation."""
        self.config = config
        self.portfolio = Portfolio(config.initial_capital)
        
        # Initialize Portfolio from Step 5 (Glass Box)
        # We need to set the date to start_date
        start_dt = pd.to_datetime(config.start_date)
        end_dt = pd.to_datetime(config.end_date)
        
        # Ensure benchmarks are loaded (IBOV used for calendar)
        if not self.data_provider.benchmarks:
            self.data_provider.fetch_benchmarks()

        # Timeline
        timeline = self.data_provider.get_market_timeline(start_dt, end_dt) 
        self.total_invested = config.initial_capital

        # Calculate Rebalance Frequency
        rebalance_days = 21 # Default Monthly
        if config.rebalance_period == 'quarterly': rebalance_days = 63
        elif config.rebalance_period == 'yearly': rebalance_days = 252
        elif config.rebalance_period == 'none': rebalance_days = 99999
        
        self.days_since_rebalance = 0

        # Pre-load initial portfolio
        effective_start_dt = timeline[0] if len(timeline) > 0 else start_dt
        
        for item in config.initial_portfolio:
            if item.shares > 0:
                # Try to get market price at effective start date
                market_price_row = self.data_provider.get_latest_price_row(item.ticker, effective_start_dt)
                execution_price = item.price # Fallback to passed price (Mock)
                
                if market_price_row is not None:
                    execution_price = float(market_price_row['close'])
                    logger.info(f"Initial Buy: Found market price {execution_price} for {item.ticker} on {effective_start_dt}")
                else:
                    logger.warning(f"Initial Buy: No market price found for {item.ticker} on {effective_start_dt}. Using fallback {execution_price}")

                success = self.portfolio.buy(effective_start_dt, item.ticker, item.shares, execution_price)
                if not success:
                    logger.error(f"Failed to execute initial buy for {item.ticker} (Qty: {item.shares}). Cash: {self.portfolio.cash}")

        logger.info(f"Starting simulation from {config.start_date} to {config.end_date} with {config.initial_capital}")
        
        # Benchmarks Setup
        ibov_series = self.data_provider.get_benchmark_data('IBOV')
        ibov_start = 0
        if not ibov_series.empty:
            idx = ibov_series.index.asof(start_dt)
            if not pd.isna(idx):
                ibov_start = ibov_series.loc[idx]
                
        selic_curve_val = config.initial_capital

        for date in timeline:
            self.process_day(date)
            
            # Update Benchmarks for History
            ibov_val = 0
            if ibov_start > 0 and not ibov_series.empty:
                 idx = ibov_series.index.asof(date)
                 if not pd.isna(idx):
                     curr = ibov_series.loc[idx]
                     # Adjust for total_invested to be comparable? 
                     # Standard practice: Normalize to initial capital.
                     # But total_invested grows with contributions. 
                     # Comparison should probably be TWR or just indexed to start.
                     # Let's index to start for simplicity in this chart.
                     ibov_val = (curr / ibov_start) * config.initial_capital

            # SELIC Accumulation
            daily_selic = self.data_provider.get_selic_daily(date)
            selic_curve_val *= (1 + daily_selic)

            # Enrich the history entry created in process_day
            if self.portfolio.history:
                self.portfolio.history[-1]['ibov_value'] = ibov_val
                self.portfolio.history[-1]['selic_value'] = selic_curve_val
            
            # Check Entries / Rebalance / Contribution
            # ... (rest of loop logic)
            
        # Finalize
        # Get last known prices for valuation
        final_val = self.portfolio.cash
        final_holdings_list = []
        
        for ticker, holding in self.portfolio.holdings.items():
             # Try get price on last day, else fallback
             price_row = self.data_provider.get_latest_price_row(ticker, timeline[-1])
             price = price_row['close'] if price_row is not None else holding.get('current_price', holding['avg_price'])
             
             holding_val = holding['quantity'] * price
             final_val += holding_val
             
             final_holdings_list.append({
                 "ticker": ticker,
                 "quantity": holding['quantity'],
                 "price": price,
                 "value": holding_val,
                 "avg_price": holding['avg_price'],
                 "return_pct": ((price - holding['avg_price']) / holding['avg_price']) * 100 if holding['avg_price'] > 0 else 0
             })
             
        total_return = (final_val - self.total_invested) / self.total_invested if self.total_invested > 0 else 0
        years = (end_dt - start_dt).days / 365.25
        # CAGR based on Total Return (Simple annualized) or IRR?
        # Creating a simple CAGR of the portfolio value vs invested is tricky with flows.
        # Approximation: Final / Invested ^ (1/years) - 1 ?? No, because invested changed over time.
        # User complained about CAGR being function of contributions.
        # Let's use simple ROI for now as Total Return.
        # And CAGR: (Final / Initial)^(1/Y) - 1 is standard but wrong with flows.
        # Let's provide the raw ROI annualized.
        cagr = ((1 + total_return) ** (1/years)) - 1 if years > 0 and total_return > -1 else 0
        
        return BacktestResult(
            final_capital=final_val,
            total_return=total_return,
            cagr=cagr,
            max_drawdown=0.0, # TODO
            sortino_ratio=0.0,
            win_rate=0.0,
            total_trades=len(self.portfolio.transactions),
            trade_log=[t for t in self.portfolio.transactions],
            final_holdings=final_holdings_list,
            total_invested=self.total_invested,
            history=self.portfolio.history
        )

    def process_day(self, date: datetime):
        # 0. Idle Cash Yield (SELIC)
        selic_daily = self.data_provider.get_selic_daily(date)
        if self.portfolio.cash > 0:
            yield_val = self.portfolio.cash * selic_daily
            self.portfolio.cash += yield_val

        # 1. Update Portfolio Valuation & Delisting Check
        current_prices = {}
        # Iterate copy of keys to allow deletion
        for ticker in list(self.portfolio.holdings.keys()):
            price_row = self.data_provider.get_latest_price_row(ticker, date)
            
            # Check Delisting / Staleness (Price > 15 days old)
            is_stale = False
            current_price = 0.0
            
            if price_row is None:
                is_stale = True
            else:
                price_date = pd.to_datetime(price_row.name)
                days_diff = (date - price_date).days
                if days_diff > 15: # Tolerance for holidays + weekends
                    is_stale = True
                else:
                    current_price = float(price_row['close'])

            if is_stale:
                holding = self.portfolio.holdings[ticker]
                exit_price = holding.get('current_price', holding['avg_price'])
                
                logger.warning(f"Delisting/OPA: {ticker} stale. Selling at {exit_price} on {date}")
                self.portfolio.sell(date, ticker, holding['quantity'], exit_price)
                
                if ticker not in self.config.blacklisted_assets:
                    self.config.blacklisted_assets.append(ticker)
                continue 

            # Normal Update
            self.portfolio.holdings[ticker]['current_price'] = current_price
            current_prices[ticker] = current_price
            
        if hasattr(self.portfolio, 'snapshot'):
             self.portfolio.snapshot(date, current_prices)
        
        # 2. Check Exits (Daily)
        self.check_exits(date, current_prices)
        
        # 3. Check Entries / Rebalance / Contribution
        if self.config.rebalance_period != 'none':
            if self.days_since_rebalance >= self.get_rebalance_days():
                 # Process Contribution
                 if self.config.contribution_amount > 0:
                     self.portfolio.cash += self.config.contribution_amount
                     self.total_invested += self.config.contribution_amount
                     
                 # Check Entries if we have slots or cash
                 if len(self.portfolio.holdings) < self.config.max_assets or self.portfolio.cash > self.config.initial_capital * 0.1:
                      self.check_entries(date)
                 
                 self.days_since_rebalance = 0
            else:
                self.days_since_rebalance += 1

    def get_rebalance_days(self):
        if self.config.rebalance_period == 'quarterly': return 63
        elif self.config.rebalance_period == 'yearly': return 252
        return 21 # Monthly default

    def get_current_prices_for_holdings(self, date: datetime) -> Dict[str, float]:
        prices = {}
        for ticker in self.portfolio.holdings:
            price_row = self.data_provider.get_latest_price_row(ticker, date)
            if price_row is not None:
                prices[ticker] = price_row['close']
        return prices

    def evaluate_rules(self, criteria_groups: List[CriteriaGroup], ticker: str, date: datetime, price: float, financials: pd.Series) -> bool:
        """
        Evaluates the dynamic criteria logic against a ticker's data.
        Returns True if the asset passes the criteria.
        """
        if not criteria_groups: return True # No rules = Pass? Or Fail? Default Pass usually.

        # Data Preparation
        # Map indicator names to data columns
        # 'p_l' -> 'p_l', 'roe' -> 'roe', 'dy' -> 'dy', 'net_debt_ebitda' -> 'net_debt_ebitda'?
        # Need to handle calculations if column doesn't exist directly.
        
        # Helper to get value
        def get_val(indicator):
            # 1. Direct Lookup
            val = financials.get(indicator)
            if val is not None: return float(val)
            
            # 2. Derived Metrics
            if indicator == 'net_debt_ebitda':
                net_debt = financials.get('net_debt')
                ebit = financials.get('ebit')
                if net_debt is not None and ebit is not None and ebit != 0:
                     return float(net_debt / ebit)
            
            if indicator == 'p_vp':
                 # P/VP = P/L * ROE
                 p_l = financials.get('p_l')
                 roe = financials.get('roe')
                 if p_l is not None and roe is not None:
                     return float(p_l * roe)

            if indicator == 'net_margin_avg_5y':
                return float(financials.get('avg_margin_5y', 0))

            if indicator == 'consecutive_profits':
                # Return number of years of consecutive profits
                full_df = self.data_provider.get_financials_data(ticker)
                if full_df.empty: return 0.0
                
                # Sort descending by date (latest first)
                history = full_df.loc[:date].sort_index(ascending=False)
                
                count = 0
                for idx, row in history.iterrows():
                    # Check yearly or quarterly? history is likely quarterly or yearly depending on source.
                    # Assuming data points are effective updates.
                    # Simple check: consecutive reports > 0.
                    # Ideally we want YEARS. If quarterly, 4 quarters > 0?
                    # Let's count consecutive reports with net_income > 0 for now as proxy, or check years.
                    # User asked for "Years". 
                    # If data is quarterly, 4 quarters = 1 year approx.
                    # Let's count valid positive reports and divide by frequency? 
                    # Simpler: Count consecutive positive result rows.
                    if row.get('net_income', -1) > 0:
                        count += 1
                    else:
                        break
                
                # If data is quarterly (approx 4 per year), divide by 4?
                # Inspect data.json: dates are "2013-06-30", "2013-09-30". It is quarterly.
                # So 20 quarters = 5 years.
                # User puts "5" (years). Rule: >= 5.
                # Metric calculation: return count / 4.
                return float(count / 4)

            if indicator == 'revenue_cagr_5y':
                history = self.data_provider.get_financials_data(ticker)
                if history.empty: return None
                history = history.loc[:date].sort_index()
                
                if len(history) < 4: return None # Need at least 1 year? 5 years preferred.
                start_rev = history.iloc[0]['revenue']
                end_rev = history.iloc[-1]['revenue']
                    
                if start_rev <= 0 or end_rev <= 0: return 0.0
                    
                years = (history.index[-1] - history.index[0]).days / 365.25
                if years < 1: return 0.0
                    
                cagr = (end_rev / start_rev) ** (1/years) - 1
                return float(cagr * 100) # Return as percentage

            return None

        # Iterate Groups
        # Logic: If config.entry_logic is "AND", all groups must pass. If "OR", one must pass.
        # But wait, the structure allows connectionToNext.
        # Let's assume global AND for simplicity for now, or use the structure.
        
        # We will assume Global AND between groups for MVP unless entry_logic specifies otherwise.
        # In frontend we have "global logic" (entry_logic).
        
        group_results = []
        for group in criteria_groups:
            # Evaluate items in group
            group_pass = True
            if isinstance(group, dict):
                group_logic = str(group.get('logic', 'AND')).upper()
                items = group.get('items', [])
            else:
                group_logic = getattr(group, 'logic', 'AND')
                if isinstance(group_logic, str):
                    group_logic = group_logic.upper()
                items = getattr(group, 'items', [])
            if items is None:
                items = []
            elif not isinstance(items, (list, tuple)):
                items = list(items)
            if group_logic == 'OR':
                group_pass = False # Default fail, need one true
            
            for item in items:
                indicator = item.indicator if hasattr(item, 'indicator') else item.get('indicator')
                operator = item.operator if hasattr(item, 'operator') else item.get('operator')
                value = item.value if hasattr(item, 'value') else item.get('value')
                value_min = getattr(item, 'value_min', None) if hasattr(item, 'value_min') else item.get('value_min')
                value_max = getattr(item, 'value_max', None) if hasattr(item, 'value_max') else item.get('value_max')

                metric_val = get_val(indicator)
                if metric_val is None:
                    # Missing data triggers fail?
                    item_pass = False
                else:
                    item_pass = False
                    if operator == '>': item_pass = metric_val > value
                    elif operator == '>=': item_pass = metric_val >= value
                    elif operator == '<': item_pass = metric_val < value
                    elif operator == '<=': item_pass = metric_val <= value
                    elif operator == '==': item_pass = metric_val == value
                    elif operator == 'range':
                        item_pass = (metric_val >= value_min) and (metric_val <= value_max)
                    elif operator == 'outsiderange':
                        item_pass = (metric_val < value_min) or (metric_val > value_max)
                
                if group_logic == 'AND':
                    if not item_pass:
                        group_pass = False
                        break 
                elif group_logic == 'OR':
                    if item_pass:
                        group_pass = True
                        break
            
            group_results.append(group_pass)

        # Combine Group Results (Default AND)
        if self.config.entry_logic == 'OR':
            return any(group_results)
        else:
            return all(group_results)

    def check_exits(self, date: datetime, prices: Dict[str, float]):
        holdings = list(self.portfolio.holdings.keys())
        for ticker in holdings:
            price = prices.get(ticker)
            if not price: continue

            # Get Financials (Lagged)
            fin_row = self.data_provider.get_latest_financials_row(ticker, date)
            if fin_row is None: continue

            # 1. Stop Loss / Take Profit (Allocated)
            # Need entry price for this holding.
            # Simplified: checking relative to avg_price
            avg_price = self.portfolio.holdings[ticker]['avg_price']
            pct_change = (price - avg_price) / avg_price
            
            if self.config.stop_loss and pct_change < -(self.config.stop_loss / 100):
                self.portfolio.sell(date, ticker, self.portfolio.holdings[ticker]['quantity'], price)
                continue
            
            if self.config.take_profit and pct_change > (self.config.take_profit / 100):
                 self.portfolio.sell(date, ticker, self.portfolio.holdings[ticker]['quantity'], price)
                 continue

            # 2. Dynamic Exit Criteria
            should_exit = False
            # If we have exit criteria, evaluate them.
            # Frontend sends explicit rules now (even for auto-transpose).
            if self.config.exit_criteria:
                if self.evaluate_rules(self.config.exit_criteria, ticker, date, price, fin_row):
                    should_exit = True
            
            if should_exit:
                 self.portfolio.sell(date, ticker, self.portfolio.holdings[ticker]['quantity'], price)

    def check_entries(self, date: datetime):
        candidates = []
        
        # Scan Universe
        for ticker in self.data_provider.assets_list:
            if ticker in self.portfolio.holdings: continue
            if ticker in self.config.blacklisted_assets: continue
            
            # Price Check
            price_row = self.data_provider.get_latest_price_row(ticker, date)
            if price_row is None: continue
            if (date - price_row.name).days > 5: continue # Stale price
            price = float(price_row['close'])
            
            # Financials Check
            fin_row = self.data_provider.get_latest_financials_row(ticker, date)
            if fin_row is None: continue
            if (date - fin_row.name).days > 500: continue # Stale financials
            
            # Data Quality Check: Collect indicators used nas regras
            required_indicators = set()
            for group in self.config.entry_criteria:
                if isinstance(group, dict):
                    items = group.get('items', [])
                else:
                    items = getattr(group, 'items', []) or []

                for item in items:
                    indicator = (
                        item['indicator']
                        if isinstance(item, dict)
                        else getattr(item, 'indicator', None)
                    )
                    if indicator:
                        required_indicators.add(indicator)

            # Validate required data exists (valores negativos são aceitos; zeros ainda sinalizam alerta)
            data_valid = True
            for indicator in required_indicators:
                val = fin_row.get(indicator)

                if val is None:
                    data_valid = False
                    break

                zero_sensitive = indicator in ['p_l', 'p_vp', 'roe', 'roic', 'ev_ebitda']
                if zero_sensitive and val == 0:
                    # Valores zerados continuam indicando ausência de dado confiável
                    data_valid = False
                    break
            
            if not data_valid:
                continue
            
            # Evaluate Entry Rules
            if not self.evaluate_rules(self.config.entry_criteria, ticker, date, price, fin_row):
                continue
            
            # Passed! Calculate Score for Ranking
            # Score based on configured weights
            score = 0
            score_weights = getattr(self.config, "entry_score_weights", "balanced")
            
            if score_weights == 'value':
                # Value: Lower P/L, P/VP better
                p_l = fin_row.get('p_l', 20)
                p_vp = fin_row.get('p_vp', 3)
                score = p_l * 0.6 + p_vp * 0.4
                
            elif score_weights == 'growth':
                # Growth: Higher CAGR better (negate for ascending sort)
                cagr = fin_row.get('revenue_cagr_5y', 0)
                score = -cagr  # Negative so higher CAGR = lower score
                
            elif score_weights == 'quality':
                # Quality: Higher ROE, Lower Debt better
                roe = fin_row.get('roe', 0.05)
                debt_ratio = fin_row.get('net_debt_ebitda', 3)
                score = -roe * 100 + debt_ratio * 10  # Negate ROE for ascending sort
                
            else:  # 'balanced'
                # Balanced: Mix of value + quality
                p_l = fin_row.get('p_l', 20)
                roe = fin_row.get('roe', 0.05)
                dy = fin_row.get('dy', 0)
                score = p_l * 0.4 - roe * 50 - dy * 100
            
            candidates.append({
                'ticker': ticker,
                'price': price,
                'score': score
            })
        
        if not candidates:
            return  # No candidates to buy
        
        # Sort Candidates by Score (Ascending = Better)
        candidates.sort(key=lambda x: x['score'])
        
        # Buy Top N
        slots = self.config.max_assets - len(self.portfolio.holdings)
        if slots <= 0:
            return
        
        for cand in candidates[:slots]:
            # Allocation logic
            available = self.portfolio.cash
            alloc_per_slot = available / slots
            qty = int(alloc_per_slot // cand['price'])
            qty = (qty // 100) * 100  # Round Lot
            
            if qty > 0:
                self.portfolio.buy(date, cand['ticker'], qty, cand['price'])
