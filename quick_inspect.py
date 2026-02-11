"""
Fase 0: Inspeção RÁPIDA usando DataProvider

Objetivo: Sample de 20 tickers para identificar problemas de qualidade
"""

from backtest.data_provider import DataProvider
import pandas as pd

def quick_inspect():
    print("\n" + "="*80)
    print("📊 INSPEÇÃO RÁPIDA DE DADOS (Sample)")
    print("="*80 + "\n")
    
    dp = DataProvider()
    dp.load_data()
    
    print(f"Total de tickers no universo: {len(dp.assets_list)}\n")
    
    # Sample de 20 tickers
    sample_tickers = dp.assets_list[:20]
    
    print(f"Testando {len(sample_tickers)} tickers:\n")
    
    test_date = pd.to_datetime("2023-01-15")
    
    issues = {
        'p_l_zero': [],
        'p_l_null': [],
        'roe_zero': [],
        'roe_null': [],
        'no_price': [],
        'no_financials': []
    }
    
    for ticker in sample_tickers:
        print(f"🔍 {ticker}:")
        
        # Test price
        price_row = dp.get_latest_price_row(ticker, test_date)
        if price_row is None:
            print(f"   ❌ SEM PREÇO")
            issues['no_price'].append(ticker)
            continue
        else:
            price = float(price_row['close'])
            print(f"   ✅ Preço: R$ {price:.2f}")
        
        # Test financials
        fin_row = dp.get_latest_financials_row(ticker, test_date)
        if fin_row is None:
            print(f"   ❌ SEM FUNDAMENTALISTA")
            issues['no_financials'].append(ticker)
            continue
        
        # Check P/L
        p_l = fin_row.get('p_l')
        if p_l is None:
            print(f"   ⚠️  P/L: NULL")
            issues['p_l_null'].append(ticker)
        elif p_l == 0:
            print(f"   🚨 P/L: ZERO (dado inválido)")
            issues['p_l_zero'].append(ticker)
        else:
            print(f"   ✅ P/L: {p_l:.2f}")
        
        # Check ROE
        roe = fin_row.get('roe')
        if roe is None:
            print(f"   ⚠️  ROE: NULL")
            issues['roe_null'].append(ticker)
        elif roe == 0:
            print(f"   🚨 ROE: ZERO (dado inválido)")
            issues['roe_zero'].append(ticker)
        else:
            print(f"   ✅ ROE: {roe*100:.2f}%")
        
        print()
    
    # Summary
    print("\n" + "="*80)
    print("📋 RESUMO DE PROBLEMAS (Sample de 20 tickers)")
    print("="*80 + "\n")
    
    total_with_issues = 0
    for issue_type, tickers in issues.items():
        count = len(tickers)
        if count > 0:
            total_with_issues += count
            pct = (count / len(sample_tickers)) * 100
            marker = "🚨" if "zero" in issue_type else "⚠️ "
            print(f"{marker} {issue_type}: {count} tickers ({pct:.0f}%)")
            print(f"   → {', '.join(tickers)}")
    
    print(f"\n📊 {total_with_issues} problemas encontrados em {len(sample_tickers)} tickers testados")
    print(f"   Taxa de problemas: {(total_with_issues/len(sample_tickers))*100:.0f}%\n")
    
    # Recommendations
    print("🔧 AÇÃO NECESSÁRIA:")
    if issues['p_l_zero'] or issues['roe_zero']:
        print("   ❌ CRÍTICO: Dados com zero impedem critérios de funcionar")
        print("   → Adicionar filtros de qualidade no DataProvider.load_data()")
        print("   → Excluir tickers com P/L=0 ou ROE=0 do universo")
    print()

if __name__ == "__main__":
    quick_inspect()
