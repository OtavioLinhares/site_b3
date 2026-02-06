
import sys
import os
sys.path.append(os.getcwd())

from analysis.metrics import MetricsEngine
import pandas as pd

def verify():
    engine = MetricsEngine()
    
    print("--- Verifying Segment View ---")
    df_segments = engine.get_sectors_view()
    if df_segments.empty:
        print("FAIL: Segment view is empty.")
        return
    
    print(f"Number of segments: {len(df_segments)}")
    if len(df_segments) > 10:
        print(f"SUCCESS: Found {len(df_segments)} segments (more than the old limit of 10).")
    else:
        print(f"WARNING: Only found {len(df_segments)} segments. Check if DB has enough data.")
        
    if "__OUTROS__" in df_segments['sector_names'].values or "Outros Setores" in df_segments['labels'].values:
        print("FAIL: Found 'Outros' in segment view.")
    else:
        print("SUCCESS: No 'Outros' found in segment view.")
        
    print("\n--- Verifying Companies View (Sample Segment) ---")
    if not df_segments.empty:
        sample_segment = df_segments.iloc[0]['sector_names']
        print(f"Checking segment: {sample_segment}")
        df_companies = engine.get_companies_view(sample_segment)
        
        print(f"Number of companies in {sample_segment}: {len(df_companies)}")
        if "__OUTRAS__" in df_companies['company_tickers'].values or "Outras Empresas" in df_companies['labels'].values:
            print("FAIL: Found 'Outras' in companies view.")
        else:
            print("SUCCESS: No 'Outras' found in companies view.")

if __name__ == "__main__":
    verify()
