
import ipeadatapy as ipea
import pandas as pd

codes = ['BM12_TJOVER12', 'MACRO_DOLF']

for code in codes:
    print(f"--- Checking {code} ---")
    try:
        df = ipea.timeseries(code)
        print("Columns:", df.columns.tolist())
        print(df.head())
        print(df.tail())
    except Exception as e:
        print(f"Error: {e}")
