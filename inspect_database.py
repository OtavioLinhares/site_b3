"""
Fase 0: Inspeção de Qualidade de Dados

Objetivo: Auditar data/processed/cvm_financials_history.csv e price_history.json
          para identificar dados faltantes, incoerentes ou inválidos
"""

import json
import pandas as pd
from collections import defaultdict
from pathlib import Path


class DataInspector:
    """Auditor de qualidade de dados"""
    
    def __init__(self):
        self.data_dir = Path("data/processed")
        self.financials_path = self.data_dir / "cvm_financials_history.csv"
        self.prices_path = self.data_dir / "price_history.json"
        
        self.report = {
            'financials': {},
            'prices': {},
            'summary': {}
        }
    
    def inspect_financials(self):
        """Inspeciona dados fundamentalistas"""
        print("\n" + "="*80)
        print("📊 INSPECIONANDO CVM_FINANCIALS_HISTORY.CSV")
        print("="*80 + "\n")
        
        # Ler apenas colunas necessárias
        key_cols = ['ticker', 'date', 'p_l', 'p_vp', 'roe', 'roic', 'dy', 
                    'net_margin', 'net_debt_ebitda', 'revenue_cagr_5y']
        
        print("Carregando CSV (primeiros 5000 registros para análise rápida)...")
        df = pd.read_csv(self.financials_path, usecols=lambda x: x in key_cols, 
                        parse_dates=['date'], low_memory=False, nrows=5000)
        
        print(f"Total de registros: {len(df)}")
        print(f"Colunas carregadas: {list(df.columns)}\n")
        
        # Validar colunas faltantes
        expected_cols = ['p_l', 'p_vp', 'roe', 'roic', 'dy', 'net_margin', 
                        'net_debt_ebitda', 'revenue_cagr_5y']
        missing_cols = [col for col in expected_cols if col not in df.columns]
        if missing_cols:
            print(f"⚠️  Colunas faltantes: {missing_cols}\n")
        
        # Analisar por ticker (registro mais recente)
        df['date'] = pd.to_datetime(df['date'])
        latest_df = df.sort_values('date').groupby('ticker').last().reset_index()
        
        total_tickers = len(latest_df)
        print(f"Total de tickers únicos: {total_tickers}\n")
        
        issues = defaultdict(list)
        
        for indicator in expected_cols:
            if indicator not in df.columns:
                continue
            
            # Dados faltantes (None/NaN)
            null_mask = latest_df[indicator].isnull()
            null_tickers = latest_df[null_mask]['ticker'].tolist()
            if null_tickers:
                issues[f'{indicator}_null'].extend(null_tickers)
            
            # Zero em indicadores que não deveriam ser zero
            if indicator in ['p_l', 'p_vp', 'roe', 'roic']:
                zero_mask = latest_df[indicator] == 0
                zero_tickers = latest_df[zero_mask]['ticker'].tolist()
                if zero_tickers:
                    issues[f'{indicator}_zero'].extend(zero_tickers)
            
            # Negativos em indicadores positivos
            if indicator in ['p_l', 'p_vp', 'roe', 'roic', 'dy']:
                neg_mask = latest_df[indicator] < 0
                neg_tickers = latest_df[neg_mask]['ticker'].tolist()
                if neg_tickers:
                    issues[f'{indicator}_negative'].extend(neg_tickers)
        
        # Relatório
        print("🔍 PROBLEMAS ENCONTRADOS:\n")
        
        critical_count = 0
        for issue_type in sorted(issues.keys()):
            tickers = issues[issue_type]
            count = len(tickers)
            if count > 0:
                pct = (count / total_tickers) * 100
                critical = issue_type in ['p_l_zero', 'p_l_null', 'roe_zero', 'roe_null']
                marker = "🚨" if critical else "⚠️ "
                
                print(f"{marker} {issue_type}: {count} tickers ({pct:.1f}%)")
                
                if critical:
                    critical_count += count
                    print(f"   Exemplos: {', '.join(tickers[:5])}")
        
        self.report['financials'] = {
            'total': total_tickers,
            'issues': {k: len(v) for k, v in issues.items()},
            'critical_count': critical_count,
            'critical_tickers': {
                'p_l_zero': issues.get('p_l_zero', [])[:20],
                'p_l_null': issues.get('p_l_null', [])[:20],
                'roe_zero': issues.get('roe_zero', [])[:20],
                'roe_null': issues.get('roe_null', [])[:20]
            }
        }
        
        return issues
    
    def inspect_prices(self):
        """Inspeciona histórico de preços"""
        print("\n" + "="*80)
        print("📈 INSPECIONANDO PRICE_HISTORY.JSON")
        print("="*80 + "\n")
        
        print("Carregando arquivo (pode demorar)...")
        with open(self.prices_path, 'r') as f:
            prices = json.load(f)
        
        total_tickers = len(prices)
        print(f"Total de tickers: {total_tickers}\n")
        
        issues = defaultdict(list)
        ticker_stats = {}
        
        for ticker, records in list(prices.items())[:100]:  # Sample primeiros 100
            if not records:
                issues['no_prices'].append(ticker)
                continue
            
            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Estatísticas
            ticker_stats[ticker] = {
                'count': len(df),
                'first_date': df['date'].min().strftime('%Y-%m-%d'),
                'last_date': df['date'].max().strftime('%Y-%m-%d')
            }
            
            # Problema 1: Poucos dados
            if len(df) < 100:
                issues['insufficient_data'].append(ticker)
            
            # Problema 2: Gaps grandes (>30 dias)
            df['gap'] = df['date'].diff().dt.days
            max_gap = df['gap'].max()
            
            if max_gap > 30:
                issues['large_gaps'].append(ticker)
            
            # Problema 3: Dados muito antigos
            last_date = df['date'].max()
            if last_date < pd.to_datetime("2023-01-01"):
                issues['outdated'].append(ticker)
        
        # Relatório
        print("🔍 PROBLEMAS ENCONTRADOS (Sample 100 tickers):\n")
        
        for issue_type in sorted(issues.keys()):
            tickers = issues[issue_type]
            count = len(tickers)
            if count > 0:
                print(f"⚠️  {issue_type}: {count} tickers")
                print(f"   Exemplos: {', '.join(tickers[:5])}")
        
        self.report['prices'] = {
            'total': total_tickers,
            'sampled': 100,
            'issues': {k: len(v) for k, v in issues.items()},
            'sample_stats': list(ticker_stats.items())[:10]
        }
        
        return issues
    
    def create_report(self):
        """Gera relatório final"""
        print("\n" + "="*80)
        print("📋 RELATÓRIO DE QUALIDADE DE DADOS")
        print("="*80 + "\n")
        
        fin = self.report['financials']
        prc = self.report['prices']
        
        print(f"✅ Financials: {fin['total']} tickers carregados")
        print(f"✅ Prices: {prc['total']} tickers carregados\n")
        
        print(f"🚨 PROBLEMAS CRÍTICOS (Financials):")
        print(f"   P/L inválido: {fin['issues'].get('p_l_zero', 0) + fin['issues'].get('p_l_null', 0)} tickers")
        print(f"   ROE inválido: {fin['issues'].get('roe_zero', 0) + fin['issues'].get('roe_null', 0)} tickers\n")
        
        # Salvar relatório detalhado
        report_path = "data_quality_report.json"
        with open(report_path, 'w') as f:
            json.dump(self.report, f, indent=2)
        
        print(f"💾 Relatório completo salvo em: {report_path}\n")
        
        # Recomendações
        print("🔧 AÇÕES NECESSÁRIAS:")
        print("   1. ❌ REMOVER tickers com P/L=0 do universo de simulação")
        print("   2. ❌ REMOVER tickers com ROE=0 do universo de simulação")
        print("   3. ⚠️  Considerar re-executar ETL para tickers com dados null")
        print("   4. ✅ Adicionar filtros de qualidade no DataProvider\n")


if __name__ == "__main__":
    inspector = DataInspector()
    
    # Fase 1: Inspecionar Financials
    fin_issues = inspector.inspect_financials()
    
    # Fase 2: SKIP prices (arquivo muito grande - 180MB JSON)
    print("\n⏩ Pulando inspeção de prices (arquivo 180MB)\n")
    inspector.report['prices'] = {'total': '?', 'skipped': True}
    
    # Fase 3: Relatório
    inspector.create_report()
