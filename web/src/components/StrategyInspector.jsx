import React, { useState, useMemo } from 'react';
import { ArrowLeft, ArrowRight, Filter, CheckCircle, Database } from 'lucide-react';

const StrategyInspector = ({ decisionLog }) => {
    const [currentIndex, setCurrentIndex] = useState(0);

    // Ensure logs are sorted by date
    const sortedLog = useMemo(() => {
        if (!decisionLog) return [];
        return decisionLog.sort((a, b) => new Date(a.date) - new Date(b.date));
    }, [decisionLog]);

    if (!sortedLog || sortedLog.length === 0) {
        return <div className="fu-card">Nenhum log de decisão disponível para este cenário.</div>;
    }

    const currentDecision = sortedLog[currentIndex];

    const handlePrev = () => setCurrentIndex(prev => Math.max(0, prev - 1));
    const handleNext = () => setCurrentIndex(prev => Math.min(sortedLog.length - 1, prev + 1));

    // Format helpers
    const fmtPct = (val) => (val * 100).toFixed(1) + '%';
    const fmtNum = (val) => val.toFixed(2);
    const fmtBRL = (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

    return (
        <div className="fu-card animate-fade-in" style={{ marginBottom: 'var(--spacing-8)', border: '1px solid var(--color-border)' }}>
            <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid #333', paddingBottom: '15px' }}>
                <h3 className="fu-title-sm" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Database size={18} /> Inspeção de Estratégia (Glass Box)
                </h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                    <button
                        onClick={handlePrev}
                        disabled={currentIndex === 0}
                        className="fu-btn-secondary"
                        style={{ opacity: currentIndex === 0 ? 0.5 : 1 }}
                    >
                        <ArrowLeft size={16} />
                    </button>
                    <span style={{ fontWeight: 'bold', minWidth: '100px', textAlign: 'center' }}>
                        {currentDecision.date}
                    </span>
                    <button
                        onClick={handleNext}
                        disabled={currentIndex === sortedLog.length - 1}
                        className="fu-btn-secondary"
                        style={{ opacity: currentIndex === sortedLog.length - 1 ? 0.5 : 1 }}
                    >
                        <ArrowRight size={16} />
                    </button>
                </div>
            </header>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginBottom: '20px' }}>
                <div className="fu-stat-card">
                    <span className="fu-label">Candidatos Filtrados</span>
                    <div className="fu-value-md">{currentDecision.candidates_count}</div>
                </div>
                <div className="fu-stat-card">
                    <span className="fu-label">Comprados</span>
                    <div className="fu-value-md" style={{ color: 'var(--color-success)' }}>{currentDecision.selected.length}</div>
                </div>
            </div>

            <h4 className="fu-title-xs" style={{ marginBottom: '10px', color: 'var(--color-text-secondary)' }}>
                Top 20 Candidatos (Ordenado por ROE)
            </h4>
            <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                    <thead>
                        <tr style={{ textAlign: 'left', color: 'var(--color-text-secondary)', borderBottom: '1px solid #333' }}>
                            <th style={{ padding: '8px' }}>Ticker</th>
                            <th style={{ padding: '8px' }}>Preço</th>
                            <th style={{ padding: '8px' }}>ROE</th>
                            <th style={{ padding: '8px' }}>P/L</th>
                            <th style={{ padding: '8px' }}>Dívida/EBITDA</th>
                            <th style={{ padding: '8px' }}>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {currentDecision.top_candidates.map((cand, idx) => {
                            const isSelected = currentDecision.selected.includes(cand.ticker);
                            return (
                                <tr key={cand.ticker} style={{
                                    backgroundColor: isSelected ? 'rgba(46, 204, 113, 0.1)' : 'transparent',
                                    borderBottom: '1px solid #222'
                                }}>
                                    <td style={{ padding: '8px', fontWeight: 'bold' }}>{cand.ticker}</td>
                                    <td style={{ padding: '8px' }}>R$ {fmtNum(cand.price)}</td>
                                    <td style={{ padding: '8px', color: 'var(--color-accent-gold)' }}>{fmtPct(cand.roe)}</td>
                                    <td style={{ padding: '8px' }}>{fmtNum(cand.p_l)}</td>
                                    <td style={{ padding: '8px', color: cand.net_debt_ebitda > 5 ? 'var(--color-danger)' : 'inherit' }}>
                                        {fmtNum(cand.net_debt_ebitda)}x
                                    </td>
                                    <td style={{ padding: '8px' }}>
                                        {isSelected ? (
                                            <span style={{ color: 'var(--color-success)', display: 'flex', alignItems: 'center', gap: '5px' }}>
                                                <CheckCircle size={14} /> Comprado
                                            </span>
                                        ) : (
                                            <span style={{ color: '#555' }}>-</span>
                                        )}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
            {currentDecision.top_candidates.length === 0 && (
                <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
                    Nenhum candidato atendeu aos critérios nesta data.
                </div>
            )}
        </div>
    );
};

export default StrategyInspector;
