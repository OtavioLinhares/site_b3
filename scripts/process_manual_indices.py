#!/usr/bin/env python3
"""
Processa planilhas manuais de índices globais (Investing.com) e gera:
1. CSV normalizado com as 40–50 maiores companhias do índice.
2. Resumo com métricas agregadas (P/L ponderado e margem líquida estimada).
3. JSONs finais consumidos pelo front (`world_comparison.json`, `world_markets.json`).

Uso:
    python3 scripts/process_manual_indices.py
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
PUBLIC_DATA_DIR = ROOT_DIR / "public" / "data"

SUFFIXES = {
    "K": 1_000,
    "M": 1_000_000,
    "B": 1_000_000_000,
    "T": 1_000_000_000_000,
}


@dataclass(frozen=True)
class IndexConfig:
    slug: str
    name: str
    country: str
    flag: str
    raw_filename: str
    top_label: int  # usado no nome do arquivo (_top{label})


INDEX_CONFIGS: List[IndexConfig] = [
    IndexConfig("sp500", "S&P 500", "Estados Unidos", "🇺🇸", "sp500_index.csv", 50),
    IndexConfig("nasdaq100", "Nasdaq 100", "Estados Unidos", "🇺🇸", "nasdaq100_index.csv", 50),
    IndexConfig("ftse100", "FTSE 100", "Reino Unido", "🇬🇧", "ftse100_index.csv", 50),
    IndexConfig("dax", "DAX 40", "Alemanha", "🇩🇪", "dax_index.csv", 50),
    IndexConfig("cac40", "CAC 40", "França", "🇫🇷", "cac40_index.csv", 40),
    IndexConfig("ibex35", "IBEX 35", "Espanha", "🇪🇸", "ibex35_index.csv", 35),
    IndexConfig("ftsemib", "FTSE MIB", "Itália", "🇮🇹", "ftsemib_index.csv", 40),
    IndexConfig("stoxx50", "Euro Stoxx 50", "Zona do Euro", "🇪🇺", "stoxx50_index.csv", 50),
    IndexConfig("nikkei225", "Nikkei 225", "Japão", "🇯🇵", "nikkei225_index.csv", 50),
    IndexConfig("nifty50", "Nifty 50", "Índia", "🇮🇳", "nifty50_index.csv", 50),
    IndexConfig("shanghai", "Shanghai Composite", "China", "🇨🇳", "shanghai_index.csv", 50),
    IndexConfig("tadawul", "Tadawul All Share", "Arábia Saudita", "🇸🇦", "tadawul_index.csv", 50),
    IndexConfig("jse_top40", "JSE Top 40", "África do Sul", "🇿🇦", "jse_top40_index.csv", 40),
    IndexConfig("nse30", "NSE 30", "Nigéria", "🇳🇬", "nse30_index.csv", 30),
    IndexConfig("omxs30", "OMX Stockholm 30", "Suécia", "🇸🇪", "omxs30_index.csv", 30),
]

# Seleção final para o comparativo (12 bolsas internacionais)
ACTIVE_SLUGS = {
    "sp500",
    "nasdaq100",
    "ftse100",
    "dax",
    "cac40",
    "ftsemib",
    "ibex35",
    "nikkei225",
    "nifty50",
    "shanghai",
    "tadawul",
    "jse_top40",
}


def parse_numeric(value: object, allow_negative: bool = False) -> Optional[float]:
    """Converte strings como '808,97B' em floats. Retorna None para valores inválidos."""
    if value is None:
        return None
    if isinstance(value, (int, float, np.number)):
        return float(value)

    text = str(value).strip()
    if not text or text in {"-", "--", "N/A", "NaN"}:
        return None

    multiplier = 1.0
    suffix = text[-1].upper()
    if suffix in SUFFIXES:
        multiplier = SUFFIXES[suffix]
        text = text[:-1]

    # Remove separador de milhar e normaliza decimal
    text = text.replace(".", "").replace(",", ".")

    try:
        number = float(text)
    except ValueError:
        return None

    if not allow_negative and number <= 0:
        return None

    return number * multiplier


def compute_company_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza as colunas principais e calcula lucro estimado e margem."""
    df = df.copy()
    df["market_cap"] = df["Valor de Mercado"].apply(parse_numeric)
    df["revenue"] = df["Receita"].apply(parse_numeric)
    df["pe"] = df["Relação P/L"].apply(lambda x: parse_numeric(x, allow_negative=True))
    df["name"] = df["Nome"].astype(str).str.strip()

    df = df[df["market_cap"].notna()]
    df = df.sort_values("market_cap", ascending=False).reset_index(drop=True)

    df["earnings"] = np.where(
        (df["pe"].notna()) & (df["pe"] > 0),
        df["market_cap"] / df["pe"],
        np.nan,
    )
    df["margin"] = np.where(
        (df["earnings"].notna()) & (df["revenue"].notna()) & (df["revenue"] > 0),
        df["earnings"] / df["revenue"],
        np.nan,
    )
    return df


