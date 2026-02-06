
from sqlalchemy.orm import Session
from data.database import init_db, Asset, FundamentalData, EconomicData
from sqlalchemy import func, desc
import pandas as pd
import fundamentus

class MetricsEngine:
    def __init__(self, db_path='sqlite:///stocks.db'):
        self.engine = init_db(db_path)
    
    def get_session(self):
        return Session(self.engine)

    def _base_filter(self, query):
        """
        Applies common filters:
        - Liquidity > 0 (to remove inactive stocks)
        """
        return query.filter(FundamentalData.liq_2m > 0)


    def avg_pl_market(self):
        """
        Calculates the average P/L of the market using 2 Standard Deviations outlier removal.
        """
        session = self.get_session()
        try:
            # 1. Fetch all positive P/Ls (assuming negative P/L is a different category/cleaning step, 
            # or should we include negatives in the distribution? 
            # Usually for "Market P/L" we look at profitable companies or the whole market. 
            # Let's fetch all valid numeric P/Ls first.
            
            # Using pandas for easy std deviation calc
            query = session.query(FundamentalData.p_l).filter(FundamentalData.p_l != None)
            query = self._base_filter(query)
            df = pd.read_sql(query.statement, session.bind)
            
            if df.empty:
                return 0.0
            
            # 2. Calculate Stats
            # Filter out zero/null if necessary? decided to keep neg P/L for distribution unless specified otherwise.
            # But usually P/L avg implies we want to see valuation. 
            # Let's keep all valid numbers first.
            
            mean = df['p_l'].mean()
            std = df['p_l'].std()
            
            # 3. Filter Outliers (2 SD)
            lower_bound = mean - 2 * std
            upper_bound = mean + 2 * std
            
            filtered_df = df[(df['p_l'] >= lower_bound) & (df['p_l'] <= upper_bound)]
            
            new_mean = filtered_df['p_l'].mean()
            
            print(f"Stats: Original Count={len(df)}, Mean={mean:.2f}, Std={std:.2f}")
            print(f"Filter: [{lower_bound:.2f}, {upper_bound:.2f}]")
            print(f"Filtered Count={len(filtered_df)}, New Mean={new_mean:.2f}")
            
            return new_mean
        finally:
            session.close()

    def avg_pl_top50(self):
        """
        Calculates the Average P/L of the 50 largest companies by Market Cap.
        Applies 2-sigma outlier removal on this subset.
        """
        session = self.get_session()
        try:
            # 1. Fetch Top 50 by Market Cap
            # Filter valid P/L and Market Cap
            query = session.query(FundamentalData.p_l, FundamentalData.market_cap).\
                join(Asset).\
                filter(
                    FundamentalData.p_l != None,
                    FundamentalData.market_cap != None,
                    FundamentalData.liq_2m > 0
                ).\
                order_by(FundamentalData.market_cap.desc()).\
                limit(50)
                
            df = pd.read_sql(query.statement, session.bind)
            
            if df.empty:
                return 0.0
                
            # 2. Convert raw units if needed (PatrLiq is usually raw)
            # 3. Calculate Stats & Filter
            mean = df['p_l'].mean()
            std = df['p_l'].std()
            
            lower_bound = mean - 2 * std
            upper_bound = mean + 2 * std
            
            filtered_df = df[(df['p_l'] >= lower_bound) & (df['p_l'] <= upper_bound)]
            new_mean = filtered_df['p_l'].mean()
            
            return new_mean
        finally:
            session.close()

    def get_top_companies_by_pl(self, limit=10):
        """
        Returns top 10 companies with lowest positive P/L.
        """
        session = self.get_session()
        try:
            results = session.query(Asset.ticker, FundamentalData.p_l, FundamentalData.roe, FundamentalData.net_margin).\
                join(Asset).\
                filter(
                    FundamentalData.p_l > 0,
                    
                    # (i) Liquidity > 100 Million
                    FundamentalData.liq_2m > 100000000,
                    
                    # (ii) Valid History 5y (Proxy: Must have growth data)
                    FundamentalData.revenue_growth_5y != None,
                    FundamentalData.revenue_growth_5y != 0,
                    
                    # (iii) Positive Margin (Current as Proxy for 'Last 5y')
                    FundamentalData.net_margin > 0,
                    
                    # (iv) Positive ROE (Current as Proxy for 'Last 5y')
                    FundamentalData.roe > 0
                )
            
            results = self._base_filter(results)
            
            # Fetch more candidates to allow for grouping reduction
            raw_data = results.order_by(FundamentalData.p_l.asc()).limit(limit * 3).all()
            
            df = pd.DataFrame(raw_data, columns=['ticker', 'p_l', 'roe', 'net_margin'])
            
            if df.empty:
                return pd.DataFrame(columns=['ticker', 'sector', 'p_l', 'net_margin', 'observation'])

            # Grouping: Use first 4 chars of ticker (e.g. PETR3/PETR4 -> PETR)
            df['Company_Group'] = df['ticker'].str[:4]
            # Sort by P/L ascending
            df = df.sort_values(by='p_l')
            # Drop duplicates keeping first (lowest P/L)
            df = df.drop_duplicates(subset='Company_Group', keep='first')
            
            # Take Top N
            df = df.head(limit).copy()
            
            # Enrich with Sector & Observations
            df['sector'] = 'Indefinido'
            df['observation'] = ''
            
            # On-demand sector fetch
            print(f"Fetching sectors for Top {len(df)} companies...")
            for index, row in df.iterrows():
                ticker = row['ticker']
                try:
                    details = fundamentus.get_papel(ticker)
                    if isinstance(details, pd.DataFrame) and 'Setor' in details.columns:
                        sector = details['Setor'].iloc[0]
                        df.at[index, 'sector'] = sector
                except Exception as e:
                    print(f"Error fetching sector for {ticker}: {e}")
            
            # Heuristic for Observation: Check for high margin (>35%)
            # User asked: "Aumentos superiores a 35%... avaliar recorrencia"
            # Since we only have current margin, we flag High Margin > 35% as a proxy warning
            mask_high_margin = df['net_margin'] > 0.35
            df.loc[mask_high_margin, 'observation'] = 'Alta Margem Líq (>35%): Avaliar Recorrência'
            
            return df[['ticker', 'sector', 'p_l', 'net_margin', 'observation']]
        finally:
            session.close()
            
    def get_top_stable_companies(self, limit=10):
        """
        Without history, we define 'stable' as:
        - Positive P/L
        - Positive ROE
        - Positive Margin
        Ordered by P/L descending (as requested: 'ordenado por P/L descresente')
        """
        session = self.get_session()
        try:
            results = session.query(Asset.ticker, FundamentalData.p_l, FundamentalData.roe, FundamentalData.net_margin).\
                join(Asset).\
                filter(
                    FundamentalData.p_l > 0,
                    FundamentalData.roe > 0.10, # > 10% ROE
                    FundamentalData.net_margin > 0.05 # > 5% Margin
                )
            
            results = self._base_filter(results)
            
            # Requested: Stability candidates sorted by Net Margin (Margem Líquida)
            results = results.order_by(FundamentalData.net_margin.desc()).\
                limit(limit).all()
                
            df = pd.DataFrame(results, columns=['ticker', 'p_l', 'roe', 'net_margin'])
            # Add stability_score proxy (Net Margin for now as per previous logic)
            df['stability_score'] = df['net_margin']
            return df
        finally:
            session.close()

    def get_top_growth_companies(self, limit=10):
        """
        Using Revenue Growth 5y (c5y) as proxy for Growth since we lack historical LPA series.
        """
        session = self.get_session()
        try:
            results = session.query(Asset.ticker, FundamentalData.p_l, FundamentalData.revenue_growth_5y).\
                join(Asset).\
                filter(
                    FundamentalData.revenue_growth_5y > 0.10, # > 10% growth
                    FundamentalData.p_l > 0
                )
            
            results = self._base_filter(results)
            
            results = results.order_by(FundamentalData.revenue_growth_5y.desc()).\
                limit(limit).all()
            
            return pd.DataFrame(results, columns=['ticker', 'p_l', 'revenue_growth_5y'])
        finally:
            session.close()

    MACRO_SECTOR_MAP = {
        'Setor Bancário': ['Bancos'],
        'Serviços Financeiros e Seguros': ['Seguradoras', 'Soc. Crédito e Financiamento', 'Serviços Financeiros Diversos', 'Gestão de Recursos e Investimentos', 'Corretoras de Seguros'],
        'Alimentos e Bebidas': ['Alimentos Processados', 'Bebidas', 'Alimentos', 'Alimentos Diversos', 'Carnes e Derivados', 'Açucar e Alcool', 'Cervejas e Refrigerantes'],
        'Varejo e Bens de Consumo': ['Comércio', 'Comércio e Distribuição', 'Produtos de Uso Pessoal e de Limpeza', 'Tecidos, Vestuário e Calçados', 'Utilidades Domésticas', 'Acessórios', 'Calçados', 'Vestuário', 'Fios e Tecidos', 'Móveis', 'Eletrodomésticos', 'Utensílios Domésticos', 'Produtos de Limpeza', 'Produtos de Uso Pessoal'],
        'Energia Elétrica': ['Energia Elétrica'],
        'Saneamento e Gás': ['Água e Saneamento', 'Gás'],
        'Materiais Básicos': ['Mineração', 'Minerais Metálicos', 'Siderurgia', 'Siderurgia e Metalurgia', 'Artefatos de Ferro e Aço', 'Artefatos de Cobre', 'Papel e Celulose', 'Madeira', 'Madeira e Papel', 'Químicos', 'Químicos Diversos', 'Petroquímicos', 'Fertilizantes e Defensivos'],
        'Bens Industriais': ['Máquinas e Equipamentos', 'Máq. e Equip. Industriais', 'Máq. e Equip. Construção e Agrícolas', 'Motores, Compressores e Outros', 'Armas e Munições'],
        'Logística e Transportes': ['Transporte', 'Exploração de Rodovias', 'Serviços de Apoio e Armazenagem', 'Transporte Ferroviário', 'Transporte Hidroviário', 'Transporte Rodoviário', 'Transporte Aéreo'],
        'Construção e Engenharia': ['Construção e Engenharia', 'Construção Pesada', 'Engenharia Consultiva', 'Produtos para Construção'],
        'Tecnologia e Telecom': ['Tecnologia da Informação', 'Telecomunicações', 'Computadores e Equipamentos', 'Programas e Serviços'],
        'Saúde': ['Saúde', 'Medicamentos e Outros Produtos', 'Serv.Méd.Hospit. Análises e Diagnósticos'],
        'Imobiliário': ['Exploração de Imóveis', 'Incorporações', 'Intermediação Imobiliária'],
        'Petróleo e Gás': ['Petróleo, Gás e Biocombustíveis', 'Exploração, Refino e Distribuição', 'Equipamentos e Serviços'],
        'Agronegócio': ['Agropecuária', 'Agricultura'],
        'Lazer e Turismo': ['Viagens e Lazer', 'Viagens e Turismo', 'Atividades Esportivas', 'Bicicletas', 'Brinquedos e Jogos', 'Produção de Eventos e Shows', 'Hotelaria', 'Restaurante e Similares'],
        'Holdings e Diversos': ['Holdings Diversificadas', 'Diversos', 'Programas de Fidelização', 'Serviços Educacionais', 'Serviços Diversos', 'Produtos Diversos', 'Outros']
    }

    def get_macro_sector(self, sector_or_subsector):
        for macro, items in self.MACRO_SECTOR_MAP.items():
            if sector_or_subsector in items:
                return macro
        return 'Holdings e Diversos'

    def calculate_pl_color_score(self, pl):
        """
        Maps P/L to a 0-1 score for heatmap coloring.
        0.0 (Green) = Attractive (Positive and close to 0)
        1.0 (Red) = Unattractive (Negative or very high)
        """
        if pl is None or pl <= 0:
            return 1.0 # Red for losses
        
        # Max limit for green-to-red gradient is 40
        if pl <= 40:
            return pl / 40.0
        else:
            return 1.0 # Red for very expensive stocks

    def get_sectors_view(self, macro_sector=None):
        """
        Returns data for Macro Sector OR Segment view.
        Uses Score-first Averaging for color and E/P-based Averaging for numerical P/L.
        """
        session = self.get_session()
        try:
            query = session.query(
                Asset.ticker, 
                Asset.sector.label('setor'),
                Asset.subsector.label('segmento'), 
                FundamentalData.market_cap,
                FundamentalData.p_l,
                FundamentalData.net_margin
            ).join(Asset).filter(
                FundamentalData.market_cap > 0,
                FundamentalData.market_cap < 1e12, # Safety Cap: 1 Trillion BRL
                FundamentalData.liq_2m > 0,
                ~Asset.ticker.like('AZUL%'),
                ~Asset.ticker.like('GOLL%')
            )
            
            df = pd.read_sql(query.statement, session.bind)
            if df.empty:
                return pd.DataFrame()

            df['Company_Base'] = df['ticker'].str[:4]
            
            def get_best_ticker_idx(group):
                pos_pl = group[group['p_l'] > 0]
                if not pos_pl.empty:
                    return pos_pl['p_l'].idxmin()
                valid = group.dropna(subset=['p_l'])
                if valid.empty:
                    return group.index[0]
                return valid['p_l'].idxmax()
            
            best_indices = df.groupby('Company_Base', group_keys=True).apply(get_best_ticker_idx, include_groups=False).dropna()
            df_agg = df.loc[best_indices].copy()
            mcap_sums = df.groupby('Company_Base')['market_cap'].sum()
            df_agg['market_cap'] = df_agg['Company_Base'].map(mcap_sums)
            df = df_agg.reset_index(drop=True)
            
            df['Segmento'] = df['segmento'].fillna('Indefinido')
            df['Macro_Sector'] = df['Segmento'].apply(self.get_macro_sector)
            
            # Individual Score Calculation
            df['color_score'] = df['p_l'].apply(self.calculate_pl_color_score)
            
            # E/P for weighted P/L Display
            df['e_p'] = df['p_l'].apply(lambda x: 1/x if (x and x != 0) else 0)
            
            def weighted_score(g):
                valid = g.dropna(subset=['color_score', 'market_cap'])
                if valid['market_cap'].sum() == 0: return 0.5
                return (valid['color_score'] * valid['market_cap']).sum() / valid['market_cap'].sum()

            def weighted_pl_ep(g):
                valid = g.dropna(subset=['e_p', 'market_cap'])
                total_mcap = valid['market_cap'].sum()
                if total_mcap == 0: return 0
                avg_ep = (valid['e_p'] * valid['market_cap']).sum() / total_mcap
                if avg_ep <= 0: return -1.0 
                return 1 / avg_ep

            def weighted_margin(g):
                valid = g.dropna(subset=['net_margin', 'market_cap'])
                if valid['market_cap'].sum() == 0: return 0
                return (valid['net_margin'] * valid['market_cap']).sum() / valid['market_cap'].sum()
            
            if macro_sector is None:
                group_col = 'Macro_Sector'
            else:
                df = df[df['Macro_Sector'] == macro_sector]
                group_col = 'Segmento'
            
            stats = df.groupby(group_col).agg({
                'market_cap': 'sum',
                'ticker': 'count'
            }).rename(columns={'ticker': 'num_companies'})
            stats = stats.sort_values('market_cap', ascending=False)
            
            top_20 = stats.index[:20].tolist()
            outros = stats.index[20:].tolist()
            
            stats['avg_score'] = df.groupby(group_col, group_keys=True).apply(weighted_score, include_groups=False)
            stats['weighted_pl'] = df.groupby(group_col, group_keys=True).apply(weighted_pl_ep, include_groups=False)
            stats['weighted_margin'] = df.groupby(group_col, group_keys=True).apply(weighted_margin, include_groups=False)
            
            total_mcap = df['market_cap'].sum()
            labels, values, colors, custom_data, group_names = [], [], [], [], []
            df_labels_text = [] 
            
            for g_name in top_20:
                g_stats = stats.loc[g_name]
                mcap = g_stats['market_cap']
                pct = mcap / total_mcap
                w_score = g_stats['avg_score']
                w_pl = g_stats['weighted_pl']
                w_margin = g_stats['weighted_margin']
                
                labels.append(g_name)
                values.append(mcap)
                colors.append(w_score)
                group_names.append(g_name)
                
                pl_disp = f"{w_pl:.2f}" if w_pl > 0 else "NEG"
                df_labels_text.append(f"{g_name}<br>P/L: {pl_disp}<br>M.Liq: {w_margin:.1%}")
                
                custom_data.append([
                    f"P/L Médio (E/P): {pl_disp}",
                    f"Valor: R$ {mcap/1e9:.1f}B ({pct:.1%})",
                    f"Empresas: {int(g_stats['num_companies'])}",
                    ""
                ])
            
            if outros:
                outros_df = df[df[group_col].isin(outros)]
                mcap = outros_df['market_cap'].sum()
                w_score = weighted_score(outros_df)
                w_pl = weighted_pl_ep(outros_df)
                w_margin = weighted_margin(outros_df)
                pct = mcap / total_mcap
                
                name = "Outros Segmentos" if macro_sector else "Outros Macro Setores"
                labels.append(name)
                values.append(mcap)
                colors.append(w_score)
                group_names.append("__OUTROS__")
                pl_disp = f"{w_pl:.2f}" if w_pl > 0 else "NEG"
                df_labels_text.append(name)
                
                custom_data.append([
                    f"P/L Médio (E/P): {pl_disp}",
                    f"Valor: R$ {mcap/1e9:.1f}B ({pct:.1%})",
                    f"Itens agrupados: {len(outros)}",
                    ""
                ])

            return pd.DataFrame({
                'labels': labels, 'values': values, 'colors': colors,
                'custom_data': custom_data, 'sector_names': group_names,
                'labels_text': df_labels_text
            })
        finally:
            session.close()

    def get_companies_view(self, sector_name, offset=0):
        """
        Returns data for COMPANIES-ONLY Treemap view for a specific segment.
        Applies a limit of 20 items, consolidating the rest into 'Outras'.
        """
        session = self.get_session()
        try:
            query = session.query(
                Asset.ticker, 
                Asset.subsector.label('segmento'), 
                FundamentalData.market_cap,
                FundamentalData.p_l,
                FundamentalData.net_margin,
                FundamentalData.net_debt_ebitda
            ).join(Asset).filter(
                FundamentalData.market_cap > 0,
                FundamentalData.market_cap < 1e12, # Safety Cap: 1 Trillion BRL
                FundamentalData.liq_2m > 0,
                ~Asset.ticker.like('AZUL%'),
                ~Asset.ticker.like('GOLL%')
            )
            
            df = pd.read_sql(query.statement, session.bind)
            if df.empty:
                return pd.DataFrame()

            df['Company_Base'] = df['ticker'].str[:4]
            
            def get_best_ticker_idx(group):
                pos_pl = group[group['p_l'] > 0]
                if not pos_pl.empty:
                    return pos_pl['p_l'].idxmin()
                valid = group.dropna(subset=['p_l'])
                if valid.empty:
                    return group.index[0]
                return valid['p_l'].idxmax()
            
            best_indices = df.groupby('Company_Base', group_keys=True).apply(get_best_ticker_idx, include_groups=False).dropna()
            df_agg = df.loc[best_indices].copy()
            mcap_sums = df.groupby('Company_Base')['market_cap'].sum()
            df_agg['market_cap'] = df_agg['Company_Base'].map(mcap_sums)
            df = df_agg.reset_index(drop=True)
            df['Segmento'] = df['segmento'].fillna('Indefinido')
            
            sector_df = df[df['Segmento'] == sector_name].sort_values('market_cap', ascending=False)
            
            # Slice Top 20
            top_20_df = sector_df.head(20)
            outras_df = sector_df.iloc[20:]
            
            labels, values, colors, custom_data, company_tickers, labels_text = [], [], [], [], [], []
            
            for _, company in top_20_df.iterrows():
                labels.append(company['ticker'])
                values.append(company['market_cap'])
                colors.append(self.calculate_pl_color_score(company['p_l']))
                company_tickers.append(company['ticker'])
                
                l_text = f"{company['ticker']}<br>P/L: {company['p_l']:.2f}<br>M.Liq: {company['net_margin']:.1%}" if company['p_l'] and company['net_margin'] else company['ticker']
                labels_text.append(l_text)
                
                custom_data.append([
                    f"P/L: {company['p_l']:.2f}" if company['p_l'] else "P/L: -",
                    f"M. Liq: {company['net_margin']:.1%}" if company['net_margin'] else "M. Liq: -",
                    f"Div/EBITDA: {company['net_debt_ebitda']:.2f}" if company['net_debt_ebitda'] else "Div/EBITDA: -",
                    ""
                ])
            
            if not outras_df.empty:
                mcap = outras_df['market_cap'].sum()
                # Simple average for P/L of Outras
                valid_pl = outras_df[outras_df['p_l'] > 0]
                w_pl = valid_pl['p_l'].mean() if not valid_pl.empty else 0
                
                labels.append("Outras Empresas")
                values.append(mcap)
                colors.append(self.calculate_pl_color_score(w_pl))
                company_tickers.append("__OUTRAS__")
                labels_text.append("Outras Empresas")
                
                custom_data.append([
                    f"{len(outras_df)} empresas",
                    f"P/L Médio: {w_pl:.2f}",
                    "", ""
                ])

            return pd.DataFrame({
                'labels': labels, 'values': values, 'colors': colors,
                'custom_data': custom_data, 'company_tickers': company_tickers,
                'labels_text': labels_text
            })

            return pd.DataFrame({
                'labels': labels, 'values': values, 'colors': colors,
                'custom_data': custom_data, 'company_tickers': company_tickers,
                'labels_text': labels_text
            })
        finally:
            session.close()
