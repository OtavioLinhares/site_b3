import json
import fundamentus
import pandas as pd

def patch_data():
    print("Fetching Fundamentus data...")
    df = fundamentus.get_resultado()
    df = df.reset_index()
    # Rename columns to match our schema
    # Fundamentus columns: 'papel', 'cotacao', 'pl', 'pvp', 'psr', 'dy', 'pa', 'pcg', 'pebit', 'pacl', 'evebit', 'evebitda', 'mrgebit', 'mrgliq', 'roic', 'roe', 'liqc', 'liq2m', 'patrliq', 'divbpatr', 'c5y'
    df.rename(columns={
        'papel': 'ticker', 
        'pvp': 'p_vp',
        'mrgliq': 'net_margin',
        'liq2m': 'liq_2m',
        'pl': 'p_l',
        'dy': 'dy',
        'c5y': 'revenue_growth_5y',
        'roe': 'roe'
    }, inplace=True)
    
    # Create lookups
    data_map = df.set_index('ticker').to_dict(orient='index')
    
    print("Loading b3_stocks.json...")
    try:
        with open('web/public/data/b3_stocks.json', 'r') as f:
            data = json.load(f)
            
        assets = data.get('data', [])
        updated_count = 0
        
        for asset in assets:
            ticker = asset.get('ticker')
            # Handle PRIOC3 case here too
            if ticker == 'PRIOC3':
                asset['ticker'] = 'PRIO3'
                ticker = 'PRIO3'
                
            if ticker in data_map:
                row = data_map[ticker]
                # Update fields if they exist in valid set
                asset['p_vp'] = float(row.get('p_vp', 0))
                asset['net_margin'] = float(row.get('net_margin', 0))
                asset['liq_2m'] = float(row.get('liq_2m', 0))
                asset['p_l'] = float(row.get('p_l', 0))
                asset['dy'] = float(row.get('dy', 0))
                asset['revenue_growth_5y'] = float(row.get('revenue_growth_5y', 0))
                asset['roe'] = float(row.get('roe', 0))
                
                updated_count += 1
            else:
                # Try finding without '3'/'4' suffix match? No, unsafe.
                # Just leave as is, regen_rankings will handle missing
                pass

        print(f"Updated {updated_count} assets with P/VP data.")
        
        # Save back
        with open('web/public/data/b3_stocks.json', 'w') as f:
            json.dump(data, f, indent=0) # Minimize size, indent 0 or None
            
        print("b3_stocks.json patched successfully.")
        
    except Exception as e:
        print(f"Error patching data: {e}")

if __name__ == "__main__":
    patch_data()