def safe_float(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (float, np.floating)):
        if math.isnan(float(value)):
            return None
        return float(value)
    return float(value)


def summarize_index(df_top: pd.DataFrame, config: IndexConfig) -> Tuple[Dict, List[Dict], List[Dict]]:
    """Calcula métricas agregadas e lista de exclusões."""
    excluded: List[Dict] = []

    def add_exclusion(row: pd.Series, reason: str) -> None:
        excluded.append({"name": row["name"], "reason": reason})

    filtered = df_top.copy()

    # Excluir margens suspeitas (>50% ou <-50%)
    margin_outliers = filtered["margin"].notna() & (filtered["margin"].abs() > 0.5)
    for _, row in filtered[margin_outliers].iterrows():
        add_exclusion(row, "outlier_margin")
    filtered = filtered[~margin_outliers].copy()

    # Excluir casos sem earnings ou revenue válidos
    invalid_rows = filtered[
        (filtered["earnings"].isna()) | (filtered["earnings"] <= 0) | (filtered["revenue"].isna()) | (filtered["revenue"] <= 0)
    ]
    for _, row in invalid_rows.iterrows():
        if pd.isna(row["earnings"]) or row["earnings"] <= 0:
            add_exclusion(row, "non_positive_pe")
        elif pd.isna(row["revenue"]) or row["revenue"] <= 0:
            add_exclusion(row, "missing_revenue")
    filtered = filtered.drop(index=invalid_rows.index)

    market_cap_pe = filtered["market_cap"].sum()
    earnings_total = filtered["earnings"].sum()
    weighted_pe = market_cap_pe / earnings_total if earnings_total > 0 else None

    revenue_total = filtered["revenue"].sum()
    average_margin = filtered["margin"].mean() if not filtered["margin"].empty else None

    summary = {
        "index": config.name,
        "slug": config.slug,
        "source_file": str((DATA_DIR / config.raw_filename).relative_to(ROOT_DIR)),
        "top_n": int(len(filtered)),
        "market_cap_total": safe_float(market_cap_pe) or 0.0,
        "earnings_total": safe_float(earnings_total) or 0.0,
        "revenue_total": safe_float(revenue_total) or 0.0,
        "weighted_pe": safe_float(weighted_pe),
        "weighted_net_margin": safe_float(average_margin),
        "excluded_companies": excluded,
    }

    companies = filtered[["name", "market_cap", "revenue", "pe", "earnings", "margin"]].to_dict(orient="records")
    companies = [
        {
            "name": c["name"],
            "market_cap": safe_float(c.get("market_cap")),
            "revenue": safe_float(c.get("revenue")),
            "pe": safe_float(c.get("pe")),
            "earnings": safe_float(c.get("earnings")),
            "margin": safe_float(c.get("margin")),
        }
        for c in companies
    ]

    return summary, companies, excluded


