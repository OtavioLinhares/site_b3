
import logging
from datetime import datetime
import pandas as pd
from backtest.engine import BacktestEngine
from backtest.data_provider import DataProvider
from backtest.domain import StrategyConfigRequest, ReviewPortfolioItem

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DebugSim")

def run_debug():
    print("--- Starting Debug Simulation ---")
    
    # 1. Mock Config
    config = StrategyConfigRequest(
        initial_capital=100000,
        start_date="2020-01-01",
        end_date="2023-12-31",
        benchmark="IBOV",
        max_assets=10,
        min_liquidity=200000,
        forced_assets=[],
        blacklisted_assets=[],
        entry_logic="AND",
        entry_criteria=[
             {"id": 1, "logic": "AND", "connectionToNext": "AND", "items": [
                 {"indicator": "revenue_cagr_5y", "operator": ">", "value": 0.10},
                 {"indicator": "avg_margin_5y", "operator": ">", "value": 0.10},
                 {"indicator": "consecutive_profits", "operator": ">=", "value": 5}
             ]}
        ],
        entry_score_weights="growth",
        exit_mode="fixed", # ?
        exit_criteria=[],
        rebalance_period="monthly",
        contribution_amount=0,
        contribution_frequency="none",
        initial_portfolio=[
            ReviewPortfolioItem(ticker="PETR4", shares=100, price=10.0, volume=0, score=0),
            ReviewPortfolioItem(ticker="VALE3", shares=100, price=20.0, volume=0, score=0)
        ]
    )
    
    # 2. Init DataProvider
    data_provider = DataProvider()
    data_provider.load_data()
    
    # 3. Run Engine
    engine = BacktestEngine(data_provider)
    result = engine.run(config)
    
    print("\n--- Results ---")
    print(f"Final Capital: {result.final_capital}")
    print(f"Total Invested: {result.total_invested}")
    print(f"Total Return: {result.total_return * 100:.2f}%")
    print(f"Total Trades: {result.total_trades}")
    print(f"Final Holdings Count: {len(result.final_holdings)}")
    
    if result.final_holdings:
        print("\nFinal Holdings Sample:")
        for h in result.final_holdings:
            print(f" - {h['ticker']}: {h['quantity']} @ {h['price']}")
    else:
        print("\nWARNING: Final Holdings is EMPTY!")
        
    print("\nTransaction Log Sample:")
    for t in result.trade_log[:5]:
        print(t)

if __name__ == "__main__":
    run_debug()
