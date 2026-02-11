import pandas as pd
import os
import glob
from datetime import datetime

class CVMParser:
    """
    Parses DFP (Annual) and ITR (Quarterly) CSV files from CVM.
    """
    
    def __init__(self, data_dir="data/cvm"):
        self.data_dir = data_dir

    def parse_financials(self, year, doc_type='DFP'):
        """
        Parses all financial statements for a given year. Optimized for speed using pivoting.
        """
        pattern_prefix = "dfp_cia_aberta" if doc_type == 'DFP' else "itr_cia_aberta"
        year_dir = os.path.join(self.data_dir, f"{pattern_prefix}_{year}")
        if not os.path.exists(year_dir):
            # Fallback: maybe files are in main dir with year suffix
            year_dir = self.data_dir 

        def read_and_filter(suffix, cols_of_interest=None):
            search_pattern = os.path.join(year_dir, f"*{pattern_prefix}_{suffix}_{year}.csv")
            files = glob.glob(search_pattern)
            if not files: 
                # print(f"  No files found for {suffix} in {year_dir}")
                return pd.DataFrame()
            
            try:
                # print(f"  Reading {files[0]}...")
                df = pd.read_csv(files[0], sep=';', encoding='ISO-8859-1', low_memory=False)
                
                # Basic cleanup
                if 'ORDEM_EXERC' in df.columns:
                    # Normalize to Upper Case because some files use 'ÚLTIMO', others 'Último'
                    df = df[df['ORDEM_EXERC'].astype(str).str.upper() == 'ÚLTIMO']
                
                if 'CD_CONTA' in df.columns:
                    df['CD_CONTA'] = df['CD_CONTA'].astype(str)
                    print(f"DEBUG: CD_CONTA sample: {df['CD_CONTA'].head().tolist()}")

                # Filter rows if we know the codes (Optimization)
                if cols_of_interest:
                    pattern = '^(' + '|'.join([c.replace('.', r'\.') for c in cols_of_interest]) + ')'
                    print(f"DEBUG: Pattern: {pattern}")
                    df = df[df['CD_CONTA'].str.contains(pattern, regex=True, na=False)]
                    print(f"DEBUG: Filtered size: {len(df)}")
                
                return df
            except Exception as e:
                print(f"Error reading {files[0]}: {e}")
                return pd.DataFrame()

        # Codes we want
        # DRE: 3.01 (Rev), 3.05 (EBIT), 3.11 (Net Inc), 3.99 (EPS)
        dre_codes = ['3.01', '3.05', '3.11', '3.99']
        df_dre = read_and_filter("DRE_con", dre_codes)

        # BPP/BPA: 1 (Asset), 1.01 (Cash), 2.01.04 (Debt CP), 2.02.01 (Debt LP), 2.03 (Equity)
        bpp_codes = ['2.01.04', '2.02.01', '2.03']
        bpa_codes = ['1', '1.01'] # 1 is tricky, might match 10? No, usually exact matches or startswith. '1' matches '1'
        
        # BPP/BPA often separate files
        df_bpp = read_and_filter("BPP_con", bpp_codes)
        df_bpa = read_and_filter("BPA_con", bpa_codes)
        
        # DFC: 6.01, 6.02, 6.03... just read all getting dividend text?
        # Reading all DFC is safer to grep text.
        df_dfc_md = read_and_filter("DFC_MD_con")
        df_dfc_mi = read_and_filter("DFC_MI_con")
        df_dfc = pd.concat([df_dfc_md, df_dfc_mi], ignore_index=True)

        # --- Aggregation Helper ---
        def extract_metric(df, code_prefix, metric_name, exact=False, use_text_grep=None):
            if df.empty: return None
            
            # Select rows
            if use_text_grep:
                mask = df['DS_CONTA'].str.contains(use_text_grep, case=False, na=False)
                subset = df[mask].copy()
            elif exact:
                subset = df[df['CD_CONTA'] == code_prefix].copy()
            else:
                subset = df[df['CD_CONTA'].str.startswith(code_prefix)].copy()
            
            if subset.empty: return None
            
            # Scale
            # Assume 'ESCALA_MOEDA' exists
            if 'ESCALA_MOEDA' in subset.columns:
                subset['multiplier'] = subset['ESCALA_MOEDA'].map({'MIL': 1000, 'MILHAO': 1000000}).fillna(1)
                subset['VL_CONTA'] *= subset['multiplier']
            
            # Pivot to get one row per (CD_CVM, DT_FIM_EXERC)
            # If multiple rows match (e.g. sub-accounts for Debt), we SUM them.
            
            # Group by Entity and Date
            grouped = subset.groupby(['CD_CVM', 'DT_FIM_EXERC', 'DENOM_CIA'])['VL_CONTA'].sum().reset_index()
            grouped.rename(columns={'VL_CONTA': metric_name}, inplace=True)
            return grouped

        # Extract all metrics
        metrics_dfs = []

        metrics_dfs.append(extract_metric(df_dre, '3.01', 'revenue', exact=True))
        metrics_dfs.append(extract_metric(df_dre, '3.05', 'ebit', exact=True))
        metrics_dfs.append(extract_metric(df_dre, '3.11', 'net_income', exact=True))
        
        # EPS - Try Basic ON (3.99.01.01)
        metrics_dfs.append(extract_metric(df_dre, '3.99.01.01', 'eps', exact=True))

        metrics_dfs.append(extract_metric(df_bpa, '1', 'total_assets', exact=True))
        metrics_dfs.append(extract_metric(df_bpa, '1.01', 'cash', exact=True))
        
        metrics_dfs.append(extract_metric(df_bpp, '2.03', 'equity', exact=True))
        
        # Debt: Sum of CP and LP
        # We can extract them separately and sum later, or extract combined here?
        # Let's extract separate.
        metrics_dfs.append(extract_metric(df_bpp, '2.01.04', 'debt_cp')) # Starts with
        metrics_dfs.append(extract_metric(df_bpp, '2.02.01', 'debt_lp')) # Starts with
        
        # Dividends from DFC
        metrics_dfs.append(extract_metric(df_dfc, None, 'dividends_paid', use_text_grep='Dividendos|Juros sobre'))

        # Merge all
        # Base is the distinct list of companies/dates
        base_df = None
        for m_df in metrics_dfs:
            if m_df is None: continue
            if base_df is None:
                base_df = m_df
            else:
                # Merge on keys
                base_df = pd.merge(base_df, m_df, on=['CD_CVM', 'DT_FIM_EXERC', 'DENOM_CIA'], how='outer')
        
        if base_df is None: return pd.DataFrame()

        # Fill NaNs
        base_df.fillna(0, inplace=True)
        
        # Calculate derived
        base_df['gross_debt'] = base_df['debt_cp'] + base_df['debt_lp']
        base_df['net_debt'] = base_df['gross_debt'] - base_df['cash']
        
        # Add metadata
        base_df['doc_type'] = doc_type
        
        return base_df

if __name__ == "__main__":
    # Test
    parser = CVMParser()
    df = parser.parse_financials(2023, 'DFP')
    print(df.head())
