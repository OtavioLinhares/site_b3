
import ipeadatapy as ipea
import pandas as pd
from datetime import datetime

class IpeadataClient:
    def __init__(self):
        self.common_series = {
            'IPCA': 'PRECOS12_IPCA12',
            'SELIC': 'BM12_TJOVER12', # Taxa de juros - Over / Selic - acumulada no mês - (% a.m.)
            'USDBRL': 'MACRO_DOLF', # Dólar comercial (venda) - média de período
            # Add more as needed
        }

    def list_series(self, query):
        return ipea.list_series(query)

    def fetch_series(self, code):
        """
        Fetches a time series by code.
        Returns a DataFrame with index as Date and a 'value' column.
        """
        try:
            # ipea.timeseries returns a dataframe
            df = ipea.timeseries(code)
            
            # Find the value column (starts with VALUE)
            value_col = next((col for col in df.columns if col.startswith('VALUE')), None)
            
            if not value_col:
                print(f"Could not find Value column for {code}. Columns: {df.columns}")
                return pd.DataFrame()
            
            # Standardize
            df = df.rename(columns={value_col: 'value'})
            df = df[['value']]
            
            return df
        except Exception as e:
            print(f"Error fetching Ipea series {code}: {e}")
            return pd.DataFrame()
