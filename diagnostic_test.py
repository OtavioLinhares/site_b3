"""
Script de Diagnóstico: Auditoria da Lógica de Simulação

Objetivo: Testar com critérios SUPER SIMPLES e logging detalhado
para identificar exatamente onde a lógica está quebrando.
"""

import logging
from datetime import datetime
import pandas as pd
from backtest.engine import BacktestEngine
from backtest.data_provider import DataProvider
from backtest.domain import StrategyConfigRequest, ReviewPortfolioItem

# Setup Logging VERBOSE
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DiagnosticTest")

def run_diagnostic():
    print("\n" + "="*80)
    print("TESTE DIAGNÓSTICO: Critério Simples de Entrada")
    print("="*80 + "\n")
    
    # Critério SUPER SIMPLES: P/L < 15
    # Universo pequeno: 5 ativos
    # Período curto: 6 meses
    
    config = StrategyConfigRequest(
        initial_capital=100000,
        start_date="2023-01-01",
        end_date="2023-06-30",
        benchmark="IBOV",
        max_assets=5,
        min_liquidity=100000,  # Baixo para garantir candidatos
        forced_assets=[],
        blacklisted_assets=[],
        entry_logic="AND",
        entry_criteria=[
             {"id": 1, "logic": "AND", "connectionToNext": "AND", "items": [
                 {"indicator": "p_l", "operator": "<", "value": 15}
             ]}
        ],
        entry_score_weights="balanced",
        exit_mode="fixed",  # Sem saída automática
        exit_criteria=[],
        stop_loss=None,
        take_profit=None,
        rebalance_period="monthly",
        contribution_amount=0,
        contribution_frequency="none",
        initial_portfolio=[]
    )
    
    # Init DataProvider
    data_provider = DataProvider()
    data_provider.load_data()
    
    # Instrumentação Manual: Vamos checar alguns ativos manualmente
    print("\n📊 TESTE MANUAL DE CRITÉRIOS")
    print("-" * 80)
    
    test_tickers = ['PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'WEGE3']
    test_date = pd.to_datetime("2023-01-15")
    
    for ticker in test_tickers:
        print(f"\n🔍 {ticker}:")
        
        # 1. Tem preço?
        price_row = data_provider.get_latest_price_row(ticker, test_date)
        if price_row is None:
            print(f"   ❌ SEM PREÇO em {test_date}")
            continue
        else:
            price = float(price_row['close'])
            price_date = price_row.name
            print(f"   ✅ Preço: R$ {price:.2f} (Data: {price_date})")
        
        # 2. Tem fundamentalista?
        fin_row = data_provider.get_latest_financials_row(ticker, test_date)
        if fin_row is None:
            print(f"   ❌ SEM FUNDAMENTALISTA")
            continue
        else:
            fin_date = fin_row.name
            p_l = fin_row.get('p_l', None)
            print(f"   ✅ Fundamentalista (Data: {fin_date})")
            print(f"      P/L: {p_l}")
            
            if p_l is not None and p_l < 15:
                print(f"   🎯 PASSA NO CRITÉRIO (P/L < 15)")
            else:
                print(f"   🚫 NÃO PASSA (P/L >= 15 ou None)")
    
    print("\n" + "="*80)
    print("RODANDO SIMULAÇÃO OFICIAL")
    print("="*80 + "\n")
    
    # Run Engine
    engine = BacktestEngine(data_provider)
    result = engine.run(config)
    
    print("\n" + "="*80)
    print("RESULTADOS")
    print("="*80)
    print(f"Capital Final: R$ {result.final_capital:,.2f}")
    print(f"Total Investido: R$ {result.total_invested:,.2f}")
    print(f"Retorno: {result.total_return * 100:.2f}%")
    print(f"Total de Trades: {result.total_trades}")
    print(f"Holdings Finais: {len(result.final_holdings)}")
    
    if result.total_trades == 0:
        print("\n⚠️  ZERO TRADES! PROBLEMA CONFIRMADO")
        print("Verificando logs acima para identificar onde quebrou...")
    else:
        print(f"\n✅ {result.total_trades} trades executados")
        print("\nPrimeiros 10 trades:")
        for i, t in enumerate(result.trade_log[:10]):
            print(f"  {i+1}. {t.date.strftime('%Y-%m-%d')} - {t.action} {t.quantity} {t.ticker} @ R${t.price:.2f}")
    
    print("\nHoldings Finais:")
    for h in result.final_holdings:
        print(f"  - {h['ticker']}: {h['quantity']} @ R${h['price']:.2f}")

if __name__ == "__main__":
    run_diagnostic()
