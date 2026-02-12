from typing import List, Optional, Union
from pydantic import BaseModel
from dataclasses import dataclass, field

# --- Domain Models ---

class CriteriaItem(BaseModel):
    indicator: str
    operator: str  # >, >=, <, <=, range, outsiderange
    value: Optional[float] = None
    value_min: Optional[float] = None
    value_max: Optional[float] = None

class CriteriaGroup(BaseModel):
    logic: str  # AND, OR
    items: List[CriteriaItem]
    connectionToNext: Optional[str] = None # AND, OR

class ReviewPortfolioItem(BaseModel):
    ticker: str
    shares: int
    price: float
    volume: float
    score: Optional[float] = None

class StrategyConfigRequest(BaseModel):
    # Step 1: Basics
    initial_capital: float
    start_date: str
    end_date: str
    benchmark: str = "IBOV"
    max_assets: int = 10
    min_liquidity: float = 0
    forced_assets: List[str] = [] 
    blacklisted_assets: List[str] = [] 

    # Step 2: Entry
    entry_logic: str # AND, OR
    entry_criteria: List[CriteriaGroup]
    entry_score_weights: str = "balanced"  # value, growth, quality, balanced

    # Step 3: Exit
    exit_mode: str 
    exit_criteria: List[CriteriaGroup] = []
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None
    exit_tolerance_margin: Optional[float] = 0

    # Step 4: Management
    rebalance_period: str # none, monthly, quarterly, yearly
    contribution_amount: float = 0
    contribution_frequency: str = "none" # none, monthly

    # Step 5: Review
    initial_portfolio: List[ReviewPortfolioItem] = []

@dataclass
class BacktestResult:
    final_capital: float
    total_return: float
    cagr: float
    max_drawdown: float
    sortino_ratio: float
    win_rate: float
    total_trades: int
    trade_log: List[dict]
    final_holdings: List[dict] = field(default_factory=list)
    total_invested: float = 0.0
    history: List[dict] = field(default_factory=list)
