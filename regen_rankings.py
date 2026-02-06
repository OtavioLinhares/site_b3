import json
import pandas as pd
import sys

def get_rank_score(series, ascending=True):
    return series.rank(pct=True, ascending=ascending)

def generate_rankings(assets):
    df = pd.DataFrame(assets)
    if df.empty:
        return {}

    # Apply strict liquidity filter if not already applied (though b3_stocks might have it, rankings validation ensures it)
    # The user asked for strict liquidity check in rankings.
    # b3_stocks.json usually contains all processed data.
    # Ensure we use the same liquidty threshold as the frontend/pipeline if needed, 
    # but the pipeline usually exports everything valid.
    # Let's filter df by liq_2m >= 1000000 just in case b3_stocks has everything.
    # Wait, previous pipeline export might include low liq stocks?
    # Let's check pipeline.py. It filters by `limit` during fetch but `processedData` in frontend filters by 1M.
    # To be safe, let's filter here too.
    
    
    # HOTFIX: Rename PRIOC3 -> PRIO3 immediately
    if 'ticker' in df.columns:
        df['ticker'] = df['ticker'].replace('PRIOC3', 'PRIO3')

    # Deduplication Logic: One ticker per company.
    # User preference: "Principal (normally PN)".
    # Methodology:
    # 1. Extract base ticker (e.g. PETR from PETR4).
    # 2. Assign priority: 4 (PN) = 1, 3 (ON) = 2, 11 (UNIT) = 3, Others = 4.
    # 3. Sort by Base + Priority.
    # 4. Drop duplicates on Base.
    
    if 'ticker' in df.columns:
        df['base_ticker'] = df['ticker'].str[:4]
        
        def get_priority(ticker):
             if ticker.endswith('4'): return 1 # PN
             if ticker.endswith('3'): return 2 # ON
             if ticker.endswith('11'): return 3 # UNIT
             return 4
             
        df['priority'] = df['ticker'].apply(get_priority)
        
        # Sort by Base (asc) and Priority (asc)
        df = df.sort_values(by=['base_ticker', 'priority'], ascending=[True, True])
        
        # Keep first (highest priority)
        df = df.drop_duplicates(subset='base_ticker', keep='first')

    
    if 'liq_2m' in df.columns:
        # Cast to numeric just in case
        df['liq_2m'] = pd.to_numeric(df['liq_2m'], errors='coerce').fillna(0)
        df = df[df['liq_2m'] >= 1000000].copy()

    # 1. Ranking: Oportunidades (Pontinha de Cigarro)
    # Metodologia: Baixo P/VP + Margem Líquida Positiva
    if 'p_vp' not in df.columns:
        df['p_vp'] = 100.0 # Fallback

    # Filters: P/VP > 0, P/VP < 1, (Net Margin > 0 OR ROE > 0)
    # BBAS3 has margin 0.0 in Fundamentus but ROE > 0.
    
    df_cigar = df[(df['p_vp'] > 0) & (df['p_vp'] < 1) & ((df['net_margin'] > 0) | (df['roe'] > 0))].copy()
    
    if not df_cigar.empty:
        ranking_cigar = df_cigar.sort_values(by='p_vp', ascending=True).head(10)
    else:
        ranking_cigar = pd.DataFrame()

    # 2. Ranking: Dividendos, Margem e P/L (Composite Score)
    # Methodology: Maximize DY and Margin, Minimize P/L.
    df_div = df[(df['dy'] > 0) & (df['p_l'] > 0)].copy()
    
    if not df_div.empty:
        # Calculate percentile ranks (0 to 1)
        df_div['rank_dy'] = get_rank_score(df_div['dy'], ascending=True)      # High DY = High Score
        df_div['rank_margin'] = get_rank_score(df_div['net_margin'], ascending=True) # High Margin = High Score
        df_div['rank_pl'] = get_rank_score(df_div['p_l'], ascending=False)    # Low P/L = High Score
        
        # Composite Score (Equal weights)
        df_div['final_score'] = df_div['rank_dy'] + df_div['rank_margin'] + df_div['rank_pl']
        
        ranking_div = df_div.sort_values(by='final_score', ascending=False).head(10)
    else:
        ranking_div = pd.DataFrame()

    # 3. Ranking: Crescimento (5 Anos)
    # Filters: Revenue Growth > 10%, Net Margin > 12%
    df_growth = df[(df['revenue_growth_5y'] > 0.10) & (df['net_margin'] > 0.12)].copy()
    if not df_growth.empty:
        ranking_growth = df_growth.sort_values(by='revenue_growth_5y', ascending=False).head(10)
    else:
        ranking_growth = pd.DataFrame()
    
    return {
        "valor_qualidade": ranking_cigar.to_dict(orient='records'),
        "dividendos": ranking_div.to_dict(orient='records'),
        "crescimento": ranking_growth.to_dict(orient='records')
    }

def main():
    try:
        with open('web/public/data/b3_stocks.json', 'r') as f:
            data = json.load(f)
        
        # Structure is { "data": [...] }
        assets = data.get('data', [])
        print(f"Loaded {len(assets)} assets.")
        
        # Remove TRPN3 manually just in case
        assets = [a for a in assets if a['ticker'] != 'TRPN3']
        
        rankings = generate_rankings(assets)
        
        output = { "data": rankings }
        
        with open('web/public/data/rankings.json', 'w') as f:
            json.dump(output, f, indent=2)
            
        print("Rankings regenerated successfully.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
