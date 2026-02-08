import React, { useState, useEffect } from 'react';

const RankingTable = ({ title, description, data, metrics, centeredTitle }) => {
    if (!data || data.length === 0) {
        return (
            <div className="ranking-card fu-card">
                <h4 className="ranking-card-title" style={{ textAlign: centeredTitle ? 'center' : 'left' }}>{title}</h4>
                <p className="ranking-empty">Aguardando dados suficientes para este ranking...</p>
            </div>
        );
    }

    return (
        <div className="ranking-card fu-card">
            <h4 className="ranking-card-title" style={{ textAlign: centeredTitle ? 'center' : 'left' }}>{title}</h4>
            <p className="ranking-card-desc">{description}</p>
            <div className="ranking-table-wrapper">
                <table className="ranking-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Ticker</th>
                            {metrics.map(m => <th key={m.key} style={{ textAlign: 'right' }}>{m.label}</th>)}
                        </tr>
                    </thead>
                    <tbody>
                        {data.slice(0, 10).map((item, idx) => (
                            <tr key={item.ticker}>
                                <td className="rank-pos">{idx + 1}</td>
                                <td className="rank-ticker"><strong>{item.ticker}</strong></td>
                                {metrics.map(m => (
                                    <td key={m.key} className="rank-val">
                                        {m.format ? m.format(item[m.key]) : item[m.key]}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

const Rankings = () => {
    const [rankings, setRankings] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${import.meta.env.BASE_URL}data/rankings.json?t=${Date.now()}`)
            .then(res => res.json())
            .then(data => {
                // Apply strict liquidity filter
                const filtered = {};
                if (data && data.data) {
                    Object.keys(data.data).forEach(key => {
                        filtered[key] = data.data[key].filter(s => s.liq_2m && s.liq_2m >= 1000000);
                    });
                }
                setRankings({ ...data, data: filtered });
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to load rankings", err);
                setLoading(false);
            });
    }, []);

    if (loading) return <div className="fu-container"><div className="fu-card">Calculando rankings...</div></div>;
    if (!rankings) return null;

    return (
        <section className="rankings-section fu-container">
            {/* Standardized Header */}
            <div style={{ textAlign: 'left', marginBottom: 'var(--spacing-12)', maxWidth: '100%' }}>
                <h2 style={{
                    fontFamily: 'var(--font-family-serif)',
                    fontSize: '2.5rem',
                    lineHeight: '1.2',
                    marginBottom: 'var(--spacing-6)',
                    background: 'linear-gradient(to right, var(--color-text-primary), var(--color-text-secondary))',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    display: 'inline-block'
                }}>
                    Estratégias de Seleção
                </h2>

                <div style={{
                    marginTop: 'var(--spacing-4)',
                    borderLeft: '2px solid var(--color-accent-gold)',
                    paddingLeft: 'var(--spacing-6)',
                    marginLeft: 'var(--spacing-2)'
                }}>
                    <div style={{
                        textAlign: 'justify',
                        color: 'var(--color-text-tertiary)',
                        fontSize: 'var(--font-size-lg)',
                        lineHeight: '1.8',
                        maxWidth: '100%'
                    }}>
                        <p style={{ marginBottom: 0 }}>
                            Filtros quantitativos fundamentados em métricas essenciais de valuation, rentabilidade e crescimento.
                        </p>
                    </div>
                </div>
            </div>

            <div className="rankings-grid">
                <RankingTable
                    title="Oportunidades (Pontinha de Cigarro)"
                    description="Estratégia 'Deep Value': Empresas descontadas (Baixo P/VP) que ainda são lucrativas (Margem Positiva)."
                    data={rankings.data?.valor_qualidade}
                    metrics={[
                        { key: 'p_vp', label: 'P/VP', format: (v) => v.toFixed(2) + 'x' },
                        { key: 'net_margin', label: 'Margem Líq.', format: (v) => (v * 100).toFixed(1) + '%' }
                    ]}
                />

                <RankingTable
                    title="Bom, Bonito e Barato"
                    description="DIVIDENDOS: Equilíbrio entre proventos, eficiência operacional e preço justo."
                    data={rankings.data?.dividendos}
                    metrics={[
                        { key: 'dy', label: 'Yield', format: (v) => (v * 100).toFixed(1) + '%' },
                        { key: 'net_margin', label: 'Margem Líq.', format: (v) => (v * 100).toFixed(1) + '%' },
                        { key: 'p_l', label: 'Preço/Lucro', format: (v) => v.toFixed(1) + 'x' }
                    ]}
                    centeredTitle={true}
                />

                <RankingTable
                    title="Crescimento e Lucro"
                    description="Empresas com alto crescimento de receita (CAGR 5y) preservando margens saudáveis."
                    data={rankings.data?.crescimento}
                    metrics={[
                        { key: 'revenue_growth_5y', label: 'Cresc. Receita (5a)', format: (v) => (v * 100).toFixed(1) + '%' },
                        { key: 'net_margin', label: 'Margem Líq.', format: (v) => (v * 100).toFixed(1) + '%' }
                    ]}
                />
            </div>

            <style>{`
                .rankings-section { padding: var(--spacing-16) 0; max-width: 1400px; margin: 0 auto; }
                .rankings-grid {
                    display: grid;
                    grid-template-columns: 1fr;
                    gap: var(--spacing-8);
                    margin-top: var(--spacing-8);
                }
                @media (min-width: 1024px) {
                    .rankings-grid {
                        grid-template-columns: 1fr 1.3fr 1fr; /* Middle wider as requested */
                    }
                }
                .ranking-card { padding: var(--spacing-6); border: 1px solid var(--color-border); }
                .ranking-card-title { margin: 0; font-family: var(--font-family-serif); color: var(--color-primary); }
                .ranking-card-desc { font-size: 0.85rem; color: var(--color-text-secondary); margin: 8px 0 20px; min-height: 40px; }
                
                .ranking-table-wrapper { margin: 0 -12px; }
                .ranking-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
                .ranking-table th { font-weight: 500; color: var(--color-text-tertiary); text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em; padding: 12px; border-bottom: 1px solid var(--color-border); }
                .ranking-table td { padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); }
                
                .rank-pos { color: var(--color-text-tertiary); font-weight: 600; font-size: 0.8rem; text-align: center; width: 40px; }
                .rank-ticker { color: var(--color-text-primary); }
                .rank-val { text-align: right; font-variant-numeric: tabular-nums; color: var(--color-text-primary); font-weight: 500; }
                
                .ranking-empty { padding: var(--spacing-8); text-align: center; color: var(--color-text-tertiary); font-style: italic; font-size: 0.9rem; }
            `}</style>
        </section>
    );
};

export default Rankings;
