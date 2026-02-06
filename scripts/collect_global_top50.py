"""
Collect aggregated valuation metrics for the 40–50 maiores empresas de cada
bolsa monitorada (fora a B3).

Executa via:
    python3 scripts/collect_global_top50.py

Saídas:
- public/data/world_comparison.json  -> resumo por bolsa (P/L e margem média)
- public/data/world_markets.json     -> detalhes por bolsa e empresa

Dependências: yfinance
"""

from __future__ import annotations

import json
import logging
import math
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import requests_cache
import yfinance as yf

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from etl.exporter import Exporter

logger = logging.getLogger("collect_global_top50")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

CACHE_DIR = ROOT_DIR / "cache" / "yf_global"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 6 * 60 * 60  # 6 horas
REQUEST_DELAY = 4.0  # segundos entre requisições para evitar 429
MAX_RETRIES = 5
RETRY_BACKOFF = 8  # segundos de espera incremental quando houver 429

SESSION = requests_cache.CachedSession(
    cache_name=str(CACHE_DIR / "yfinance"),
    backend="sqlite",
    expire_after=CACHE_TTL,
    allowable_methods=("GET", "POST"),
)
SESSION.headers.update(
    {
        "User-Agent": "b3-dashboard/1.0 (+https://example.com)",
        "Accept": "application/json,text/plain,*/*",
    }
)

