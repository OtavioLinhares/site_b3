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
                
                if 'GRUPO_DFP' in df.columns:
                    df = df[df['GRUPO_DFP'].astype(str).str.contains('CONSOLID', case=False, na=False)]
                
                if 'CD_CONTA' in df.columns:
                    df['CD_CONTA'] = df['CD_CONTA'].astype(str)

                # Filter rows if we know the codes (Optimization)
                if cols_of_interest:
                    pattern = '^(?:' + '|'.join([c.replace('.', r'\.') for c in cols_of_interest]) + ')'
                    df = df[df['CD_CONTA'].str.contains(pattern, regex=True, na=False)]
                
                return df
            except Exception as e:
                print(f"Error reading {files[0]}: {e}")
                return pd.DataFrame()

        # Codes we want
        # DRE: 3.01 (Rev), 3.05 (EBIT), 3.11 (Net Inc), 3.99 (EPS)
        dre_codes = ['3.01', '3.05', '3.09', '3.10', '3.11', '3.99']
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

        df_capital = read_and_filter("composicao_capital")

        # --- Aggregation Helper ---
        def extract_metric(df, code_prefix, metric_name, exact=False, use_text_grep=None):
            if df.empty: return None
            
            # Allow passing a collection of codes; sum all matches.
            if isinstance(code_prefix, (list, tuple, set)):
                for single_prefix in code_prefix:
                    result = extract_metric(
                        df,
                        single_prefix,
                        metric_name,
                        exact=exact,
                        use_text_grep=use_text_grep,
                    )
                    if result is not None and not result.empty:
                        return result
                return None
            
            # Select rows
            if use_text_grep:
                mask = df['DS_CONTA'].str.contains(use_text_grep, case=False, na=False)
                subset = df[mask].copy()
            elif exact:
                subset = df[df['CD_CONTA'] == code_prefix].copy()
            else:
                subset = df[df['CD_CONTA'].str.startswith(code_prefix)].copy()
            
            if subset.empty: return None
            
            # Deduplicate by (company, date), keeping the period that starts earlier (YTD)
            if {'CD_CVM', 'DT_FIM_EXERC', 'DENOM_CIA', 'DT_INI_EXERC'}.issubset(subset.columns):
                subset['DT_INI_EXERC'] = pd.to_datetime(subset['DT_INI_EXERC'], errors='coerce')
                subset = subset.sort_values('DT_INI_EXERC').drop_duplicates(
                    subset=['CD_CVM', 'DT_FIM_EXERC', 'DENOM_CIA'], keep='first'
                )

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
        net_income_control_df = extract_metric(df_dre, '3.11.01', 'net_income_control', exact=True)
        if net_income_control_df is None or net_income_control_df.empty:
            net_income_control_df = extract_metric(df_dre, '3.09.01', 'net_income_control', exact=True)
        metrics_dfs.append(net_income_control_df)

        net_income_total_df = extract_metric(df_dre, ['3.11', '3.10', '3.09'], 'net_income_total', exact=True)
        if net_income_total_df is None or net_income_total_df.empty:
            net_income_total_df = extract_metric(df_dre, '3.09', 'net_income_total', exact=True)
        metrics_dfs.append(net_income_total_df)
        
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

        if not df_capital.empty:
            for col in [
                'QT_ACAO_TOTAL_CAP_INTEGR',
                'QT_ACAO_PREF_CAP_INTEGR',
                'QT_ACAO_ORDIN_CAP_INTEGR',
                'QT_ACAO_TOTAL_TESOURO',
                'QT_ACAO_PREF_TESOURO',
                'QT_ACAO_ORDIN_TESOURO',
            ]:
                if col in df_capital.columns:
                    df_capital[col] = pd.to_numeric(df_capital[col], errors='coerce').fillna(0)
            df_capital['DT_REFER'] = pd.to_datetime(df_capital['DT_REFER'], errors='coerce')
            df_capital['shares_outstanding'] = (
                df_capital.get('QT_ACAO_TOTAL_CAP_INTEGR', 0)
                - df_capital.get('QT_ACAO_TOTAL_TESOURO', 0)
            )
            lookup = None
            if not df_dre.empty and {'CNPJ_CIA', 'CD_CVM'}.issubset(df_dre.columns):
                lookup = (
                    df_dre[['CNPJ_CIA', 'CD_CVM', 'DENOM_CIA']]
                    .drop_duplicates()
                    .rename(columns={'DENOM_CIA': 'DENOM_CIA_DRE'})
                )
            if lookup is not None:
                df_capital = df_capital.merge(lookup, on='CNPJ_CIA', how='left')
                df_capital['DENOM_CIA'] = df_capital['DENOM_CIA_DRE'].fillna(df_capital.get('DENOM_CIA'))
            if 'CD_CVM' in df_capital.columns:
                shares_df = df_capital[
                    df_capital['CD_CVM'].notna()
                    & df_capital['DT_REFER'].notna()
                ][['CD_CVM', 'DT_REFER', 'DENOM_CIA', 'shares_outstanding']].copy()
                shares_df.rename(columns={'DT_REFER': 'DT_FIM_EXERC'}, inplace=True)
                shares_df['DT_FIM_EXERC'] = shares_df['DT_FIM_EXERC'].dt.strftime('%Y-%m-%d')
                metrics_dfs.append(shares_df)

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
        
        if base_df is None:
            return pd.DataFrame()

        # Combine net income preference for control results when available
        if 'net_income_control' in base_df.columns or 'net_income_total' in base_df.columns:
            base_df['net_income'] = pd.NA
            if 'net_income_control' in base_df.columns:
                base_df['net_income'] = base_df['net_income_control']
            if 'net_income_total' in base_df.columns:
                base_df['net_income'] = base_df['net_income'].fillna(base_df['net_income_total'])
        base_df.drop(columns=['net_income_control', 'net_income_total'], inplace=True, errors='ignore')

        # Normalize dates for ordering and forward-fill share counts
        if 'DT_FIM_EXERC' in base_df.columns:
            base_df['DT_FIM_EXERC'] = pd.to_datetime(base_df['DT_FIM_EXERC'], errors='coerce')
        if 'shares_outstanding' in base_df.columns:
            base_df['shares_outstanding'] = pd.to_numeric(base_df['shares_outstanding'], errors='coerce')
            shares_mask = (base_df['shares_outstanding'] <= 0) | (base_df['shares_outstanding'].isna())
            base_df.loc[shares_mask, 'shares_outstanding'] = pd.NA
        sort_keys = ['CD_CVM', 'DT_FIM_EXERC']
        if 'doc_type' in base_df.columns:
            sort_keys.append('doc_type')
        base_df.sort_values(sort_keys, inplace=True)
        if 'shares_outstanding' in base_df.columns:
            base_df['shares_outstanding'] = (
                base_df.groupby('CD_CVM')['shares_outstanding']
                .ffill()
                .bfill()
            )

        # Fill numeric NaNs selectively (after share propagation)
        numeric_cols = [
            'revenue',
            'ebit',
            'net_income',
            'eps',
            'total_assets',
            'cash',
            'equity',
            'debt_cp',
            'debt_lp',
            'dividends_paid',
            'gross_debt',
            'net_debt',
        ]
        for col in numeric_cols:
            if col in base_df.columns:
                base_df[col] = pd.to_numeric(base_df[col], errors='coerce').fillna(0)

        if 'shares_outstanding' in base_df.columns:
            base_df['shares_outstanding'] = pd.to_numeric(base_df['shares_outstanding'], errors='coerce').fillna(0)
        if 'DT_FIM_EXERC' in base_df.columns:
            base_df['DT_FIM_EXERC'] = base_df['DT_FIM_EXERC'].dt.strftime('%Y-%m-%d')
        
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
