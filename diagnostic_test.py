"""
Script de Diagnóstico: Auditoria da Lógica de Simulação

Objetivo: Testar com critérios SUPER SIMPLES e logging detalhado
para identificar exatamente onde a lógica está quebrando.
"""

import logging
from datetime import datetime
from typing import Iterable

import pandas as pd

from backtest.engine import BacktestEngine
from backtest.data_provider import DataProvider
from backtest.domain import (
    StrategyConfigRequest,
    ReviewPortfolioItem,
    CriteriaGroup,
    CriteriaItem,
)

# Setup Logging VERBOSE
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("DiagnosticTest")

CRITICAL_TICKERS = ["PETR4", "VALE3", "ITUB4", "BBDC4", "WEGE3"]
DIAGNOSTIC_DATE = pd.Timestamp("2023-01-15")


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80 + "\n")


def _print_data_quality(report: dict) -> None:
    _print_header("AUDITORIA: COBERTURA DE DADOS")
    print(f"- Tickers com fundamentalistas: {report['total_financial_tickers']}")
    print(f"- Tickers com histórico de preços: {report['total_price_tickers']}")
    print(
        f"- Tickers sem histórico carregado (financials presentes): "
        f"{len(report['tickers_without_prices'])}"
    )
    print(
        f"- Tickers sem financials no JSON: "
        f"{len(report['tickers_without_financials'])}"
    )

    def _format_issue(issue_map: dict, label: str, limit: int = 5) -> None:
        if not issue_map:
            return
        print(f"\n{label}:")
        for indicator, tickers in sorted(
            issue_map.items(), key=lambda item: len(item[1]), reverse=True
        ):
            if not tickers:
                continue
            sample = ", ".join(tickers[:limit])
            print(f"  - {indicator}: {len(tickers)} (ex.: {sample})")

    _format_issue(report.get("missing", {}), "Indicadores ausentes")
    _format_issue(report.get("zero", {}), "Indicadores zerados")


def _inspect_tickers(data_provider: DataProvider, tickers: Iterable[str]) -> None:
    print("\n📊 TESTE MANUAL DE CRITÉRIOS")
    print("-" * 80)

    if not tickers:
        print("Nenhum ticker informado para inspeção.")
        return

    for ticker in tickers:
        print(f"\n🔍 {ticker}:")

        if ticker not in data_provider.prices_data:
            print("   ❌ Sem histórico de preços carregado no price_history.json")
            continue

        price_row = data_provider.get_latest_price_row(ticker, DIAGNOSTIC_DATE)
        if price_row is None:
            print(f"   ❌ Sem preço disponível até {DIAGNOSTIC_DATE.date()}")
        else:
            price = float(price_row["close"])
            price_date = price_row.name
            print(f"   ✅ Preço: R$ {price:.2f} (Data-base: {price_date.date()})")

        fin_df = data_provider.get_financials_data(ticker)
        if fin_df.empty:
            print("   ❌ Nenhum fundamentalista carregado")
            continue

        fin_row = data_provider.get_latest_financials_row(ticker, DIAGNOSTIC_DATE)
        if fin_row is None:
            latest_date = fin_df.index.max()
            print(
                f"   ⚠️ Sem fundamentalista até {DIAGNOSTIC_DATE.date()} "
                f"(último disponível: {latest_date.date() if pd.notna(latest_date) else 'n/a'})"
            )
            continue

        p_l = fin_row.get("p_l")
        roe = fin_row.get("roe")
        fin_date = fin_row.name
        print(f"   ✅ Fundamentalista carregado ({fin_date.date()})")
        print(f"      P/L: {p_l}")
        print(f"      ROE: {roe if roe is None else f'{roe*100:.2f}%'}")

        if p_l is not None and p_l < 15:
            print("   🎯 PASSA NO CRITÉRIO (P/L < 15)")
        else:
            print("   🚫 NÃO PASSA (P/L >= 15 ou ausente)")


def run_diagnostic():
    _print_header("TESTE DIAGNÓSTICO: Critério Simples de Entrada")

    config = StrategyConfigRequest(
        initial_capital=100_000,
        start_date="2023-01-01",
        end_date="2023-06-30",
        benchmark="IBOV",
        max_assets=5,
        min_liquidity=100_000,  # Baixo para garantir candidatos
        forced_assets=[],
        blacklisted_assets=[],
        entry_logic="AND",
        entry_criteria=[
            CriteriaGroup(
                logic="AND",
                connectionToNext=None,
                items=[CriteriaItem(indicator="p_l", operator="<", value=15)],
            )
        ],
        entry_score_weights="balanced",
        exit_mode="fixed",  # Sem saída automática
        exit_criteria=[],
        stop_loss=None,
        take_profit=None,
        rebalance_period="monthly",
        contribution_amount=0,
        contribution_frequency="none",
        initial_portfolio=[],
    )

    data_provider = DataProvider()
    data_provider.load_data()
    report = data_provider.get_data_quality_report()

    _print_data_quality(report)
    _inspect_tickers(data_provider, CRITICAL_TICKERS)

    if not data_provider.assets_list:
        print("\n⚠️ Universo vazio – impossível rodar a simulação.")
        return

    print("\n" + "=" * 80)
    print("RODANDO SIMULAÇÃO OFICIAL")
    print("=" * 80 + "\n")

    engine = BacktestEngine(data_provider)
    try:
        result = engine.run(config)
    except Exception as exc:
        print(f"❌ Falha durante a simulação: {exc}")
        raise

    _print_header("RESULTADOS")
    print(f"Capital Final: R$ {result.final_capital:,.2f}")
    print(f"Total Investido: R$ {result.total_invested:,.2f}")
    print(f"Retorno: {result.total_return * 100:.2f}%")
    print(f"Total de Trades: {result.total_trades}")
    print(f"Holdings Finais: {len(result.final_holdings)}")

    if result.total_trades == 0:
        print("\n⚠️ ZERO TRADES! Verifique os logs para identificar os bloqueios.")
    else:
        print(f"\n✅ {result.total_trades} trades executados")
        print("\nPrimeiros 10 trades:")
        for i, trade in enumerate(result.trade_log[:10]):
            print(
                f"  {i + 1}. {trade.date.strftime('%Y-%m-%d')} - "
                f"{trade.action} {trade.quantity} {trade.ticker} "
                f"@ R$ {trade.price:.2f}"
            )

    if result.final_holdings:
        print("\nHoldings Finais:")
        for holding in result.final_holdings:
            print(
                f"  - {holding['ticker']}: {holding['quantity']} "
                f"@ R$ {holding['price']:.2f}"
            )


if __name__ == "__main__":
    run_diagnostic()