# Listas ~top 50 por bolsa (não inclui B3; a B3 já é coberta pelo pipeline local)
GLOBAL_MARKETS: Dict[str, Dict[str, object]] = {
    "NASDAQ": {
        "name": "NASDAQ",
        "exchange": "NASDAQ",
        "flag": "🇺🇸",
        "source": "yfinance",
        "tickers": [
            "AAPL",
            "MSFT",
            "GOOGL",
            "GOOG",
            "AMZN",
            "NVDA",
            "META",
            "TSLA",
            "AVGO",
            "PEP",
            "CSCO",
            "ADBE",
            "NFLX",
            "INTC",
            "AMD",
            "QCOM",
            "TXN",
            "INTU",
            "AMAT",
            "LRCX",
            "MU",
            "BKNG",
            "ADP",
            "PYPL",
            "PDD",
            "PANW",
            "MRNA",
            "KLAC",
            "VRTX",
            "GILD",
            "REGN",
            "IDXX",
            "MNST",
            "ORLY",
            "COST",
            "SBUX",
            "CDNS",
            "SNPS",
            "CHTR",
            "LULU",
            "MAR",
            "BIIB",
            "NXPI",
            "ROST",
            "CTAS",
        ],
    },
    "NYSE": {
        "name": "NYSE",
        "exchange": "NYSE",
        "flag": "🇺🇸",
        "source": "yfinance",
        "tickers": [
            "BRK-B",
            "JPM",
            "V",
            "MA",
            "XOM",
            "JNJ",
            "WMT",
            "HD",
            "UNH",
            "PG",
            "CVX",
            "DIS",
            "KO",
            "BAC",
            "C",
            "GS",
            "MS",
            "T",
            "IBM",
            "BA",
            "CAT",
            "MMM",
            "HON",
            "UPS",
            "LMT",
            "NKE",
            "BLK",
            "SPGI",
            "LOW",
            "DHR",
            "CVS",
            "DE",
            "GE",
            "AXP",
            "PLD",
            "PNC",
            "USB",
            "MO",
            "FDX",
            "SO",
            "DUK",
            "TGT",
            "BDX",
            "APD",
            "SCHW",
        ],
    },
    "NSE": {
        "name": "Índia",
        "exchange": "NSE",
        "flag": "🇮🇳",
        "source": "yfinance",
        "tickers": [
            "RELIANCE.NS",
            "TCS.NS",
            "HDFCBANK.NS",
            "ICICIBANK.NS",
            "INFY.NS",
            "ITC.NS",
            "LT.NS",
            "AXISBANK.NS",
            "KOTAKBANK.NS",
            "SBIN.NS",
            "BHARTIARTL.NS",
            "ASIANPAINT.NS",
            "HINDUNILVR.NS",
            "BAJFINANCE.NS",
            "BAJAJFINSV.NS",
            "HCLTECH.NS",
            "WIPRO.NS",
            "ULTRACEMCO.NS",
            "M&M.NS",
            "SUNPHARMA.NS",
            "TITAN.NS",
            "MARUTI.NS",
            "POWERGRID.NS",
            "NESTLEIND.NS",
            "TATASTEEL.NS",
            "JSWSTEEL.NS",
            "NTPC.NS",
            "GRASIM.NS",
            "ONGC.NS",
            "HDFCLIFE.NS",
            "SBILIFE.NS",
            "ADANIGREEN.NS",
            "ADANIPORTS.NS",
            "ADANIENT.NS",
            "DIVISLAB.NS",
            "TECHM.NS",
            "LTIM.NS",
            "EICHERMOT.NS",
            "HEROMOTOCO.NS",
            "COALINDIA.NS",
            "VEDL.NS",
            "PIDILITIND.NS",
            "SHREECEM.NS",
            "BAJAJ-AUTO.NS",
            "BRITANNIA.NS",
        ],
    },
    "TADAWUL": {
        "name": "Arábia Saudita",
        "exchange": "TADAWUL",
        "flag": "🇸🇦",
        "source": "yfinance",
        "tickers": [
            "2222.SR",
            "2010.SR",
            "1180.SR",
            "1120.SR",
            "1050.SR",
            "1140.SR",
            "1010.SR",
            "1080.SR",
            "1090.SR",
            "1040.SR",
            "1060.SR",
            "1020.SR",
            "1030.SR",
            "1111.SR",
            "1211.SR",
            "2030.SR",
            "2080.SR",
            "2290.SR",
            "2350.SR",
            "2380.SR",
            "3010.SR",
            "3020.SR",
            "3030.SR",
            "3040.SR",
            "4010.SR",
            "4003.SR",
            "4007.SR",
            "4002.SR",
            "4050.SR",
            "4070.SR",
            "4090.SR",
            "4100.SR",
            "4161.SR",
            "4200.SR",
            "5110.SR",
            "6010.SR",
            "6050.SR",
            "8100.SR",
            "8170.SR",
            "8210.SR",
            "8230.SR",
            "9510.SR",
        ],
    },
    "ASX": {
        "name": "Austrália",
        "exchange": "ASX",
        "flag": "🇦🇺",
        "source": "yfinance",
        "tickers": [
            "BHP.AX",
            "CSL.AX",
            "CBA.AX",
            "NAB.AX",
            "WBC.AX",
            "ANZ.AX",
            "WES.AX",
            "TLS.AX",
            "WOW.AX",
            "FMG.AX",
            "MQG.AX",
            "WDS.AX",
            "GMG.AX",
            "RIO.AX",
            "BXB.AX",
            "SCG.AX",
            "COL.AX",
            "SUN.AX",
            "AMC.AX",
            "ORG.AX",
            "TPG.AX",
            "MPL.AX",
            "IAG.AX",
            "ALL.AX",
            "QBE.AX",
            "APA.AX",
            "NST.AX",
            "STO.AX",
            "CPU.AX",
            "TCL.AX",
            "JHX.AX",
            "SEK.AX",
            "COH.AX",
            "ARB.AX",
            "LYC.AX",
            "S32.AX",
            "IGO.AX",
            "ALD.AX",
            "CWY.AX",
            "JBH.AX",
            "CAR.AX",
            "XRO.AX",
            "PME.AX",
            "SHL.AX",
            "DMP.AX",
        ],
    },
    "JPX": {
        "name": "Japão",
        "exchange": "JPX",
        "flag": "🇯🇵",
        "source": "yfinance",
        "tickers": [
            "7203.T",
            "6758.T",
            "8306.T",
            "6861.T",
            "8035.T",
            "9983.T",
            "9984.T",
            "8058.T",
            "8316.T",
            "8411.T",
            "4502.T",
            "6098.T",
            "7267.T",
            "6501.T",
            "6752.T",
            "7974.T",
            "8002.T",
            "6503.T",
            "7741.T",
            "6326.T",
            "4901.T",
            "4452.T",
            "5108.T",
            "2914.T",
            "4503.T",
            "6981.T",
            "8766.T",
            "8750.T",
            "3382.T",
            "2412.T",
            "4568.T",
            "6702.T",
            "6954.T",
            "7751.T",
            "8053.T",
            "8031.T",
            "9020.T",
            "9022.T",
            "4063.T",
            "6367.T",
            "6504.T",
            "6988.T",
            "3436.T",
            "4689.T",
            "6952.T",
        ],
    },
    "TSX": {
        "name": "Canadá",
        "exchange": "TSX",
        "flag": "🇨🇦",
        "source": "yfinance",
        "tickers": [
            "RY.TO",
            "TD.TO",
            "SHOP.TO",
            "CNQ.TO",
            "BNS.TO",
            "BAM.TO",
            "ENB.TO",
            "CNR.TO",
            "BCE.TO",
            "TRP.TO",
            "MFC.TO",
            "SU.TO",
            "BMO.TO",
            "ATD.TO",
            "NA.TO",
            "AQN.TO",
            "NTR.TO",
            "IFC.TO",
            "BIP-UN.TO",
            "BAMR.TO",
            "QSR.TO",
            "FTS.TO",
            "EMP-A.TO",
            "L.TO",
            "POW.TO",
            "BTE.TO",
            "CAR-UN.TO",
            "FNV.TO",
            "PPL.TO",
            "IMO.TO",
            "WCN.TO",
            "CP.TO",
            "TRI.TO",
            "TFII.TO",
            "BN.TO",
            "CM.TO",
            "GWO.TO",
            "ERF.TO",
            "SLF.TO",
            "MG.TO",
            "GIB-A.TO",
            "CPG.TO",
            "WN.TO",
            "CVE.TO",
            "TECK-B.TO",
        ],
    },
    "EURONEXT": {
        "name": "Euronext",
        "exchange": "EURONEXT",
        "flag": "🇪🇺",
        "source": "yfinance",
        "tickers": [
            "MC.PA",
            "OR.PA",
            "RMS.PA",
            "AI.PA",
            "BN.PA",
            "AIR.PA",
            "SU.PA",
            "SGO.PA",
            "HO.PA",
            "GLE.PA",
            "ACA.PA",
            "SAN.PA",
            "DG.PA",
            "VIV.PA",
            "EL.PA",
            "KER.PA",
            "CAP.PA",
            "ALO.PA",
            "BNP.PA",
            "ORA.PA",
            "ENGI.PA",
            "STLA.PA",
            "RI.PA",
            "CS.PA",
            "ATO.PA",
            "ASML.AS",
            "AD.AS",
            "UNA.AS",
            "PHIA.AS",
            "AKZA.AS",
            "RAND.AS",
            "NN.AS",
            "INGA.AS",
            "HEIA.AS",
            "ABI.BR",
            "KBC.BR",
            "SOLB.BR",
            "UCB.BR",
            "GALP.LS",
            "EDP.LS",
            "STM.PA",
            "PUB.PA",
            "FR.PA",
            "WLN.PA",
            "ILIAD.PA",
        ],
    },
    "LSE": {
        "name": "Reino Unido",
        "exchange": "LSE",
        "flag": "🇬🇧",
        "source": "yfinance",
        "tickers": [
            "AZN.L",
            "HSBA.L",
            "SHEL.L",
            "ULVR.L",
            "BP.L",
            "GSK.L",
            "RIO.L",
            "BATS.L",
            "LLOY.L",
            "BARC.L",
            "LSEG.L",
            "REL.L",
            "GLEN.L",
            "NG.L",
            "IMB.L",
            "AHT.L",
            "BT-A.L",
            "BA.L",
            "SSE.L",
            "CPG.L",
            "FLTR.L",
            "DGE.L",
            "VOD.L",
            "SMT.L",
            "PRU.L",
            "HLMA.L",
            "CCEP.L",
            "CKI.L",
            "STAN.L",
            "ANTO.L",
            "LGEN.L",
            "EXPN.L",
            "IAG.L",
            "IHG.L",
            "AV.L",
            "CRH.L",
            "PSON.L",
            "FERG.L",
            "SBRY.L",
            "AUTO.L",
            "JDW.L",
            "WEIR.L",
            "SN.L",
            "BDEV.L",
            "TSCO.L",
        ],
    },
    "SSE": {
        "name": "China",
        "exchange": "SSE",
        "flag": "🇨🇳",
        "source": "yfinance",
        "tickers": [
            "600519.SS",
            "601318.SS",
            "601166.SS",
            "601288.SS",
            "601939.SS",
            "601988.SS",
            "600028.SS",
            "600030.SS",
            "600036.SS",
            "600276.SS",
            "600837.SS",
            "601398.SS",
            "601857.SS",
            "600000.SS",
            "600104.SS",
            "600048.SS",
            "600585.SS",
            "600703.SS",
            "600887.SS",
            "600900.SS",
            "600919.SS",
            "601088.SS",
            "601225.SS",
            "601668.SS",
            "601669.SS",
            "601688.SS",
            "601766.SS",
            "601888.SS",
            "601899.SS",
            "603160.SS",
            "603288.SS",
            "603259.SS",
            "603501.SS",
            "688981.SS",
            "688012.SS",
            "688036.SS",
            "601012.SS",
            "600660.SS",
            "600016.SS",
            "600188.SS",
            "600362.SS",
            "601187.SS",
            "600050.SS",
            "600111.SS",
            "600845.SS",
        ],
    },
    "HKEX": {
        "name": "Hong Kong",
        "exchange": "HKEX",
        "flag": "🇭🇰",
        "source": "yfinance",
        "tickers": [
            "0700.HK",
            "9988.HK",
            "3690.HK",
            "1299.HK",
            "0388.HK",
            "0939.HK",
            "1398.HK",
            "2318.HK",
            "2628.HK",
            "2388.HK",
            "0883.HK",
            "0005.HK",
            "1928.HK",
            "0960.HK",
            "0688.HK",
            "0003.HK",
            "0267.HK",
            "2007.HK",
            "0101.HK",
            "0027.HK",
            "0017.HK",
            "0002.HK",
            "0016.HK",
            "0066.HK",
            "0011.HK",
            "0308.HK",
            "1038.HK",
            "0175.HK",
            "0386.HK",
            "1898.HK",
            "0233.HK",
            "0192.HK",
            "0181.HK",
            "0992.HK",
            "0762.HK",
            "2020.HK",
            "0669.HK",
            "2688.HK",
            "2015.HK",
            "9999.HK",
            "3692.HK",
            "0981.HK",
            "1093.HK",
            "1109.HK",
            "0823.HK",
        ],
    },
    "KRX": {
        "name": "Coreia do Sul",
        "exchange": "KRX",
        "flag": "🇰🇷",
        "source": "yfinance",
        "tickers": [
            "005930.KS",
            "000660.KS",
            "035420.KS",
            "005380.KS",
            "051910.KS",
            "068270.KS",
            "006400.KS",
            "028260.KS",
            "012330.KS",
            "003550.KS",
            "055550.KS",
            "034730.KS",
            "017670.KS",
            "018260.KS",
            "032830.KS",
            "015760.KS",
            "090430.KS",
            "000270.KS",
            "000810.KS",
            "011170.KS",
            "051900.KS",
            "329180.KS",
            "096770.KS",
            "035900.KS",
            "086790.KS",
            "030200.KS",
            "161390.KS",
            "097950.KS",
            "034020.KS",
            "066570.KS",
            "024110.KS",
            "271560.KS",
            "105560.KS",
            "316140.KS",
            "003670.KS",
            "032640.KS",
            "009150.KS",
            "271940.KS",
            "078930.KS",
            "091990.KS",
            "010950.KS",
            "180640.KS",
            "000720.KS",
            "251270.KS",
            "138040.KS",
        ],
    },
    "B3": {
        "name": "Brasil",
        "exchange": "B3",
        "flag": "🇧🇷",
        "source": "b3_local",
    },
}