def process_index(config: IndexConfig) -> Tuple[IndexConfig, Dict, List[Dict]]:
    raw_path = DATA_DIR / config.raw_filename
    if not raw_path.exists():
        raise FileNotFoundError(f"Arquivo bruto não encontrado: {raw_path}")

    raw_df = pd.read_csv(raw_path, encoding="utf-8-sig")
    df_normalized = compute_company_metrics(raw_df)

    top_limit = min(config.top_label, len(df_normalized))
    df_top = df_normalized.head(top_limit).copy()

    summary, companies, excluded = summarize_index(df_top, config)

    clean_path = DATA_DIR / f"{config.slug}_top{config.top_label}_clean.csv"
    summary_path = DATA_DIR / f"{config.slug}_top{config.top_label}_summary.json"

    df_export = df_top[["name", "market_cap", "revenue", "pe", "earnings", "margin"]].copy()
    df_export.rename(
        columns={
            "name": "name",
            "market_cap": "market_cap",
            "revenue": "revenue",
            "pe": "pe",
            "earnings": "earnings",
            "margin": "margin",
        },
        inplace=True,
    )
    df_export.to_csv(clean_path, index=False)

    with summary_path.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False)

    return config, {"summary": summary, "companies": companies, "excluded": excluded}


def is_bdr(ticker: str) -> bool:
    return ticker.endswith(("32", "33", "34", "35", "36", "37", "38", "39"))


def is_fii(ticker: str) -> bool:
    return ticker.endswith("11")


def compute_b3_metrics() -> Dict:
    """
    Constrói o resumo da B3 a partir do dataset reconciliado
    `data/b3_ibx50_pipeline_compare.csv`, já com margens revisadas.
    """
    dataset_path = DATA_DIR / "b3_ibx50_pipeline_compare.csv"
    if not dataset_path.exists():
        raise FileNotFoundError(
            "Dataset da B3 não encontrado. Execute antes o comparativo IBX50 vs pipeline."
        )

    df = pd.read_csv(dataset_path)
    if df.empty:
        raise ValueError("Dataset da B3 está vazio.")

    df = df.sort_values("pipeline_market_cap", ascending=False).copy()

    # Remove margens irreais (>50% ou <-50%)
    high_margin_mask = df["pipeline_net_margin_recalc"].abs() > 0.5
    if high_margin_mask.any():
        df.loc[high_margin_mask, "pipeline_net_margin_recalc"] = np.nan
        df.loc[high_margin_mask, "margin_source"] = "filtered_outlier"

    df["earnings"] = np.where(
        (df["pipeline_p_l"] > 0) & df["pipeline_p_l"].notna(),
        df["pipeline_market_cap"] / df["pipeline_p_l"],
        np.nan,
    )

    total_market_cap = df["pipeline_market_cap"].sum()

    margins = df["pipeline_net_margin_recalc"].dropna()
    average_margin = margins.mean() if not margins.empty else None

    valid_pl = df[df["earnings"].notna() & (df["earnings"] > 0)]
    market_cap_pl = valid_pl["pipeline_market_cap"].sum()
    earnings_total = valid_pl["earnings"].sum()
    weighted_pe = market_cap_pl / earnings_total if earnings_total > 0 else None

    companies = []
    for _, row in df.iterrows():
        companies.append(
            {
                "ticker": row["ticker"],
                "market_cap": safe_float(row.get("pipeline_market_cap")),
                "p_l": safe_float(row.get("pipeline_p_l")),
                "net_margin": safe_float(row.get("pipeline_net_margin_recalc")),
                "margin_source": row.get("margin_source"),
            }
        )

    summary = {
        "exchange": "B3",
        "country": "Brasil",
        "flag": "🇧🇷",
        "top_n": int(len(df)),
        "market_cap_total": safe_float(total_market_cap) or 0.0,
        "earnings_total": safe_float(earnings_total) or 0.0,
        "weighted_pe": safe_float(weighted_pe),
        "weighted_net_margin": safe_float(average_margin),
        "excluded_companies": [],
        "notes": {
            "margin_source": {
                "fundamentus_calc": int((df["margin_source"] == "fundamentus_calc").sum()),
                "planilha_ibx50": int((df["margin_source"] == "planilha_ibx50").sum()),
                "filtered_outlier": int((df["margin_source"] == "filtered_outlier").sum()),
            }
        },
    }

    return {"summary": summary, "companies": companies}


