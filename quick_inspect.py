"""
Fase 0: Inspeção RÁPIDA usando DataProvider

Objetivo: fornecer um panorama da cobertura de dados e inspecionar uma amostra
de tickers críticos.
"""

from typing import Iterable

from backtest.data_provider import DataProvider
import pandas as pd

DEFAULT_SAMPLE = 10
INSPECTION_DATE = pd.Timestamp("2023-01-15")


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80 + "\n")


def _print_quality_summary(report: dict) -> None:
    print(f"- Tickers com fundamentalistas: {report['total_financial_tickers']}")
    print(f"- Tickers com histórico de preços: {report['total_price_tickers']}")
    print(
        f"- Sem histórico de preços (mas com financials): "
        f"{len(report['tickers_without_prices'])}"
    )
    print(
        f"- Sem financials no JSON (mas com preços): "
        f"{len(report['tickers_without_financials'])}"
    )

    def _emit(issue_map: dict, label: str, limit: int = 5) -> None:
        if not issue_map:
            return
        print(f"\n{label}:")
        for indicator, tickers in sorted(
            issue_map.items(), key=lambda kv: len(kv[1]), reverse=True
        ):
            if not tickers:
                continue
            sample = ", ".join(tickers[:limit])
            print(f"  - {indicator}: {len(tickers)} (ex.: {sample})")

    _emit(report.get("missing", {}), "Indicadores ausentes")
    _emit(report.get("zero", {}), "Indicadores com valor zero")


def _inspect_sample(data_provider: DataProvider, tickers: Iterable[str]) -> None:
    for ticker in tickers:
        print(f"🔍 {ticker}:")

        if ticker not in data_provider.prices_data:
            print("   ❌ Sem histórico de preços carregado.")
        else:
            price_row = data_provider.get_latest_price_row(ticker, INSPECTION_DATE)
            if price_row is None:
                print(
                    f"   ⚠️ Sem preço disponível até {INSPECTION_DATE.date()}. "
                    "Verificar sincronização de preços."
                )
            else:
                price = float(price_row["close"])
                price_date = price_row.name
                print(
                    f"   ✅ Preço: R$ {price:.2f} "
                    f"(mais recente: {price_date.date()})"
                )

        fin_df = data_provider.get_financials_data(ticker)
        if fin_df.empty:
            print("   ❌ Nenhum fundamentalista disponível.")
            print()
            continue

        fin_row = data_provider.get_latest_financials_row(ticker, INSPECTION_DATE)
        if fin_row is None:
            latest_date = fin_df.index.max()
            print(
                f"   ⚠️ Sem fundamentalista até {INSPECTION_DATE.date()} "
                f"(último registro: {latest_date.date()})"
            )
            print()
            continue

        p_l = fin_row.get("p_l")
        roe = fin_row.get("roe")
        fin_date = fin_row.name.date()
        p_l_marker = "⚠️" if p_l is None else ("⚠️" if p_l == 0 else "✅")
        roe_marker = "⚠️" if roe is None else ("⚠️" if roe == 0 else "✅")

        print(f"   ✅ Fundamentalista carregado ({fin_date})")
        print(f"   {p_l_marker} P/L: {p_l}")
        print(
            f"   {roe_marker} ROE: "
            f"{'n/a' if roe is None else f'{roe*100:.2f}%'}"
        )
        print()


def quick_inspect():
    _print_header("📊 INSPEÇÃO RÁPIDA DE DADOS")

    dp = DataProvider()
    dp.load_data()
    report = dp.get_data_quality_report()

    print(f"Total de tickers no universo (com preços): {len(dp.assets_list)}")
    _print_quality_summary(report)

    if not dp.assets_list:
        print("\n⚠️ Universo vazio – rode o DataPipeline antes da inspeção.")
        return

    sample_size = min(DEFAULT_SAMPLE, len(dp.assets_list))
    sample_tickers = dp.assets_list[:sample_size]

    print(f"\nAmostra avaliada: {sample_size} tickers")
    print("-" * 80 + "\n")
    _inspect_sample(dp, sample_tickers)


if __name__ == "__main__":
    quick_inspect()
