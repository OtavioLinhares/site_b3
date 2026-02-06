
import yfinance as yf
import pandas as pd

def check_history_retry():
    tickers = ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA']
    print(f"Checking {tickers}...")
    
    for t in tickers:
        print(f"\n--- {t} ---")
        try:
            ticker = yf.Ticker(t)
            # Try getting history
            hist = ticker.history(period="5y")
            print(f"Price History Rows: {len(hist)}")
            if not hist.empty:
                print(hist.head(2))
            
            # Try financials (LPA/EPS)
            fin = ticker.financials
            if not fin.empty:
                print("Financials found!")
                print(fin.index)
            else:
                print("Financials empty.")
                
        except Exception as e:
            print(f"Error {t}: {e}")

if __name__ == "__main__":
    check_history_retry()
