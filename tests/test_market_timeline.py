"""
Fase 1: Teste de Timeline & Dias de Negociação

Objetivo: Garantir que apenas dias úteis são incluídos na simulação
"""

import pytest
import pandas as pd
from datetime import datetime
from backtest.data_provider import DataProvider


class TestMarketTimeline:
    """Testes para validação do timeline de mercado"""
    
    @pytest.fixture
    def data_provider(self):
        """Fixture: DataProvider carregado"""
        dp = DataProvider()
        dp.load_data()
        return dp
    
    def test_timeline_no_weekends(self, data_provider):
        """1.1: Timeline não deve conter sábados ou domingos"""
        start = pd.to_datetime("2023-01-01")
        end = pd.to_datetime("2023-12-31")
        
        timeline = data_provider.get_market_timeline(start, end)
        
        for date in timeline:
            weekday = date.weekday()
            assert weekday < 5, f"Timeline contém fim de semana: {date} ({date.strftime('%A')})"
    
    def test_timeline_no_new_year(self, data_provider):
        """1.2: Timeline não deve conter 1º de Janeiro"""
        start = pd.to_datetime("2023-01-01")
        end = pd.to_datetime("2023-01-31")
        
        timeline = data_provider.get_market_timeline(start, end)
        
        for date in timeline:
            assert not (date.month == 1 and date.day == 1), \
                f"Timeline contém feriado (Jan 1): {date}"
    
    def test_timeline_has_prices(self, data_provider):
        """1.3: Cada dia do timeline deve ter cotações para VALE3"""
        start = pd.to_datetime("2023-01-01")
        end = pd.to_datetime("2023-06-30")
        
        timeline = data_provider.get_market_timeline(start, end)
        
        # VALE3 é muito líquida, deve ter preço todos os dias
        missing_dates = []
        for date in timeline[:10]:  # Testar primeiros 10 dias
            price_row = data_provider.get_latest_price_row('VALE3', date)
            if price_row is None:
                missing_dates.append(date)
        
        assert len(missing_dates) == 0, \
            f"Timeline contém {len(missing_dates)} dias sem cotação para VALE3: {missing_dates}"
    
    def test_timeline_order(self, data_provider):
        """1.4: Timeline deve estar em ordem cronológica"""
        start = pd.to_datetime("2023-01-01")
        end = pd.to_datetime("2023-12-31")
        
        timeline = data_provider.get_market_timeline(start, end)
        
        for i in range(len(timeline) - 1):
            assert timeline[i] < timeline[i+1], \
                f"Timeline fora de ordem: {timeline[i]} > {timeline[i+1]}"
    
    def test_timeline_within_bounds(self, data_provider):
        """1.5: Timeline deve estar dentro do período solicitado"""
        start = pd.to_datetime("2023-03-01")
        end = pd.to_datetime("2023-06-30")
        
        timeline = data_provider.get_market_timeline(start, end)
        
        assert timeline[0] >= start, f"Primeiro dia {timeline[0]} < start {start}"
        assert timeline[-1] <= end, f"Último dia {timeline[-1]} > end {end}"
