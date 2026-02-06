
import fundamentus
import pandas as pd

try:
    print("--- Bulk Data Columns ---")
    df = fundamentus.get_resultado()
    print(df.columns.tolist())
    print(df.head(1).to_dict())
    
    print("\n--- Details for PETR4 ---")
    # check if get_papel or get_detalhes_papel exists and what it returns
    # fundamentus library usually has get_papel which returns a list of dataframes from the html tables
    try:
        details = fundamentus.get_papel('PETR4')
        if isinstance(details, list):
            print(f"Returned {len(details)} tables.")
            for i, tbl in enumerate(details):
                print(f"Table {i}:")
                print(tbl.head())
        elif isinstance(details, pd.DataFrame):
             print(details.head())
        else:
             print(type(details))
    except Exception as e:
        print(f"get_papel error: {e}")

except Exception as e:
    print(e)
