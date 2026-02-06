
import fundamentus
import pandas as pd

def check_history(ticker='PETR4'):
    print(f"Checking history for {ticker}...")
    try:
        # get_papel returns a list of dataframes usually? Or a dict?
        # Let's inspect the return type/content
        details = fundamentus.get_papel(ticker)
        if isinstance(details, pd.DataFrame):
            print("Columns List:", details.columns.tolist())
            # Print specific potential matches
            for c in details.columns:
                if 'Lucro' in c or 'Cresc' in c:
                    print(f"{c}: {details[c].iloc[0]}")
        
        elif isinstance(details, list):
            for i, d in enumerate(details):
                if isinstance(d, pd.DataFrame):
                    cols = d.columns.tolist()
                    if 'Setor' in cols:
                        print(f"Setor FOUND: {d['Setor'].iloc[0]}")
                    else:
                        print("Setor NOT FOUND in columns.")
                        print(cols)
        elif isinstance(details, dict):
             print("Keys:", details.keys())
        else:
             print(details)
             
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_history()