@dataclass
class CompanyRecord:
    symbol: str
    short_name: Optional[str]
    market_cap: Optional[float]
    p_l: Optional[float]
    net_margin: Optional[float]
    roe: Optional[float]
    currency: Optional[str]


def _cache_file(symbol: str) -> Path:
    safe = symbol.replace(".", "_").upper()
    return CACHE_DIR / f"{safe}.json"


def _load_cache(symbol: str) -> Optional[dict]:
    path = _cache_file(symbol)
    if not path.exists():
        return None
    age = time.time() - path.stat().st_mtime
    if age > CACHE_TTL:
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def _save_cache(symbol: str, payload: dict) -> None:
    _cache_file(symbol).write_text(json.dumps(payload))


def _to_float(value: Optional[float]) -> Optional[float]:
    if value in (None, "", 0):
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(num):
        return None
    return num


def fetch_info(symbol: str) -> Optional[CompanyRecord]:
    cached = _load_cache(symbol)
    if cached:
        return CompanyRecord(**cached)

    ticker = yf.Ticker(symbol, session=SESSION)
    info = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            info = ticker.get_info()
        except Exception as exc:  # noqa: BLE001
            message = str(exc)
            rate_limited = any(
                token in message
                for token in (
                    "429",
                    "Too Many Requests",
                    "Expecting value",
                )
            )
            if rate_limited and attempt < MAX_RETRIES:
                wait_time = RETRY_BACKOFF * attempt
                logger.warning(
                    "Rate limit/erro transitório ao buscar %s (tentativa %s/%s). "
                    "Aguardando %ss.",
                    symbol,
                    attempt,
                    MAX_RETRIES,
                    wait_time,
                )
                time.sleep(wait_time)
                continue

            logger.warning("Falha ao buscar %s: %s", symbol, exc)
            return None

        if info:
            break

    if not info:
        logger.debug("Sem dados para %s após %s tentativas", symbol, MAX_RETRIES)
        return None

    payload = {
        "symbol": symbol,
        "short_name": info.get("shortName"),
        "market_cap": _to_float(info.get("marketCap")),
        "p_l": _to_float(info.get("trailingPE") or info.get("forwardPE")),
        "net_margin": _to_float(info.get("profitMargins")),
        "roe": _to_float(info.get("returnOnEquity") or info.get("returnOnEquityTTM")),
        "currency": info.get("currency"),
    }

    _save_cache(symbol, payload)
    time.sleep(REQUEST_DELAY)
    return CompanyRecord(**payload)


