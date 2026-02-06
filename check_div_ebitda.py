
import fundamentus
import pandas as pd

try:
    print("Fetching details for PETR4...")
    # get_papel returns a list of dataframes usually? Or a single one if library updated?
    # Inspect tool showed it returns a DataFrame with many columns.
    df = fundamentus.get_papel('PETR4')
    print("Columns:", df.columns.tolist())
    
    # Look for likely candidates
    candidates = [c for c in df.columns if 'Div' in c or 'EBITDA' in c]
    print("Candidates:", candidates)
    
    if not df.empty:
        print("Values:", df[candidates].iloc[0].to_dict())

except Exception as e:
    print(e)
