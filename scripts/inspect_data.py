import fundamentus
import pandas as pd

# Get basic results
df = fundamentus.get_resultado()
print("Columns available in get_resultado:")
print(df.columns.tolist())

# Check a sample for ROIC and Margin
sample = df.head(1)
print("\nSample data (first row):")
print(sample.T)

# Check if we can get historical data for a specific ticker (e.g. PETR4) to calculate 5y margin
# Note: get_papel might return history if arguments are used, or we might need another function
try:
    print("\nAttempting to fetch details/history for PETR4...")
    # Does get_papel return specific details or history? 
    # Usually get_papel(ticker) returns more info or history depending on lib version.
    # Let's try to see what it returns.
    details = fundamentus.get_papel('PETR4')
    print("get_papel('PETR4') type:", type(details))
    if isinstance(details, pd.DataFrame):
         print(details.columns.tolist())
         print(details.head())
    else:
         print(details)
except Exception as e:
    print(f"Error fetching details: {e}")
