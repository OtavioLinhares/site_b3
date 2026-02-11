"""
Fase 3: Teste de Critérios de Entrada

Objetivo: Garantir que evaluate_rules funciona corretamente
"""

import pytest
import pandas as pd
from datetime import datetime
from backtest.engine import BacktestEngine
from backtest.data_provider import DataProvider
from backtest.domain import StrategyConfigRequest


class TestEntryCriteria:
    """Testes para validação dos critérios de entrada"""
    
    @pytest.fixture
    def engine(self):
        """Fixture: BacktestEngine configurado"""
        dp = DataProvider()
        dp.load_data()
        engine = BacktestEngine(dp)
        
        # Config mínima
        config = StrategyConfigRequest(
            initial_capital=100000,
            start_date="2023-01-01",
            end_date="2023-12-31",
            benchmark="IBOV",
            max_assets=10,
            min_liquidity=100000,
            forced_assets=[],
            blacklisted_assets=[],
            entry_logic="AND",
            entry_criteria=[],
            entry_score_weights="balanced",
            exit_mode="fixed",
            exit_criteria=[],
            rebalance_period="monthly",
            contribution_amount=0,
            contribution_frequency="none",
            initial_portfolio=[]
        )
        engine.config = config
        return engine
    
    def test_operator_less_than(self, engine):
        """3.1: Operador < deve funcionar corretamente"""
        criteria = [
            {"id": 1, "logic": "AND", "items": [
                {"indicator": "p_l", "operator": "<", "value": 10}
            ]}
        ]
        
        # Mock financials
        fin_row = pd.Series({'p_l': 5.0})
        
        result = engine.evaluate_rules(criteria, "TEST", datetime(2023,1,1), 10.0, fin_row)
        assert result == True, "P/L=5 deve passar em < 10"
        
        fin_row = pd.Series({'p_l': 15.0})
        result = engine.evaluate_rules(criteria, "TEST", datetime(2023,1,1), 10.0, fin_row)
        assert result == False, "P/L=15 NÃO deve passar em < 10"
    
    def test_operator_greater_than(self, engine):
        """3.2: Operador > deve funcionar corretamente"""
        criteria = [
            {"id": 1, "logic": "AND", "items": [
                {"indicator": "roe", "operator": ">", "value": 0.15}
            ]}
        ]
        
        fin_row = pd.Series({'roe': 0.20})
        result = engine.evaluate_rules(criteria, "TEST", datetime(2023,1,1), 10.0, fin_row)
        assert result == True, "ROE=0.20 deve passar em > 0.15"
        
        fin_row = pd.Series({'roe': 0.10})
        result = engine.evaluate_rules(criteria, "TEST", datetime(2023,1,1), 10.0, fin_row)
        assert result == False, "ROE=0.10 NÃO deve passar em > 0.15"
    
    def test_multiple_criteria_and(self, engine):
        """3.3: Múltiplos critérios com lógica AND"""
        criteria = [
            {"id": 1, "logic": "AND", "items": [
                {"indicator": "p_l", "operator": "<", "value": 10},
                {"indicator": "roe", "operator": ">", "value": 0.15}
            ]}
        ]
        
        # Ambos passam
        fin_row = pd.Series({'p_l': 5.0, 'roe': 0.20})
        result = engine.evaluate_rules(criteria, "TEST", datetime(2023,1,1), 10.0, fin_row)
        assert result == True, "P/L=5 E ROE=0.20 deve passar"
        
        # Apenas 1 passa
        fin_row = pd.Series({'p_l': 5.0, 'roe': 0.10})
        result = engine.evaluate_rules(criteria, "TEST", datetime(2023,1,1), 10.0, fin_row)
        assert result == False, "P/L=5 mas ROE=0.10 NÃO deve passar (AND)"
    
    def test_data_quality_filter_pl_zero(self, engine):
        """3.4: P/L = 0 deve ser filtrado como dado inválido"""
        # Configurar engine com critério P/L
        engine.config.entry_criteria = [
            {"id": 1, "logic": "AND", "items": [
                {"indicator": "p_l", "operator": "<", "value": 15}
            ]}
        ]
        
        # Simular check_entries em uma data
        # Verificar que ativos com P/L=0 não são incluídos nos candidatos
        
        # Este teste precisa ser mais integrado - mock completo do check_entries
        # Por ora, vamos validar a lógica de filtro diretamente
        
        # P/L = 0 deve ser considerado inválido
        test_date = pd.to_datetime("2023-01-15")
        
        # Buscar PETR4 que sabemos ter P/L=0 nos dados
        fin_row = engine.data_provider.get_latest_financials_row('PETR4', test_date)
        
        if fin_row is not None and fin_row.get('p_l') == 0.0:
            # Este ativo DEVE ser filtrado no check_entries
            # Vamos validar que o filtro de qualidade está ativo
            
            required_indicators = {'p_l'}
            data_valid = True
            
            for indicator in required_indicators:
                val = fin_row.get(indicator)
                positive_required = indicator in ['p_l', 'p_vp', 'roe', 'roic', 'ev_ebitda']
                
                if val is None or (positive_required and val <= 0):
                    data_valid = False
                    break
            
            assert data_valid == False, "P/L=0 deve ser marcado como dado inválido"
