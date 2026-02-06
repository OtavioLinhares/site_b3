
import fundamentus
import pandas as pd
from datetime import date

class FundamentusClient:
    def __init__(self):
        pass

    def fetch_all_current(self):
        """
        Fetches the current snapshot of all companies from Fundamentus.
        Returns a DataFrame cleaned and ready for processing.
        """
        try:
            # get_resultado returns a raw dataframe
            df = fundamentus.get_resultado()
            
            # Reset index to get 'papel' (ticker) as a column
            df = df.reset_index()
            df.rename(columns={'papel': 'ticker'}, inplace=True)
            
            # Clean numeric columns (sometimes they come as strings, but fundamentus library usually handles it)
            # Ensure proper types
            # Columns usually are:
            # cotacao, pl, pvp, psr, dy, pa, pcg, pebit, pacl, evebit, evebitda, mrgebit, mrgliq, roic, roe, liqcorr, liq2m, patrliq, divbpatr, c5y
            
            return df
        except Exception as e:
            print(f"Error fetching from Fundamentus: {e}")
            return pd.DataFrame()

    def get_details(self, ticker):
        """
        Fetches details for a specific ticker.
        """
        try:
            # This might return a list of dataframes or a dataframe
            return fundamentus.get_papel(ticker)
        except Exception as e:
            print(f"Error fetching details for {ticker}: {e}")
            return None

    def get_extended_info(self, ticker):
        """
        Fetches Sector, Subsector, Market Cap, and Debt metrics for a ticker.
        Returns: (Sector, Subsector, Market_Cap, Net_Debt, EV_EBITDA)
        """
        try:
            details = self.get_details(ticker)
            if isinstance(details, pd.DataFrame) and not details.empty:
                # Fundamentus keys are usually Pascal/Snake case or specific.
                # Based on check_div_ebitda.py: 'Setor', 'Subsetor', 'Div_Liquida', 'EV_EBITDA', 'Valor_de_mercado'
                
                sector = details['Setor'].iloc[0] if 'Setor' in details.columns else None
                subsector = details['Subsetor'].iloc[0] if 'Subsetor' in details.columns else None
                
                # Market Cap (Valor_de_mercado) - CORRECT SOURCE
                market_cap = 0.0
                if 'Valor_de_mercado' in details.columns:
                    val = details['Valor_de_mercado'].iloc[0]
                    if isinstance(val, str):
                        val = val.replace('.', '').replace(',', '.')
                        try:
                            market_cap = float(val)
                        except:
                            market_cap = 0.0
                    else:
                        market_cap = float(val) if val else 0.0
                
                # Div_Liquida
                net_debt = 0.0
                if 'Div_Liquida' in details.columns:
                    val = details['Div_Liquida'].iloc[0]
                    # Attempt parse if string
                    if isinstance(val, str):
                        val = val.replace('.', '').replace(',', '.')
                        try:
                            net_debt = float(val)
                        except:
                            net_debt = 0.0
                    else:
                        net_debt = float(val) if val else 0.0

                # EV_EBITDA
                ev_ebitda = 0.0
                if 'EV_EBITDA' in details.columns:
                     val = details['EV_EBITDA'].iloc[0]
                     if isinstance(val, str):
                         val = val.replace('.', '').replace(',', '.') # usually formated 2,62
                         # wait, brazillian format usually comma decimal. 2,62 -> 2.62
                         try:
                             ev_ebitda = float(val) / 100 if '%' in val else float(val) # it's usually 2.62 not percent
                         except:
                             ev_ebitda = 0.0
                     else:
                         ev_ebitda = float(val) if val else 0.0

                return sector, subsector, market_cap, net_debt, ev_ebitda

            return None, None, None, None, None
        except Exception as e:
            print(f"Error extracting extended info for {ticker}: {e}")
            return None, None, None, None, None
