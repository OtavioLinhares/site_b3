import json
import pandas as pd
import numpy as np

try:
    with open('public/data/b3_stocks.json', 'r') as f:
        data = json.load(f)
        stocks = data.get('data', [])
except FileNotFoundError:
    print("Error: public/data/b3_stocks.json not found.")
    exit()

df = pd.DataFrame(stocks)

# Helper to match the frontend 'simplifyName' and 'isHolding' logic
def simplify_name(name):
    mapping = {
        'Petróleo, Gás e Biocombustíveis': 'Petróleo e Gás',
        'Serv. Méd. Hospit. Análises e Diagnósticos': 'Saúde',
        'Intermediários Financeiros': 'Financeiro',
        'Utilidade Pública': 'Utilidade',
        # ... (simplified for this check)
    }
    return mapping.get(name, name)

def is_holding(name):
    if not name: return False
    lower = name.lower()
    return any(x in lower for x in ['holding', 'banco', 'intermediários', 'segur', 'financeiro'])

df['sector_simple'] = df['sector'].apply(simplify_name)

# 1. Check for sectors with many 0% margins (potential missing data)
print("--- Sectors with high % of Zero Margins (potential bug candidates) ---")
zero_margins = df[df['net_margin'] == 0].groupby('sector_simple').size()
total_counts = df.groupby('sector_simple').size()
ratio = (zero_margins / total_counts).fillna(0).sort_values(ascending=False)

for sec, r in ratio.head(10).items():
    if r > 0:
        print(f"{sec}: {r:.1%} zero margins ({zero_margins[sec]}/{total_counts[sec]})")

# 2. Analyze 'Energia Elétrica' (usually simplified to Utilidade or kept raw?)
# Let's check subsectors or exact names for Energy
energy_keywords = ['energ', 'eletric', 'utilidade']
energy_df = df[df['sector'].str.lower().str.contains('|'.join(energy_keywords), na=False)].copy()

if not energy_df.empty:
    print("\n--- Energy / Utility Sector Analysis ---")
    # Weighted Average
    total_mcap = energy_df['market_cap'].sum()
    weighted_margin = (energy_df['net_margin'] * energy_df['market_cap']).sum() / total_mcap
    
    # Simple Average
    simple_margin = energy_df['net_margin'].mean()
    
    # Median
    median_margin = energy_df['net_margin'].median()
    
    print(f"Sector: Utilidade/Energia")
    print(f"Weighted Avg Margin: {weighted_margin:.2%}")
    print(f"Simple Avg Margin:   {simple_margin:.2%}")
    print(f"Median Margin:       {median_margin:.2%}")
    print(f"Count: {len(energy_df)}")
    
    print("\nTop 5 Largest Companies (skewing weighted avg):")
    print(energy_df.sort_values(by='market_cap', ascending=False)[['ticker', 'market_cap', 'net_margin']].head(5))

    print("\nTop 5 Highest Margin Companies:")
    print(energy_df.sort_values(by='net_margin', ascending=False)[['ticker', 'market_cap', 'net_margin']].head(5))
