## Project Plan – Global Market Data Dashboard

### Vision
Oferecer um painel que compare os principais indicadores de valuation e rentabilidade da B3 com as 12 bolsas internacionais mais relevantes, utilizando dados atualizados automaticamente.

### Current Scope
1. **Cobertura B3**
   - Coletar snapshot diário da Fundamentus > validar > persistir em `stocks.db`.
   - Exportar lista de ativos (`public/data/b3_stocks.json`), rankings e exclusões.
2. **Cobertura Internacional**
   - Reunir as ~50 maiores companhias de cada bolsa-alvo e calcular métricas médias (P/L, margem líquida, ROE).
   - Normalizar e exportar comparativos em `public/data/world_comparison.json` e `public/data/world_markets.json`.
3. **Integração Front-end**
   - Primeiro bloco do site consome P/L e margem média por bolsa.

### Status (2026-02-06)
- ✅ **B3 consolidada**: pipeline diário atualizado, 857 ativos válidos, 120 excluídos. BDRs e FIIs filtrados para o comparativo global; holdings permanecem na lista com margem ignorada conforme regra.
- ✅ **Dados internacionais gerados via planilhas**: `scripts/process_manual_indices.py` normaliza os CSVs do Investing.com (S&P 500, Nasdaq 100, FTSE 100, DAX 40, CAC 40, IBEX 35, FTSE MIB, Euro Stoxx 50, Nikkei 225, Nifty 50, Shanghai, Tadawul, JSE Top 40, NSE 30, OMX Stockholm 30) e publica `public/data/world_comparison.json` + `world_markets.json`.
- ❗ **Lista final de bolsas**: atualmente temos 15 bolsas internacionais processadas; precisamos alinhavar com o time quais 12 permanecerão no comparativo para o bloco “B3 vs Mundo”.

### Next Milestones
1. **Validar universo definitivo**: confirmar com o usuário quais bolsas compõem a lista final de 12 e remover/ajustar o excedente.
2. **Revisar dados B3 extremos**: conferir market caps anômalos (ex.: GOLL4) e margens zeradas para garantir consistência antes da publicação no front.
3. **Conectar front-end**: garantir que o gráfico inicial consuma o novo formato (incluir B3 + bolsas aprovadas).
4. **Automatização**: definir rotina para substituir planilhas manuais e rodar `process_manual_indices.py` diariamente (cron + sync de arquivos).

### Risks / Decisions
- **Dependência de planilhas manuais**: requer disciplina para atualizar os CSVs de cada bolsa antes da execução diária.
- **Cobertura de dados históricos**: atualmente trabalhamos com snapshots; se for necessária série temporal para o gráfico, precisaremos ampliar o escopo.
