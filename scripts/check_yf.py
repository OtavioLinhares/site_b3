
import yfinance as yf
import pandas as pd

def check_yf():
    ticker = yf.Ticker("PETR4.SA")
    
    print("--- Financials ---")
    print(ticker.financials.head())
    
    print("\n--- Income Statement ---")
    # specific verification for EPS (LPA)
    try:
        inc = ticker.income_stmt
        if 'Basic EPS' in inc.index:
            print("Found Basic EPS:\n", inc.loc['Basic EPS'])
        else:
            print("Basic EPS not found in index:", inc.index)
    except Exception as e:
        print("Error getting income stmt:", e)

    print("\n--- History (Price) ---")
    hist = ticker.history(period="1y")
    print(hist.tail())

if __name__ == "__main__":
    check_yf()
