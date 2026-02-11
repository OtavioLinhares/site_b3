import sys
import os
import pandas as pd
import glob

# Add current directory to path to import CVMClient
sys.path.append(os.getcwd())
from etl.cvm_client import CVMClient

def inspect_dfp(year):
    client = CVMClient()
    print(f"--- PILOT: Downloading DFP {year} ---")
    files = client.fetch_annual_reports(year)
    
    if not files:
        print("No files downloaded.")
        return

    print(f"\n--- PILOT: Inspecting {len(files)} files ---")
    
    # We want to check for "Quantidade de Ações" in specific files
    # Usually in DFP, basic info might be in "dfp_cia_aberta_YYYY.csv" (cadastral)
    # or "Mutações do Patrimônio Líquido" (DMPL)
    
    for file_path in files:
        filename = os.path.basename(file_path)
        print(f"\nChecking: {filename}")
        
        try:
            # ISO-8859-1 is common for CVM files
            df = pd.read_csv(file_path, sep=';', encoding='ISO-8859-1', nrows=50) # Read small chunk
            
            print(f"Columns: {list(df.columns)}")
            
            # Check for "Ações" in columns or basic data
            if 'dfp_cia_aberta_2023.csv' in filename: # The main metadata file
                print("--- METADATA PREVIEW ---")
                print(df.head(2))
            
            # DMPL might have "Capital Social" vs "Reservas" but maybe not Quantity
            
            # Looking for typical tables
            if 'DRE' in filename and 'con' in filename: # Consolidated DRE
                print("--- DRE PREVIEW (CONSOLIDATED) ---")
                # Look for CD_CONTA specific to Net Income
                # 3.11 = Lucro Líquido
                print(df[df['CD_CONTA'].str.startswith('3.01') | df['CD_CONTA'].str.startswith('3.11')].head())

        except Exception as e:
            print(f"Error reading {filename}: {e}")

if __name__ == "__main__":
    inspect_dfp(2023)
