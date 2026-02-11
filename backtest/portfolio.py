
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict

@dataclass
class Transaction:
    date: datetime
    ticker: str
    action: str  # 'BUY' or 'SELL'
    quantity: int
    price: float
    fees: float = 0.0
    total_value: float = 0.0

class Portfolio:
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.holdings: Dict[str, dict] = {} # {ticker: {'quantity': 100, 'avg_price': 10.0}}
        self.transactions: List[Transaction] = []
        self.history: List[dict] = [] # Daily NAV snapshot

    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        """Calculates total portfolio value (Cash + Holdings * Price)."""
        holdings_value = 0.0
        for ticker, data in self.holdings.items():
            price = current_prices.get(ticker, data['avg_price']) # Fallback if price missing?
            holdings_value += data['quantity'] * price
        return self.cash + holdings_value

    def buy(self, date: datetime, ticker: str, quantity: int, price: float, fees: float = 0.0):
        if quantity <= 0: return
        total_cost = (quantity * price) + fees
        if total_cost > self.cash:
            # raise ValueError(f"Insufficient funds: {self.cash} < {total_cost}")
            # Adjust quantity? Or Return False
            return False

        self.cash -= total_cost
        
        # Update Holdings
        if ticker not in self.holdings:
            self.holdings[ticker] = {'quantity': 0, 'avg_price': 0.0}
        
        current_q = self.holdings[ticker]['quantity']
        current_avg = self.holdings[ticker]['avg_price']
        
        new_q = current_q + quantity
        new_avg = ((current_q * current_avg) + (quantity * price)) / new_q
        
        self.holdings[ticker]['quantity'] = new_q
        self.holdings[ticker]['avg_price'] = new_avg
        
        # Log
        txn = Transaction(date, ticker, 'BUY', quantity, price, fees, total_cost)
        self.transactions.append(txn)
        return True

    def sell(self, date: datetime, ticker: str, quantity: int, price: float, fees: float = 0.0):
        if ticker not in self.holdings: return False
        current_q = self.holdings[ticker]['quantity']
        
        if quantity > current_q: quantity = current_q # Sell all available
        
        if quantity <= 0: return False
        
        total_proceeds = (quantity * price) - fees
        self.cash += total_proceeds
        
        # Update Holdings
        self.holdings[ticker]['quantity'] -= quantity
        if self.holdings[ticker]['quantity'] == 0:
            del self.holdings[ticker]
            
        # Log
        txn = Transaction(date, ticker, 'SELL', quantity, price, fees, total_proceeds)
        self.transactions.append(txn)
        return True

    def snapshot(self, date: datetime, current_prices: Dict[str, float]):
        """Records daily state."""
        total_val = self.get_total_value(current_prices)
        self.history.append({
            'date': date,
            'total_value': total_val,
            'cash': self.cash,
            'holdings_count': len(self.holdings)
        })
