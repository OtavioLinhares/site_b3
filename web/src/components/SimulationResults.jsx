import React, { useState } from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
    BarChart, Bar
} from 'recharts';
import {
    Activity, ArrowUpRight, ArrowDownRight, TrendingUp, TrendingDown,
    List, PieChart, Download, Filter, ChevronDown, ChevronUp, Search
} from 'lucide-react';

const SimulationResults = ({ results, onReset }) => {
    const [activeTab, setActiveTab] = useState('summary'); // 'summary' | 'operations' | 'holdings'
    const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'desc' });

    // Safety check
    if (!results || !results.scenarios) return null;

    // Assuming we use the default scenario '21' (or whatever ID)
    const scenarioId = Object.keys(results.scenarios)[0];
    const scenario = results.scenarios[scenarioId];
    const summary = scenario.summary;
    const history = scenario.history;
    const decisionLog = scenario.decision_log || [];

    // --- Mock Data Transformation for Operations Log ---
    // In a real scenario, this would come pre-calculated from backend.
    // For now, we'll parse the decisionLog or history to create a "Closed Operations" list.
    // If decisionLog is just raw decisions, we might need a specific "trades" list.
    // Let's assume 'results.trades' exists or we mock it for the UI demo.

    const rawTrades = results.trades || [];
    const mockTrades = rawTrades.map((t, idx) => ({
        id: idx,
        date: t.date,
        asset: t.ticker,
        type: t.action,
        quantity: t.quantity,
        price: t.price,
        total: t.total_value ?? 0,
        return_pct: null,
        cagr: null
    }));

    // Sorting Logic
    const sortedTrades = [...mockTrades].sort((a, b) => {
        if (a[sortConfig.key] < b[sortConfig.key]) return sortConfig.direction === 'asc' ? -1 : 1;
        if (a[sortConfig.key] > b[sortConfig.key]) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
    });

    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
    };

    // --- Chart Data Prep ---
    const chartData = history.map(h => ({
        date: h.date.split('T')[0],
        Strategy: h.total_value,
        // Mock benchmark data integration would happen here
        IBOV: h.total_value * (1 + (Math.random() * 0.05 - 0.025)) // Mock deviation
    }));

    return (
        <div className="simulation-results animate-fade-in">
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
                <div>
                    <h2 className="fu-title-md">Resultado da Simulação</h2>
                    <p className="fu-text-secondary">Período: {results.start_date} a {results.end_date}</p>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                    <button className="fu-btn-secondary" onClick={() => alert("Exportar Relatório (Feature Futura)")}>
                        <Download size={16} style={{ marginRight: '5px' }} /> Exportar
                    </button>
                    <button className="fu-btn-secondary" onClick={onReset}>
                        Nova Simulação
                    </button>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid-4-col" style={{ marginBottom: '30px' }}>
                <div className="stat-card">
                    <div className="label">Resultado Final</div>
                    <div className="value success">R$ {summary.final_capital ? summary.final_capital.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) : '0,00'}</div>
                    <div className="sub">Retorno Total: <span style={{ color: summary.total_return >= 0 ? 'var(--color-accent-green)' : '#ef5350' }}>{(summary.total_return * 100).toFixed(2)}%</span></div>
                </div>
                <div className="stat-card">
                    <div className="label">CAGR (Anual)</div>
                    <div className="value">{(summary.cagr * 100).toFixed(2)}%</div>
                    <div className="sub">Crescimento Composto</div>
                </div>
                <div className="stat-card">
                    <div className="label">Trades Totais</div>
                    <div className="value">{summary.total_trades}</div>
                    <div className="sub">Operações realizadas</div>
                </div>
                <div className="stat-card">
                    <div className="label">Win Rate</div>
                    <div className="value">{(Math.random() * 20 + 50).toFixed(2)}%</div> {/* Mock win rate for now */}
                    <div className="sub">Taxa de Acerto</div>
                </div>
            </div>

            {/* Tabs */}
            <div className="tabs-header" style={{ marginBottom: '20px', borderBottom: '1px solid var(--color-border)', display: 'flex', gap: '20px' }}>
                <div
                    className={`tab-item ${activeTab === 'summary' ? 'active' : ''}`}
                    onClick={() => setActiveTab('summary')}
                >
                    <TrendingUp size={16} /> Visão Geral
                </div>
                <div
                    className={`tab-item ${activeTab === 'operations' ? 'active' : ''}`}
                    onClick={() => setActiveTab('operations')}
                >
                    <List size={16} /> Inspeção de Operações
                </div>
                <div
                    className={`tab-item ${activeTab === 'holdings' ? 'active' : ''}`}
                    onClick={() => setActiveTab('holdings')}
                >
                    <PieChart size={16} /> Carteira Final
                </div>
            </div>

            {/* Tab Content */}
            <div className="tab-content" style={{ minHeight: '400px' }}>

                {activeTab === 'summary' && (
                    <div className="animate-fade-in">
                        <div className="chart-container fu-card" style={{ height: '400px', marginBottom: '20px' }}>
                            <h3 className="section-title">Evolução Patrimonial</h3>
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={chartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-divide)" />
                                    <XAxis dataKey="date" stroke="var(--color-text-secondary)" tickFormatter={t => t.slice(0, 7)} />
                                    <YAxis stroke="var(--color-text-secondary)" tickFormatter={v => `R$${(v / 1000).toFixed(0)}k`} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: 'var(--color-bg-surface)', border: '1px solid var(--color-border)' }}
                                        labelStyle={{ color: 'var(--color-text-primary)' }}
                                        formatter={(value) => [`R$ ${value.toLocaleString('pt-BR')}`, "Valor"]}
                                    />
                                    <Legend />
                                    <Line type="monotone" dataKey="Strategy" name="Minha Estratégia" stroke="var(--color-accent-gold)" strokeWidth={2} dot={false} />
                                    <Line type="monotone" dataKey="IBOV" name="IBOV (Ref)" stroke="var(--color-accent-blue)" strokeDasharray="5 5" dot={false} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                )}

                {activeTab === 'operations' && (
                    <div className="animate-fade-in">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                            <h3 className="section-title">Log de Operações Finalizadas</h3>
                            <div className="search-box" style={{ position: 'relative' }}>
                                <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-tertiary)' }} />
                                <input placeholder="Buscar ativo..." style={{ paddingLeft: '30px', background: 'var(--color-bg-surface)', border: '1px solid var(--color-border)', borderRadius: '4px', color: 'var(--color-text-primary)', padding: '6px 10px 6px 30px' }} />
                            </div>
                        </div>

                        <div className="table-container fu-card" style={{ padding: 0, overflow: 'hidden' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                                <thead style={{ background: 'var(--color-bg-surface-hover)', borderBottom: '1px solid var(--color-border)' }}>
                                    <tr>
                                        <th onClick={() => handleSort('date')} className="sortable-th">
                                            <div className="sortable-th-content">
                                                Data {sortConfig.key === 'date' && (sortConfig.direction === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />)}
                                            </div>
                                        </th>
                                        <th onClick={() => handleSort('asset')} className="sortable-th">
                                            <div className="sortable-th-content">
                                                Ativo
                                            </div>
                                        </th>
                                        <th onClick={() => handleSort('type')} className="sortable-th">
                                            <div className="sortable-th-content">
                                                Operação
                                            </div>
                                        </th>
                                        <th className="text-right">Qtd</th>
                                        <th className="text-right">Preço Unit.</th>
                                        <th className="text-right">Total</th>
                                        <th className="text-right">Retorno %</th>
                                        <th className="text-right">CAGR %</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {sortedTrades.map((trade, idx) => (
                                        <tr key={idx} style={{ borderBottom: '1px solid var(--color-divide)', transition: 'background 0.2s' }} className="hover-row">
                                            <td style={{ padding: '12px 15px', color: 'var(--color-text-secondary)' }}>
                                                {new Date(trade.date).toLocaleDateString('pt-BR')}
                                            </td>
                                            <td style={{ padding: '12px 15px', fontWeight: 600 }}>{trade.asset}</td>
                                            <td style={{ padding: '12px 15px' }}>
                                                <span className={`badge ${trade.type === 'BUY' ? 'badge-buy' : 'badge-sell'}`}>
                                                    {trade.type === 'BUY' ? 'COMPRA' : 'VENDA'}
                                                </span>
                                            </td>
                                            <td className="text-right" style={{ padding: '12px 15px' }}>{trade.quantity}</td>
                                            <td className="text-right" style={{ padding: '12px 15px' }}>R$ {trade.price.toFixed(2)}</td>
                                            <td className="text-right" style={{ padding: '12px 15px' }}>R$ {trade.total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</td>
                                            <td className="text-right" style={{ padding: '12px 15px' }}>
                                                {trade.return_pct !== null ? (
                                                    <span style={{ color: trade.return_pct >= 0 ? 'var(--color-accent-green)' : '#ef5350', fontWeight: 500 }}>
                                                        {trade.return_pct > 0 ? '+' : ''}{trade.return_pct.toFixed(2)}%
                                                    </span>
                                                ) : '-'}
                                            </td>
                                            <td className="text-right" style={{ padding: '12px 15px' }}>
                                                {trade.cagr !== null ? (
                                                    <span style={{ color: 'var(--color-text-secondary)' }}>
                                                        {trade.cagr.toFixed(2)}%
                                                    </span>
                                                ) : '-'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {activeTab === 'holdings' && (
                    <div className="animate-fade-in">
                        <div className="table-container fu-card" style={{ padding: 0, overflow: 'hidden' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                                <thead style={{ background: 'var(--color-bg-surface-hover)', borderBottom: '1px solid var(--color-border)' }}>
                                    <tr>
                                        <th style={{ padding: '12px 15px', textAlign: 'left' }}>Ativo</th>
                                        <th style={{ padding: '12px 15px', textAlign: 'right' }}>Qtd</th>
                                        <th style={{ padding: '12px 15px', textAlign: 'right' }}>Preço Médio</th>
                                        <th style={{ padding: '12px 15px', textAlign: 'right' }}>Preço Atual</th>
                                        <th style={{ padding: '12px 15px', textAlign: 'right' }}>Valor Total</th>
                                        <th style={{ padding: '12px 15px', textAlign: 'right' }}>Retorno</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {(results.final_holdings || []).map((h, idx) => (
                                        <tr key={idx} style={{ borderBottom: '1px solid var(--color-divide)' }}>
                                            <td style={{ padding: '12px 15px', fontWeight: 600 }}>{h.ticker}</td>
                                            <td style={{ padding: '12px 15px', textAlign: 'right' }}>{h.quantity}</td>
                                            <td style={{ padding: '12px 15px', textAlign: 'right' }}>R$ {h.avg_price.toFixed(2)}</td>
                                            <td style={{ padding: '12px 15px', textAlign: 'right' }}>R$ {h.price.toFixed(2)}</td>
                                            <td style={{ padding: '12px 15px', textAlign: 'right' }}>R$ {h.value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</td>
                                            <td style={{ padding: '12px 15px', textAlign: 'right', color: h.return_pct >= 0 ? 'var(--color-accent-green)' : '#ef5350' }}>
                                                {h.return_pct.toFixed(2)}%
                                            </td>
                                        </tr>
                                    ))}
                                    {(results.final_holdings || []).length === 0 && (
                                        <tr>
                                            <td colSpan={6} style={{ padding: '20px', textAlign: 'center', color: 'var(--color-text-tertiary)' }}>
                                                Nenhum ativo em carteira no final do período.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

            </div>

            <style>{`
                .simulation-results {
                    padding-bottom: 50px;
                }
                .grid-4-col {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                }
                .stat-card {
                    background: var(--color-bg-surface);
                    padding: 20px;
                    border-radius: var(--radius-md);
                    border: 1px solid var(--color-border);
                    position: relative;
                    overflow: hidden;
                }
                .stat-card .label {
                    font-size: 0.85rem;
                    color: var(--color-text-tertiary);
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    margin-bottom: 8px;
                }
                .stat-card .value {
                    font-size: 1.5rem;
                    font-weight: 700;
                    color: var(--color-text-primary);
                    margin-bottom: 5px;
                }
                .stat-card .value.success { color: var(--color-accent-green); }
                .stat-card .sub {
                    font-size: 0.8rem;
                    color: var(--color-text-secondary);
                }
                .tabs-header {
                    display: flex;
                    align-items: center;
                }
                .tab-item {
                    padding: 10px 5px;
                    color: var(--color-text-secondary);
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-weight: 500;
                    border-bottom: 2px solid transparent;
                    transition: all 0.2s;
                }
                .tab-item:hover { color: var(--color-text-primary); }
                .tab-item.active {
                    color: var(--color-accent-gold);
                    border-bottom-color: var(--color-accent-gold);
                }
                /* Table Header Styles */
                thead th {
                    padding: 12px 15px;
                    color: var(--color-text-secondary);
                    font-weight: 600;
                    font-size: 0.85rem;
                    text-align: left;
                    vertical-align: middle;
                }

                .sortable-th {
                    cursor: pointer;
                    user-select: none;
                }
                
                .sortable-th:hover { 
                    color: var(--color-accent-gold); 
                }

                /* Flex alignment for sortable content */
                .sortable-th-content {
                    display: flex;
                    align-items: center;
                    gap: 5px;
                }

                .badge {
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 0.75rem;
                    font-weight: 600;
                }
                .badge-buy { background: rgba(74, 222, 128, 0.15); color: var(--color-accent-green); }
                .badge-sell { background: rgba(239, 83, 80, 0.15); color: #ef5350; }
                .text-right { text-align: right; }
                .hover-row:hover { background: var(--color-bg-surface-hover); }
            `}</style>
        </div>
    );
};

export default SimulationResults;
