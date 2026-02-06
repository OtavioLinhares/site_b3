## Plano de Implementação – Painel B3 e Bolsas Globais

### Premissas do projeto
- Visual “Fu Hui”: estética serena, tipografia limpa, alto contraste, foco em leitura.
- Dados estáticos atualizados diariamente via cron (06:00, Linux), pipeline com logs e publicação atômica em `public/data/`.
- Métricas obrigatórias conforme documento funcional (P/L, margem líquida média 5 anos, exclusão de outliers, etc.).

### Fases

#### Fase 0 – Fundamentos e Pipeline
| Tarefa | Status | Notas |
| --- | --- | --- |
| Documentação funcional completa | ✅ | Prompt original + este plano. |
| Pipeline B3 (Fundamentus + validações + export) | ✅ | `etl/pipeline.py` gera `b3_stocks.json`, `rankings.json`, `excluded_companies.json`, logs e garante atomicidade. |
| Banco e JSON com metadata (`generated_at`, etc.) | ✅ | Exporter cuida do envoltório e move atômico. |
| Lista de exclusões com motivo | ✅ | `public/data/excluded_companies.json`. |

#### Fase 1 – Abertura + B3 vs Mundo
| Tarefa | Status | Próximos passos |
| --- | --- | --- |
| Dados B3 consolidados (top 50, médias) | ✅ | Coleta local reutiliza `b3_stocks.json`. |
| Dados globais (12 bolsas) | ⚠️ | `scripts/process_manual_indices.py` gera 15 bolsas (S&P500, Nasdaq100, FTSE100, DAX40, CAC40, IBEX35, FTSE MIB, Euro Stoxx 50, Nikkei225, Nifty50, Shanghai, Tadawul, JSE Top 40, NSE 30, OMX Stockholm 30); falta escolher quais 12 permanecem. |
| Geração de `world_comparison.json` + `world_markets.json` | ✅ | Arquivos atualizados com as métricas ponderadas e lista de exclusões. |
| Texto explicativo e layout do bloco “B3 vs Mundo” | ⏳ | Front-end deverá consumir os arquivos gerados e seguir as regras (toggle P/L / Margem, 50 maiores, políticas de exclusão). |

#### Fase 2 – Drill-down B3 por Segmentos
| Tarefa | Status | Notas |
| --- | --- | --- |
| Estrutura de dados para segmentos/subsegmentos | ⏳ | Necessário consolidar info de setores/subsetores (Fundamentus). |
| UI interativa (sem botões externos, no mínimo 3 empresas por segmento) | ⏳ | Depende do front. |
| Filtros de segmento/subsegmento + busca | ⏳ | Depende do front. |

#### Fase 3 – Rankings
| Tarefa | Status | Notas |
| --- | --- | --- |
| Ranking Valor + Qualidade (margem 5y ≥ 12%, lucro positivo 5 anos, P/L válido) | ⏳ | Pipeline atual gera dados base, mas ranking final precisa considerar histórico 5 anos (não implementado ainda). |
| Top 10 Estáveis (margem sempre ≥12%, cálculo de max drawdown) | ⏳ | Requer séries históricas de margem. |
| Top 10 Crescimento (CAGR de receita, margens) | ⏳ | Requer séries históricas. |
| Visualizações (scatter, filtros, tooltips) | ⏳ | Trabalho de front após dados disponíveis. |

### Backlog imediato
1. Confirmar com o time a lista definitiva das 12 bolsas e ajustar o script/outputs.
2. Revisar outliers da B3 (market cap e margens zeradas) antes de expor no front.
3. Integrar front-end (bloco 2) ao novo formato.
4. Definir estratégia de automação diária para atualizar planilhas e rodar `process_manual_indices.py`.

### Observações operacionais
- Todos os scripts falham com código ≠ 0 em caso de erro (respeitando requisito do cron).
- Exportação é atômica (`tempfile` + `shutil.move`) para evitar arquivos parciais no `public/data/`.
- Logs diários armazenados em `logs/update_YYYY-MM-DD.log`.
- Coleta internacional depende de planilhas do Investing.com; garantir que os CSVs estejam atualizados antes da execução diária.
- Para evitar inconsistências, futuras alterações no pipeline devem ser refletidas tanto no `PROJECT_PLAN.md` quanto aqui, seguindo a regra de ouro do documento funcional.
