from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Union, Dict, Any
import uvicorn
import pandas as pd
from datetime import datetime

from backtest.domain import StrategyConfigRequest, CriteriaGroup, CriteriaItem, ReviewPortfolioItem
from backtest.engine import BacktestEngine

# Existing backtest modules (to be refactored)
# from backtest.engine import BacktestEngine

app = FastAPI()

# CORS Configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/assets/available")
def get_available_assets():
    """
    Returns list of available tickers and their sectors for the UI.
    Mocking for now, but should come from data_provider.
    """
    # TODO: Connect to DataProvider
    return [
        {"ticker": "PETR4", "sector": "Petróleo"},
        {"ticker": "VALE3", "sector": "Mineração"},
        {"ticker": "WEGE3", "sector": "Industrial"},
        {"ticker": "ITUB4", "sector": "Financeiro"},
        {"ticker": "BBAS3", "sector": "Financeiro"},
        # ... add more real ones from data.json or DB
    ]

@app.post("/api/backtest/run")
def run_simulation(config: StrategyConfigRequest):
    print(f"Received simulation request: {config.json()}")

    try:
        # Initialize DataProvider (singleton or per request?)
        # For now, let's create one. Ensure data path is correct.
        from backtest.data_provider import DataProvider
        data_provider = DataProvider() # Assuming it loads data on init
        
        engine = BacktestEngine(data_provider)
        result = engine.run(config)
        
        # Serialize Result
        response = {
            "start_date": config.start_date,
            "end_date": config.end_date,
            "benchmarks": {
                "IBOV": [], # TODO: Fetch Benchmark Data
                "SELIC_Rate": []
            },
            "scenarios": {
                "21": {
                    "summary": {
                        "final_capital": result.final_capital,
                        "total_return": result.total_return,
                        "cagr": result.cagr,
                        "total_trades": result.total_trades,
                        "max_drawdown": result.max_drawdown
                    },
                    "history": result.history, # Check format
                    "decision_log": result.trade_log # Using trade_log for decision_log for now
                }
            },
            "trades": result.trade_log # Explicit trades list for the new tab
        }
        
        return response

    except Exception as e:
        print(f"Error running simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
