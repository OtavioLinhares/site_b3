
import sys
import os
sys.path.append(os.getcwd())

from analysis.metrics import MetricsEngine
import pandas as pd

engine = MetricsEngine()
print("--- Generating Treemap Data ---")
df = engine.get_treemap_data()

if df.empty:
    print("DataFrame is Empty! ETL might not be finished or DB is empty.")
else:
    print(f"Generated {len(df)} nodes.")
    print("Columns:", df.columns.tolist())
    print("\n--- Sample Rows (Head) ---")
    print(df.head())
    
    print("\n--- Sample Rows (Tail - Likely Outros/Companies) ---")
    print(df.tail())
    
    # Check for Debt/EBITDA in customdata
    print("\n--- Checking Tooltips ---")
    sample_company = df[df['ids'].str.startswith('C_')].iloc[0]
    print(f"Sample Company: {sample_company['labels']}")
    print(f"Tooltip: {sample_company['custom_data']}")
