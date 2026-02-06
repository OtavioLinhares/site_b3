import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add root folder to sys path to import modules
sys.path.append(os.getcwd())

from analysis import metrics
import importlib
importlib.reload(metrics)
from analysis.metrics import MetricsEngine
from data.database import init_db, Asset, FundamentalData

# --- Config ---
st.set_page_config(
    page_title="Análise Ações Brasil",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Styling ---
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #333;
    }
    .metric-value {
        font-size: 2em;
        font-weight: bold;
        color: #4CAF50;
    }
    .metric-label {
        color: #ccc;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

# --- Init Engine ---
def get_engine():
    # Force reload metrics just in case
    importlib.reload(metrics)
    return MetricsEngine()

engine = get_engine()

# --- Header ---
st.title("🇧🇷 Dashboard de Análise de Ações")
st.markdown("Monitoramento de métricas fundamentais da Bolsa Brasileira com foco em **P/L**, **Estabilidade** e **Crescimento**.")

# --- B3 Overview Section ---
st.markdown("## 📊 Visão Geral da B3")

# Navigation Stack: list of dicts {'view': 'macro'|'segments'|'companies', 'macro': str|None, 'segment': str|None}
if 'nav_stack' not in st.session_state:
    st.session_state.nav_stack = [{'view': 'macro', 'macro': None, 'segment': None}]

# Current State is the top of the stack
curr = st.session_state.nav_stack[-1]

# Navigation Breadcrumb
breadcrumb = "B3"
for item in st.session_state.nav_stack[1:]:
    if item['view'] == 'segments':
        breadcrumb += f" > {item['macro']}"
    elif item['view'] == 'companies':
        breadcrumb += f" > {item['segment']}"

st.write(f"📍 **Navegação:** {breadcrumb}")

col_nav1, col_nav2 = st.columns([1, 4])
with col_nav1:
    if len(st.session_state.nav_stack) > 1:
        if st.button("⬅️ Voltar", use_container_width=True):
            st.session_state.nav_stack.pop()
            st.rerun()

# Get appropriate data
if curr['view'] == 'macro':
    df_tree = engine.get_sectors_view(macro_sector=None)
    view_title = "Macro Setores da B3"
elif curr['view'] == 'segments':
    df_tree = engine.get_sectors_view(macro_sector=curr['macro'])
    view_title = f"Segmentos - {curr['macro']}"
else:
    df_tree = engine.get_companies_view(sector_name=curr['segment'])
    view_title = f"Empresas - {curr['segment']}"

if not df_tree.empty:
    # Display metrics
    if curr['view'] == 'macro':
        total_companies = 146  
        total_groups = len(df_tree)
        col_ov1, col_ov2 = st.columns(2)
        with col_ov1:
            st.metric("Total de Empresas", total_companies)
        with col_ov2:
            st.metric("Macro Setores", total_groups)
    
    st.markdown(f"### {view_title}")
    
    # Divergent Color Scale: Red (-) to Green (+)
    # Refined aesthetics: Centered text, thinner borders, larger font
    fig_tree = go.Figure(go.Treemap(
        labels=df_tree['labels'],
        parents=[""] * len(df_tree),
        values=df_tree['values'],
        text=df_tree['labels_text'],  # Use the enriched labels
        branchvalues="total",
        marker=dict(
            colors=df_tree['colors'],
            # Custom P/L Scale: 0 (Green/Attractive) to 1 (Red/Unattractive)
            colorscale=[[0, 'green'], [0.3, 'yellowgreen'], [0.6, 'orange'], [1, 'red']],
            showscale=True,
            colorbar=dict(title="Score P/L", tickvals=[0, 1], ticktext=["Bom", "Ruim"]),
            line=dict(width=0.5, color="#1e1e1e")
        ),
        hovertemplate='<b>%{label}</b><br>%{customdata[0]}<br>%{customdata[1]}<br>%{customdata[2]}<br>%{customdata[3]}<extra></extra>',
        customdata=df_tree['custom_data'],
        texttemplate="%{text}",
        textposition="middle center", # Center horizontally and vertically
        insidetextfont=dict(size=18)   # Larger font
    ))
    
    fig_tree.update_layout(height=600, margin=dict(t=10, l=0, r=0, b=0))
    st.plotly_chart(fig_tree, use_container_width=True)
    
    st.markdown("**Selecione para explorar:**")
    cols = st.columns(5)
    
    if curr['view'] == 'macro':
        for idx, (label, macro_name) in enumerate(zip(df_tree['labels'], df_tree['sector_names'])):
            with cols[idx % 5]:
                if st.button(label, key=f"m_{idx}", use_container_width=True):
                    # Check how many segments this macro has
                    items = engine.MACRO_SECTOR_MAP.get(macro_name, [])
                    if len(items) == 1:
                        # Short-circuit: Go directly to companies
                        st.session_state.nav_stack.append({
                            'view': 'companies', 
                            'macro': macro_name,
                            'segment': items[0],
                            'skipped_segment': True # Track that we skipped a level
                        })
                    else:
                        st.session_state.nav_stack.append({
                            'view': 'segments', 
                            'macro': macro_name,
                            'segment': None
                        })
                    st.rerun()
    elif curr['view'] == 'segments':
        for idx, (label, segment_name) in enumerate(zip(df_tree['labels'], df_tree['sector_names'])):
            with cols[idx % 5]:
                if st.button(label, key=f"s_{idx}", use_container_width=True):
                    st.session_state.nav_stack.append({
                        'view': 'companies', 
                        'macro': curr['macro'],
                        'segment': segment_name
                    })
                    st.rerun()
    else:
        for idx, (label, ticker) in enumerate(zip(df_tree['labels'], df_tree['company_tickers'])):
            with cols[idx % 5]:
                if st.button(label, key=f"c_{idx}", use_container_width=True):
                    st.info(f"Ticker: {ticker}")
else:
    st.warning("Dados não encontrados para esta visão.")

st.divider()


# --- Rankings Section ---
st.markdown("## 📈 Rankings de Ações")

# Top 10 P/L
st.markdown("### 🏆 Top 10 Melhores P/L")
top_pl = engine.get_top_companies_by_pl(limit=10)
if not top_pl.empty:
    fig_pl = px.bar(top_pl, x='ticker', y='p_l', 
                    title='', 
                    labels={'ticker': 'Ativo', 'p_l': 'P/L'},
                    color='p_l',
                    color_continuous_scale='RdYlGn_r')
    st.plotly_chart(fig_pl, use_container_width=True)
else:
    st.info("Sem dados disponíveis.")

st.divider()

# Top 10 Estabilidade
st.markdown("### 🛡️ Top 10 Mais Estáveis (Proxy: Menor Desvio Padrão P/L)")
top_stable = engine.get_top_stable_companies(limit=10)
if not top_stable.empty:
    fig_stable = px.bar(top_stable, x='ticker', y='stability_score',
                        title='',
                        labels={'ticker': 'Ativo', 'stability_score': 'Score de Estabilidade'},
                        color='stability_score',
                        color_continuous_scale='Greens')
    st.plotly_chart(fig_stable, use_container_width=True)
else:
    st.info("Sem dados disponíveis.")

st.divider()

# Top 10 Crescimento
st.markdown("### 🚀 Top 10 Maior Crescimento (Proxy: Crescimento de Receita 5a)")
top_growth = engine.get_top_growth_companies(limit=10)
if not top_growth.empty:
    fig_growth = px.bar(top_growth, x='ticker', y='revenue_growth_5y',
                        title='',
                        labels={'ticker': 'Ativo', 'revenue_growth_5y': 'Crescimento 5a (%)'},
                        color='revenue_growth_5y',
                        color_continuous_scale='Blues')
    st.plotly_chart(fig_growth, use_container_width=True)
else:
    st.info("Sem dados disponíveis.")