def build_outputs(results: Dict[IndexConfig, Dict]) -> None:
    generated_at = datetime.now(timezone.utc).isoformat()

    b3 = compute_b3_metrics()

    world_entries: List[Dict] = []
    markets_payload: List[Dict] = []

    # B3 primeiro
    world_entries.append(
        {
            "exchange": "B3",
            "country": b3["summary"]["country"],
            "flag": b3["summary"]["flag"],
            "p_l": b3["summary"]["weighted_pe"],
            "net_margin": b3["summary"]["weighted_net_margin"],
            "market_cap_agg": b3["summary"]["market_cap_total"],
            "top_n": b3["summary"]["top_n"],
        }
    )
    markets_payload.append(
        {
            "slug": "b3",
            "name": "B3",
            "country": b3["summary"]["country"],
            "flag": b3["summary"]["flag"],
            "generated_at": generated_at,
            "top_n": b3["summary"]["top_n"],
            "metrics": {
                "market_cap_total": b3["summary"]["market_cap_total"],
                "earnings_total": b3["summary"]["earnings_total"],
                "weighted_pe": b3["summary"]["weighted_pe"],
                "weighted_net_margin": b3["summary"]["weighted_net_margin"],
            },
            "companies": b3["companies"],
            "excluded_companies": b3["summary"]["excluded_companies"],
            "notes": b3["summary"].get("notes"),
        }
    )

    for config, data in results.items():
        summary = data["summary"]

        world_entries.append(
            {
                "exchange": config.name,
                "country": config.country,
                "flag": config.flag,
                "p_l": summary["weighted_pe"],
                "net_margin": summary["weighted_net_margin"],
                "market_cap_agg": summary["market_cap_total"],
                "top_n": summary["top_n"],
            }
        )

        markets_payload.append(
            {
                "slug": config.slug,
                "name": config.name,
                "country": config.country,
                "flag": config.flag,
                "generated_at": generated_at,
                "top_n": summary["top_n"],
                "metrics": {
                    "market_cap_total": summary["market_cap_total"],
                    "earnings_total": summary["earnings_total"],
                    "revenue_total": summary["revenue_total"],
                    "weighted_pe": summary["weighted_pe"],
                    "weighted_net_margin": summary["weighted_net_margin"],
                },
                "companies": data["companies"],
                "excluded_companies": summary["excluded_companies"],
            }
        )

    world_output_path = PUBLIC_DATA_DIR / "world_comparison.json"
    with world_output_path.open("w", encoding="utf-8") as fh:
        json.dump(world_entries, fh, ensure_ascii=False, indent=4)

    markets_output_path = PUBLIC_DATA_DIR / "world_markets.json"
    with markets_output_path.open("w", encoding="utf-8") as fh:
        json.dump(
            {
                "generated_at": generated_at,
                "schema_version": "1.0",
                "markets": markets_payload,
            },
            fh,
            ensure_ascii=False,
            indent=2,
        )


def main() -> None:
    results: Dict[IndexConfig, Dict] = {}
    for config in INDEX_CONFIGS:
        if config.slug not in ACTIVE_SLUGS:
            continue
        cfg, data = process_index(config)
        results[cfg] = data
    build_outputs(results)
    print("Processamento concluído. Arquivos atualizados em data/ e public/data/.")


if __name__ == "__main__":
    main()
