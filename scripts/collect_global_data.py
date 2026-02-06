"""
Global Market Data Collector (Expanded)
Collects aggregated market data from Top 50 companies of major global stock indices.
Supports USA (S&P 500), UK (FTSE 100), Germany (DAX 40), Japan (Nikkei 225), and China (Hang Seng).
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.alpha_vantage_client import AlphaVantageClient
import json
import logging
import time
from typing import List, Dict, Optional

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/global_collection.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API Key
ALPHA_VANTAGE_API_KEY = "GKNR1T3Z4H3JLZUZ"

# Ticker Lists
GLOBAL_MARKETS = {
    "USA": {
        "name": "Estados Unidos",
        "tickers": [
            "NVDA", "AAPL", "GOOGL", "MSFT", "AMZN", "META", "TSLA", "AVGO", "BRK.B", "WMT", 
            "LLY", "JPM", "V", "XOM", "JNJ", "MA", "COST", "MU", "ORCL", "BAC", 
            "HD", "ABBV", "PG", "CVX", "NFLX", "KO", "PLTR", "AMD", "CAT", "GE", 
            "CSCO", "MRK", "WFC", "GS", "MS", "PM", "IBM", "RTX", "LRCX", "UNH", 
            "INTC", "AXP", "AMAT", "MCD", "PEP", "TMUS", "LIN", "TMO", "C", "ADBE"
        ],
        "exchange": "NYSE/NASDAQ"
    },
    "UK": {
        "name": "Reino Unido",
        "tickers": [
            "HSBA.L", "AZN.L", "SHEL.L", "ULVR.L", "RR.L", "BATS.L", "RIO.L", "GSK.L", "BP.L", "BARC.L", 
            "LLOY.L", "BA.L", "NG.L", "GLEN.L", "REL.L", "NWG.L", "LSEG.L", "STAN.L", "RKT.L", "AAL.L", 
            "CPG.L", "DGE.L", "ANTO.L", "HLN.L", "III.L", "FRES.L", "CCEP.L", "PRU.L", "SSE.L", "EXPN.L", 
            "TSCO.L", "VOD.L", "IMB.L", "FLTR.L", "AHT.L", "IHG.L", "IAG.L", "AV.L", "BT-A.L", "AIBG.L", 
            "IPC.L", "SWR.L", "NXT.L", "CKI.L", "LGEN.L", "CCH.L", "HLMA.L", "ABF.L", "SMT.L", "AAF.L"
        ],
        "exchange": "LSE"
    },
    "Germany": {
        "name": "Alemanha",
        "tickers": [
            "ADS.DE", "AIR.DE", "ALV.DE", "BAS.DE", "BAYN.DE", "BEI.DE", "BMW.DE", "BNR.DE", "CBK.DE", "CON.DE", 
            "1COV.DE", "DTG.DE", "DBK.DE", "DB1.DE", "DHL.DE", "DTE.DE", "EOAN.DE", "FME.DE", "FRE.DE", "G1A.DE", 
            "HNR1.DE", "HEI.DE", "HFG.DE", "HEN3.DE", "IFX.DE", "LIN.DE", "MBG.DE", "MRK.DE", "MTX.DE", "MUV2.DE", 
            "PAH3.DE", "RHM.DE", "RWE.DE", "SAP.DE", "SIE.DE", "SHL.DE", "ENR.DE", "SY1.DE", "VOW3.DE", "VNA.DE"
        ],
        "exchange": "XETRA"
    },
    "Japan": {
        "name": "Japão",
        "tickers": [
            "7203.T", "6758.T", "8306.T", "6861.T", "9432.T", "8035.T", "9983.T", "4063.T", "6501.T", "8058.T", 
            "9433.T", "9984.T", "8316.T", "8411.T", "7267.T", "4502.T", "9022.T", "4503.T", "6752.T", "6902.T", 
            "6098.T", "4568.T", "7974.T", "8053.T", "8001.T", "8031.T", "6301.T", "7751.T", "3382.T", "7741.T", 
            "6954.T", "6981.T", "8750.T", "8766.T", "6503.T", "8591.T", "5108.T", "4901.T", "4452.T", "6762.T", 
            "2914.T", "6326.T", "5020.T", "6390.T", "9531.T", "9020.T", "7733.T", "6753.T", "6971.T", "6273.T"
        ],
        "exchange": "TSE"
    },
    "China": {
        "name": "China/HK",
        "tickers": [
            "0005.HK", "0700.HK", "9988.HK", "1299.HK", "0939.HK", "1810.HK", "3690.HK", "1398.HK", "0941.HK", "0388.HK", 
            "2318.HK", "3988.HK", "0883.HK", "9888.HK", "9618.HK", "1929.HK", "1088.HK", "1211.HK", "1024.HK", "2269.HK", 
            "0016.HK", "0002.HK", "2628.HK", "1109.HK", "0011.HK", "0066.HK", "1928.HK", "0012.HK", "2007.HK", "0027.HK", 
            "0823.HK", "0267.HK", "0762.HK", "0669.HK", "2020.HK", "0003.HK", "0001.HK", "0017.HK", "1997.HK", "2388.HK", 
            "0175.HK", "1898.HK", "0960.HK", "0291.HK", "0101.HK", "1816.HK", "1038.HK", "0386.HK", "0688.HK", "2688.HK"
        ],
        "exchange": "HKEX"
    }
}

CHECKPOINT_FILE = "public/data/global_markets_checkpoint.json"
FINAL_OUTPUT = "public/data/global_markets.json"

def load_checkpoint() -> Dict:
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_checkpoint(data: Dict):
    os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def collect_country_data(client: AlphaVantageClient, country_code: str, config: Dict, existing_data: Dict) -> Dict:
    logger.info(f"Processing {config['name']} ({country_code})...")
    
    country_results = existing_data.get(country_code, {
        "country": config['name'],
        "country_code": country_code,
        "exchange": config['exchange'],
        "companies": []
    })
    
    collected_symbols = {c['symbol'] for c in country_results['companies']}
    
    for ticker in config['tickers']:
        if ticker in collected_symbols:
            continue
            
        logger.info(f"  [{country_code}] Fetching {ticker}...")
        overview = client.get_company_overview(ticker)
        
        if overview:
            country_results['companies'].append(overview)
            logger.info(f"    ✓ {ticker}: {overview['name']} added.")
            # Save checkpoint after each successful fetch
            existing_data[country_code] = country_results
            save_checkpoint(existing_data)
        else:
            logger.warning(f"    ✗ {ticker}: Failed or no data.")
            
        # Alpha Vantage Free Tier: 5 calls per minute (12s interval)
        # We use 15s to be safe and avoid "Note" messages.
        time.sleep(15)
        
    return country_results

def finalize_metrics(global_data: Dict):
    final_data = {}
    for code, country_info in global_data.items():
        companies = country_info.get('companies', [])
        if not companies:
            continue
            
        total_market_cap = sum(c['market_cap'] for c in companies)
        
        valid_pe = [c['pe_ratio'] for c in companies if c['pe_ratio'] > 0]
        avg_pe = sum(valid_pe) / len(valid_pe) if valid_pe else 0
        
        valid_margin = [c['profit_margin'] for c in companies if c['profit_margin'] != 0]
        avg_margin = sum(valid_margin) / len(valid_margin) if valid_margin else 0
        
        valid_roe = [c['roe'] for c in companies if c['roe'] != 0]
        avg_roe = sum(valid_roe) / len(valid_roe) if valid_roe else 0
        
        final_data[code] = {
            "country": country_info['country'],
            "country_code": code,
            "exchange": country_info['exchange'],
            "total_market_cap": total_market_cap,
            "avg_pe_ratio": round(avg_pe, 2),
            "avg_profit_margin": round(avg_margin * 100, 2),
            "avg_roe": round(avg_roe * 100, 2),
            "companies_analyzed": len(companies),
            "companies": companies
        }
    return final_data

def main():
    logger.info("Starting Persistent Global Market Data Collection...")
    os.makedirs("logs", exist_ok=True)
    
    client = AlphaVantageClient(ALPHA_VANTAGE_API_KEY)
    global_data = load_checkpoint()
    
    try:
        for country_code, config in GLOBAL_MARKETS.items():
            collect_country_data(client, country_code, config, global_data)
            
        # Finalize and save
        logger.info("Finalizing data...")
        final_results = finalize_metrics(global_data)
        
        output = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "data": final_results
        }
        
        with open(FINAL_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
            
        logger.info(f"✓ FULL SUCCESS: Global market data saved to {FINAL_OUTPUT}")
        
    except KeyboardInterrupt:
        logger.info("Interrupted. Data saved in checkpoint.")
    except Exception as e:
        logger.error(f"FATAL ERROR: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
