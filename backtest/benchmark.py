
import pandas as pd
import logging
from backtest.data_provider import DataProvider

logger = logging.getLogger("BenchmarkService")

class BenchmarkService:
    def __init__(self, data_provider: DataProvider):
        self.data_provider = data_provider
        self.benchmarks = {} # Cache
        
    def load_benchmarks(self):
        """Ensures benchmarks are loaded in DataProvider."""
        self.data_provider.fetch_benchmarks()
        
    def get_benchmark_cumulative(self, name: str, start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.Series:
        """Returns cumulative return series (normalized to 0 at start)."""
        series = self.data_provider.get_benchmark_data(name)
        if series.empty:
            return pd.Series()
            
        # Slice
        subset = series.loc[start_date:end_date]
        if subset.empty: return pd.Series()
        
        # Calculate Cumulative Return
        if name == 'SELIC_Rate':
            # Daily accumulation
            # Series is % a.a. -> convert to daily factor
            daily_factors = (1 + subset) ** (1/252)
            cumulative = daily_factors.cumprod() - 1
            return cumulative
            
        elif name == 'IPCA':
            # Monthly. Need to resample to daily? or just return monthly points?
            # For plotting, daily forward fill?
            # IPCA is monthly %. (1 + r).cumprod()
            # Series index is Month Start usually.
            cumulative = (1 + subset/100).cumprod() - 1
            # Reindex to daily
            full_idx = pd.date_range(start=start_date, end=end_date, freq='D')
            cumulative = cumulative.reindex(full_idx, method='ffill')
            return cumulative
            
        else: # IBOV (Index Points)
            # Normalize to 0 at start
            start_val = subset.iloc[0]
            if start_val == 0: return subset * 0
            cumulative = (subset / start_val) - 1
            return cumulative
