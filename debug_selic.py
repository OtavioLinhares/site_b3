
import requests
import pandas as pd
import yfinance as yf

# Debug Selic
try:
    print("Fetching Selic...")
    url = "http://api.bcb.gov.br/dados/serie/bcdata.sgs.1178/dados?formato=json"
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Data Type: {type(data)}")
    if isinstance(data, list):
        print(f"First item: {data[0]}")
    else:
        print(f"Data: {data}")
        
    df = pd.DataFrame(data)
    print("DataFrame created successfully")
    print(df.head())
except Exception as e:
    print(f"Selic Error: {e}")

# Debug Ibovespa
try:
    print("\nFetching Ibovespa...")
    ticker = yf.Ticker("^BVSP")
    hist = ticker.history(period="1mo")
    print(hist)
except Exception as e:
    print(f"Ibovespa Error: {e}")
