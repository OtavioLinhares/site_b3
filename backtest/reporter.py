
import pandas as pd
import plotly.graph_objects as go
import logging
from typing import List
from backtest.domain import BacktestResult

logger = logging.getLogger("BacktestReporter")

class BacktestReporter:
    def __init__(self, result: BacktestResult, benchmarks: dict):
        self.result = result
        self.benchmarks = benchmarks # Dict of Series
        self.history_df = pd.DataFrame(result.dict_history) if hasattr(result, 'dict_history') else pd.DataFrame()
        
    def generate_html_report(self, output_path="web/public/backtest_report.html"):
        """Generates interactive Plotly chart."""
        
        # 1. Prepare Data
        # Portfolio Cumulative
        # We need daily history from Portfolio. 
        # engine.py didn't pass full history object to Result, only trade log.
        # I need to update engine.py/domain.py to pass daily values.
        # Assuming result has 'daily_values' (check domain.py)
        # domain.py has 'daily_returns'. 
        # We need Total Value History for plotting.
        
        # NOTE: I need to update domain.py and engine.py to include 'history' in result.
        # But for now let's assume I will fix engine.
        pass

    def plot_performance(self, history: List[dict], trades: List[dict]):
        df = pd.DataFrame(history)
        if df.empty: return None
        
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Normalize Portfolio
        start_val = df['total_value'].iloc[0]
        df['cumulative'] = (df['total_value'] / start_val) - 1
        
        fig = go.Figure()
        
        # Portfolio
        fig.add_trace(go.Scatter(
            x=df.index, y=df['cumulative'],
            mode='lines', name='Portfolio',
            line=dict(color='green', width=2)
        ))
        
        # Benchmarks
        colors = {'IBOV': '#6c8dd9', 'SELIC_Rate': '#ff8a80', 'IPCA': 'orange'}
        for name, series in self.benchmarks.items():
            if series.empty: continue
            # Align dates
            subset = series.loc[df.index.min():df.index.max()]
            if subset.empty: continue
            
            # Reindex to match portfolio dates (ffill)
            subset = subset.reindex(df.index, method='ffill')
            
            # Calculated cumulative from subset start
            if name == 'SELIC_Rate':
                 # Daily factor: (1+r)^(1/252)
                 # already divided by 100 in data_provider
                 factors = (1 + subset) ** (1/252)
                 cum = factors.cumprod() - 1
            elif name == 'IPCA':
                 # Monthly %
                 cum = (1 + subset).cumprod() - 1
            else:
                 # Index points
                 start = subset.iloc[0]
                 if start == 0: continue
                 cum = (subset / start) - 1
                 
            fig.add_trace(go.Scatter(
                x=subset.index, y=cum,
                mode='lines', name=name,
                line=dict(color=colors.get(name, 'gray'), dash='dot' if name != 'IBOV' else 'solid')
            ))
            
        # Buy/Sell Markers
        # Group by Date
        buy_dates = [pd.to_datetime(t['date']) for t in trades if t['action'] == 'BUY']
        sell_dates = [pd.to_datetime(t['date']) for t in trades if t['action'] == 'SELL']
        
        # Y values? Portfolio value at that date.
        # Map date to cumulative value
        
        # Optimization: Create a lookup series
        cum_series = df['cumulative']
        
        buy_y = [cum_series.asof(d) for d in buy_dates]
        sell_y = [cum_series.asof(d) for d in sell_dates]
        
        fig.add_trace(go.Scatter(
            x=buy_dates, y=buy_y,
            mode='markers', name='Buy',
            marker=dict(symbol='triangle-up', size=10, color='lime')
        ))
        
        fig.add_trace(go.Scatter(
            x=sell_dates, y=sell_y,
            mode='markers', name='Sell',
            marker=dict(symbol='triangle-down', size=10, color='red')
        ))
        
        fig.update_layout(
            title='Backtest Performance',
            xaxis_title='Date',
            yaxis_title='Cumulative Return',
            template='plotly_dark',
            hovermode='x unified'
        )
        
        return fig
