
import fundamentus
import ipeadatapy as ipea
import pandas as pd

def check_fundamentus():
    print("--- Fundamentus Check ---")
    # 1. Get List of stocks
    df = fundamentus.get_resultado()
    print(f"Total Companies found: {len(df)}")
    print("Columns:", df.columns.tolist())
    print("Sample:\n", df.head(2))

    # 2. Check details for a specific stock (e.g. PETR4)
    ticker = 'PETR4'
    # There isn't a direct "get_detalhes" that returns history easily in standard usage, 
    # but let's see what get_papel returns if it exists or get_resultado_raw
    
    # Try getting historical prices if available? 
    # Fundamentus lib usually focuses on current indicators.
    # Let's check if there is function for history.
    try:
        # Some versions might have specific functions. 
        # But commonly we might need to rely on the main table for snapshots.
        pass
    except Exception as e:
        print(f"Error checking details: {e}")

def check_ipeadata():
    print("\n--- Ipeadata Check ---")
    # List a few series
    # IPCA
    try:
        # Search for IPCA
        # series = ipea.list_series('IPCA')
        # print(series[['CODE', 'NAME']].head())
        
        # Let's try to fetch IPCA (PRECOS12_IPCA12)
        ipca = ipea.timeseries('PRECOS12_IPCA12')
        print("IPCA Data:\n", ipca.tail(5))
    except Exception as e:
        print(f"Error Ipea: {e}")

if __name__ == "__main__":
    check_fundamentus()
    check_ipeadata()
