
import logging
from backtest.data_provider import DataProvider
from backtest.engine import BacktestEngine
from backtest.domain import StrategyConfig
from backtest.benchmark import BenchmarkService
from backtest.reporter import BacktestReporter

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    print("--- Starting Backtest Simulation ---")
    
    # 1. Initialize Data
    data_provider = DataProvider()
    data_provider.load_data()
    
    # Auto-fetch benchmarks (stored in data_provider)
    data_provider.fetch_benchmarks()
    
    # Simulation Period: 2023 to 2024 (Faster Test)
    start_date = "2023-01-01"
    end_date = "2024-12-31"
    
    # 3. Run Engine (Multiple Scenarios)
    print(f"Running simulation for {start_date} to {end_date}...")
    
    scenarios = {
        '1': 'Unlimited (Daily)',
        '21': 'Monthly',
        '63': 'Quarterly',
        '126': 'Semesterly',
        '252': 'Yearly'
    }
    
    results_export = {}
    
    for days, label in scenarios.items():
        print(f"\nRunning Scenario: {label} (Days: {days})...")
        cfg = StrategyConfig(
            initial_capital=100000.0,
            min_assets=5,
            max_assets=10,
            rebalance_days=int(days),
            min_liquidity=0.0,
            max_p_l=25.0,
            min_net_margin=0.05,
            min_roe=0.10,
            max_net_debt_ebitda=4.0, # STRICTER than Exit (5.0)
            exit_p_l_above=40.0,
            exit_net_debt_ebitda_above=5.0
        )
        
        eng = BacktestEngine(data_provider)
        res = eng.run(start_date, end_date, cfg)
        
        print(f"-> Total Return: {res.total_return:.2%} | Trades: {len(res.trade_log)}")
        
        # Split history into Equity Curve and Decision Log
        equity_curve = [x for x in res.history if x.get('type') != 'decision']
        decision_log = [x['data'] for x in res.history if x.get('type') == 'decision']
        
        results_export[days] = {
            'label': label,
            'summary': {
                'final_capital': res.final_capital,
                'total_return': res.total_return,
                'cagr': res.cagr,
                'total_trades': len(res.trade_log)
            },
            'history': equity_curve,
            'trade_log': res.trade_log,
            'decision_log': decision_log if days == '21' else [] # Only export detailed logs for Monthly
        }

    # 5. Export JSON for Frontend
    print("\nExporting Data...")
    
    # Helper to convert Series/Dataframe to clean JSON-able list
    def clean_benchmark_data(series_data):
        if hasattr(series_data, 'reset_index'):
             # If it's a Series or DataFrame
             df = series_data.reset_index()
             # Rename columns if needed, assuming index is Date
             df.columns = ['date', 'value']
             # Convert timestamps to string
             df['date'] = df['date'].dt.strftime('%Y-%m-%d')
             return df.to_dict(orient='records')
        return series_data

    benchmarks_data = {
        'IBOV': clean_benchmark_data(data_provider.get_benchmark_data('IBOV')),
        'SELIC_Rate': clean_benchmark_data(data_provider.get_benchmark_data('SELIC_Rate')),
        'IPCA': clean_benchmark_data(data_provider.get_benchmark_data('IPCA'))
    }
    
    import json
    result_dict = {
        'scenarios': results_export,
        'benchmarks': benchmarks_data
    }
    with open("web/public/backtest_results.json", "w") as f:
        json.dump(result_dict, f, default=str)
    print("JSON results saved to web/public/backtest_results.json")
    
    # Generate legacy report for Monthly only (or skip)
    # reporter = BacktestReporter(result_monthly, benchmarks_data)
    
    # Filter trades for plot
    # Filter trades for plot
    # chart = reporter.plot_performance(result.history, result.trade_log)
    # if chart:
    #     output_file = "web/public/backtest_chart.html"
    #     chart.write_html(output_file, include_plotlyjs='cdn', config={'responsive': True})
    #     print(f"Chart saved to {output_file}")
    # else:
    #     print("Failed to generate chart (no history data).")

if __name__ == "__main__":
    main()