def collect_yfinance_market(code: str, meta: Dict[str, object]) -> Dict[str, object]:
    tickers = meta.get("tickers", [])
    logger.info(
        "Coletando %s (%s) - %s tickers",
        meta["name"],
        code,
        len(tickers),
    )

    companies: List[CompanyRecord] = []
    for symbol in tickers:
        record = fetch_info(symbol)
        if record and record.market_cap and record.market_cap > 0:
            companies.append(record)

    def avg(field: str, min_val: float, max_val: float) -> float:
        values = [
            getattr(item, field)
            for item in companies
            if getattr(item, field) is not None and min_val < getattr(item, field) < max_val
        ]
        if not values:
            return 0.0
        return float(sum(values) / len(values))

    summary = {
        "exchange": meta["exchange"],
        "country": meta["name"],
        "flag": meta["flag"],
        "companies_analyzed": len(companies),
        "total_market_cap": sum(item.market_cap for item in companies if item.market_cap),
        "p_l": round(avg("p_l", 0, 200), 2),
        "net_margin": round(avg("net_margin", -1, 1), 4),
        "avg_roe": round(avg("roe", -1, 1), 4),
    }

    logger.info(
        "✓ %s: P/L %.2f | Margem %.2f%% | ROE %.2f%% | %s empresas",
        summary["country"],
        summary["p_l"],
        summary["net_margin"] * 100,
        summary["avg_roe"] * 100,
        summary["companies_analyzed"],
    )

    detailed_companies = [
        {
            "symbol": item.symbol,
            "name": item.short_name,
            "market_cap": item.market_cap,
            "p_l": item.p_l,
            "net_margin": item.net_margin,
            "roe": item.roe,
            "currency": item.currency,
        }
        for item in companies
    ]

    return {
        "code": code,
        "summary": summary,
        "companies": detailed_companies,
    }


