import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LabelList } from 'recharts';

const WorldComparison = () => {
    const [data, setData] = useState([]);
    const [metric, setMetric] = useState('p_l'); // 'p_l' or 'net_margin'
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/data/world_comparison.json')
            .then(res => res.json())
            .then(fetchedData => {
                // Sort initial data locally if needed, but usually frontend handles sorting based on metric
                setData(fetchedData);
                setLoading(false);
            })
            .catch(err => console.error("Failed to load world data", err));
    }, []);

    const toNumber = (value) => {
        const num = Number(value);
        return Number.isFinite(num) ? num : null;
    };

    const getMetricValue = (entry) => {
        const value = entry?.[metric];
        return toNumber(value);
    };

    const sortedData = [...data].sort((a, b) => {
        const aVal = getMetricValue(a);
        const bVal = getMetricValue(b);
        if (aVal === null && bVal === null) return 0;
        if (aVal === null) return 1;
        if (bVal === null) return -1;
        return bVal - aVal;
    });

    const enrichedData = sortedData.map((entry) => {
        const metricRaw = getMetricValue(entry);
        return {
            ...entry,
            metric_raw: metricRaw,
            metric_value: metricRaw ?? 0,
        };
    });

    const metricLabel = metric === 'p_l' ? "Preço (P/L)" : "Margem Líquida (Rentabilidade)";
    const formatValue = (val) => {
        const num = toNumber(val);
        if (num === null) return 'N/A';
        return metric === 'p_l' ? `${num.toFixed(2)}x` : `${(num * 100).toFixed(1)}%`;
    };

    const getBarColor = (exchange) => {
        if (exchange === 'B3') return 'var(--color-accent-gold)';
        return '#333'; // Neutral
    };

    if (loading) return <div className="fu-card">Carregando dados globais...</div>;

    const comparisonMarkets = enrichedData.filter(item => item.exchange !== 'B3');
    const universeCount = comparisonMarkets.length;

    return (
        <section className="world-section fu-container">
            {/* Standardized Header */}
            <div className="section-header" style={{ display: 'block', textAlign: 'left', marginBottom: 'var(--spacing-12)', maxWidth: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
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
                        B3 vs O Mundo
                    </h2>

                    <div className="toggle-group" style={{ marginTop: '10px' }}>
                        <button
                            className={`toggle-btn ${metric === 'p_l' ? 'active' : ''}`}
                            onClick={() => setMetric('p_l')}
                        >
                            Preço (P/L)
                        </button>
                        <button
                            className={`toggle-btn ${metric === 'net_margin' ? 'active' : ''}`}
                            onClick={() => setMetric('net_margin')}
                        >
                            Rentabilidade (Margem)
                        </button>
                    </div>
                </div>

                <div style={{
                    marginTop: 'var(--spacing-4)',
                    borderLeft: '2px solid var(--color-accent-gold)',
                    paddingLeft: 'var(--spacing-6)',
                    marginLeft: 'var(--spacing-2)'
                }}>
                    <div className="section-desc" style={{
                        textAlign: 'justify',
                        color: 'var(--color-text-tertiary)',
                        fontSize: 'var(--font-size-lg)',
                        lineHeight: '1.8',
                        maxWidth: '100%',
                        marginBottom: 0
                    }}>
                        <p style={{ marginBottom: 'var(--spacing-4)' }}>
                            Comparativo da <strong>B3</strong> com {universeCount} bolsas monitoradas, sempre considerando o maior conjunto disponível de companhias líderes em cada índice.
                            A leitura pondera {metric === 'p_l' ? 'o múltiplo P/L agregado' : 'a margem líquida média dos últimos anos'} de cada mercado.
                        </p>
                        <p className="section-note" style={{ fontSize: 'var(--font-size-sm)', opacity: 0.8 }}>
                            P/L compara o preço de mercado com o lucro anual médio (quanto maior, mais caro). Margem líquida indica qual parcela da receita se transforma em lucro depois de todos os custos e impostos.
                        </p>
                    </div>
                </div>
            </div>

            <div className="chart-container fu-card">
                <ResponsiveContainer width="100%" height={500}>
                    <BarChart data={enrichedData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                        <XAxis type="number" hide />
                        <YAxis
                            dataKey="exchange"
                            type="category"
                            width={140}
                            tick={({ x, y, payload }) => {
                                const dataItem = enrichedData.find(d => d.exchange === payload.value);
                                return (
                                    <g transform={`translate(${x},${y})`}>
                                        <text x={0} y={0} dy={4} textAnchor="end" fill="var(--color-text-secondary)" fontSize={12}>
                                            {dataItem?.flag} {payload.value}
                                        </text>
                                    </g>
                                );
                            }}
                            axisLine={false}
                            tickLine={false}
                        />
                        <Tooltip
                            cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                            contentStyle={{ backgroundColor: 'var(--color-bg-surface)', borderColor: 'var(--color-border)', borderRadius: '8px' }}
                            itemStyle={{ color: 'var(--color-text-primary)' }}
                            formatter={(value) => [formatValue(value), metricLabel]}
                            labelFormatter={(label) => {
                                const item = enrichedData.find(d => d.exchange === label);
                                return item ? `${item.flag} ${item.exchange} • ${item.country} (Top ${item.top_n})` : label;
                            }}
                        />
                        <Bar dataKey="metric_value" radius={[0, 4, 4, 0]} barSize={20}>
                            {enrichedData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={getBarColor(entry.exchange)} />
                            ))}
                            <LabelList
                                dataKey="metric_value"
                                position="right"
                                formatter={(value, _name, props) =>
                                    formatValue(
                                        props?.payload?.metric_raw !== undefined
                                            ? props.payload.metric_raw
                                            : value
                                    )
                                }
                                fill="var(--color-text-secondary)"
                                fontSize={12}
                            />
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>

            <style>{`
        .world-section {
          padding: var(--spacing-12) 0;
        }
        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--spacing-6);
        }
        .section-title {
          font-family: var(--font-family-serif);
          font-size: var(--font-size-2xl);
          margin-bottom: 0;
        }
        .toggle-group {
          background-color: var(--color-bg-surface);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-sm);
          padding: 2px;
          display: flex;
        }
        .toggle-btn {
          background: transparent;
          border: none;
          color: var(--color-text-tertiary);
          padding: 6px 12px;
          cursor: pointer;
          font-size: var(--font-size-sm);
          font-weight: 500;
          border-radius: 2px;
          transition: all 0.2s;
        }
        .toggle-btn.active {
          background-color: var(--color-bg-main); /* Inverted for active state or distinct */
          background-color: #333;
          color: var(--color-text-primary);
        }
        .section-desc {
          margin-bottom: var(--spacing-8);
          max-width: 100%;
          color: var(--color-text-secondary);
        }
        .section-note {
          margin-top: var(--spacing-3);
          font-size: var(--font-size-xs);
          color: var(--color-text-tertiary);
        }
        .chart-container {
          height: 550px;
        }
      `}</style>
        </section>
    );
};

export default WorldComparison;