def collect_b3_market(code: str, meta: Dict[str, object]) -> Dict[str, object]:
    dataset_path = ROOT_DIR / "public/data/b3_stocks.json"
    if not dataset_path.exists():
        logger.error("Arquivo %s não encontrado; não foi possível gerar dados da B3.", dataset_path)
        return {
            "code": code,
            "summary": {
                "exchange": meta["exchange"],
                "country": meta["name"],
                "flag": meta["flag"],
                "companies_analyzed": 0,
                "total_market_cap": 0.0,
                "p_l": 0.0,
                "net_margin": 0.0,
                "avg_roe": 0.0,
            },
            "companies": [],
        }

    try:
        payload = json.loads(dataset_path.read_text())
    except json.JSONDecodeError as exc:
        logger.error("Erro ao carregar JSON da B3 (%s): %s", dataset_path, exc)
        return {
            "code": code,
            "summary": {
                "exchange": meta["exchange"],
                "country": meta["name"],
                "flag": meta["flag"],
                "companies_analyzed": 0,
                "total_market_cap": 0.0,
                "p_l": 0.0,
                "net_margin": 0.0,
                "avg_roe": 0.0,
            },
            "companies": [],
        }

    assets = payload.get("data", [])
    filtered = [
        asset
        for asset in assets
        if isinstance(asset, dict)
        and isinstance(asset.get("market_cap"), (int, float))
        and asset["market_cap"] > 0
    ]
    filtered.sort(key=lambda item: item.get("market_cap", 0), reverse=True)
    top_assets = filtered[:50]

    def avg(field: str, min_val: float, max_val: float) -> float:
        values: List[float] = []
        for asset in top_assets:
            value = asset.get(field)
            if isinstance(value, (int, float)) and min_val < float(value) < max_val:
                values.append(float(value))
        if not values:
            return 0.0
        return float(sum(values) / len(values))

    total_market_cap = float(sum(asset.get("market_cap", 0.0) for asset in top_assets))

    summary = {
        "exchange": meta["exchange"],
        "country": meta["name"],
        "flag": meta["flag"],
        "companies_analyzed": len(top_assets),
        "total_market_cap": total_market_cap,
        "p_l": round(avg("p_l", 0, 200), 2),
        "net_margin": round(avg("net_margin", -1, 1), 4),
        "avg_roe": round(avg("roe", -1, 1), 4),
    }

    logger.info(
        "✓ %s: P/L %.2f | Margem %.2f%% | ROE %.2f%% | %s empresas",
        summary["country"],
        summary["p_l"],
        summary["net_margin"] * 100,
        summary["avg_roe"] * 100,
        summary["companies_analyzed"],
    )

    companies = [
        {
            "symbol": asset.get("ticker"),
            "name": asset.get("sector"),
            "market_cap": asset.get("market_cap"),
            "p_l": asset.get("p_l"),
            "net_margin": asset.get("net_margin"),
            "roe": asset.get("roe"),
            "currency": "BRL",
        }
        for asset in top_assets
    ]

    return {
        "code": code,
        "summary": summary,
        "companies": companies,
    }


def collect_market(code: str, meta: Dict[str, object]) -> Dict[str, object]:
    source = meta.get("source", "yfinance")
    if source == "b3_local":
        return collect_b3_market(code, meta)
    return collect_yfinance_market(code, meta)


def export(results: List[Dict[str, object]]) -> None:
    exporter = Exporter(output_dir="public/data")

    comparison = [
        {
            "exchange": item["summary"]["exchange"],
            "country": item["summary"]["country"],
            "flag": item["summary"]["flag"],
            "p_l": item["summary"]["p_l"],
            "net_margin": item["summary"]["net_margin"],
        }
        for item in results
    ]

    detailed = {
        item["code"]: {
            **item["summary"],
            "companies": item["companies"],
        }
        for item in results
    }

    exporter.export_json(comparison, "world_comparison.json")
    exporter.export_json(detailed, "world_markets.json")


def collect() -> None:
    results: List[Dict[str, object]] = []
    for code, meta in GLOBAL_MARKETS.items():
        results.append(collect_market(code, meta))
    export(results)
    logger.info("Arquivos atualizados em public/data/world_comparison.json e world_markets.json")


if __name__ == "__main__":
    collect()
