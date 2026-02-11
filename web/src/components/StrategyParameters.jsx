import React, { useState, useEffect } from 'react';
import { Settings, Sliders, AlertTriangle, Plus, Trash2, Check, X } from 'lucide-react';

const StrategyParameters = ({ onRun }) => {
    const [activeTab, setActiveTab] = useState('entry');

    // Logic Operators
    const [entryLogic, setEntryLogic] = useState('AND');
    const [exitLogic, setExitLogic] = useState('AND');

    // Available Metrics Configuration
    const METRICS = [
        { id: 'p_l', label: 'P/L', unit: 'x' },
        { id: 'p_vp', label: 'P/VP', unit: 'x' },
        { id: 'dl_ebitda', label: 'Dívida L./EBITDA', unit: 'x' },
        { id: 'roe', label: 'ROE', unit: '%' },
        { id: 'dy', label: 'Dividend Yield', unit: '%' },
        { id: 'net_margin', label: 'Margem Líq.', unit: '%' },
        { id: 'liquidity', label: 'Liq. Diária', unit: 'MM' },
        { id: 'cagr_revenue', label: 'CAGR Rec. 5a', unit: '%' },
        { id: 'cagr_profit', label: 'CAGR Lucro 5a', unit: '%' }
    ];

    const OPERATORS = [
        { id: '>', label: 'Maior que (>)' },
        { id: '>=', label: 'Maior ou Igual (>=)' },
        { id: '<', label: 'Menor que (<)' },
        { id: '<=', label: 'Menor ou Igual (<=)' },
        { id: '=', label: 'Igual (=)' }
    ];

    // Dynamic Rules State
    const [rules, setRules] = useState({
        entry: [
            { id: 1, metric: 'roe', operator: '>=', value: 10 },
            { id: 2, metric: 'p_l', operator: '<=', value: 25 }
        ],
        exit: [
            { id: 3, metric: 'p_l', operator: '>', value: 40 },
            { id: 4, metric: 'p_vp', operator: '>', value: 3.5 }
        ]
    });

    const [conflicts, setConflicts] = useState([]);

    // Helper to add a new rule
    const addRule = (section) => {
        const newId = Math.max(0, ...rules.entry.map(r => r.id), ...rules.exit.map(r => r.id)) + 1;
        setRules(prev => ({
            ...prev,
            [section]: [...prev[section], { id: newId, metric: 'p_l', operator: '>', value: 0 }]
        }));
    };

    // Helper to remove a rule
    const removeRule = (section, id) => {
        setRules(prev => ({
            ...prev,
            [section]: prev[section].filter(r => r.id !== id)
        }));
    };

    // Helper to update a rule
    const updateRule = (section, id, field, val) => {
        setRules(prev => ({
            ...prev,
            [section]: prev[section].map(r => r.id === id ? { ...r, [field]: val } : r)
        }));
    };

    // Conflict Detection Logic
    useEffect(() => {
        const newConflicts = [];

        // Find max Entry P/L and min Exit P/L for logical checks
        // This is heuristic because users can now add multiple rules
        const entryMaxPL = rules.entry.find(r => r.metric === 'p_l' && (r.operator === '<' || r.operator === '<='));
        const exitMinPL = rules.exit.find(r => r.metric === 'p_l' && (r.operator === '>' || r.operator === '>='));

        if (entryMaxPL && exitMinPL && parseFloat(entryMaxPL.value) >= parseFloat(exitMinPL.value)) {
            newConflicts.push(`Conflito P/L: Entrada (< ${entryMaxPL.value}) deve ser menor que Saída (> ${exitMinPL.value}).`);
        }

        const entryMaxPVP = rules.entry.find(r => r.metric === 'p_vp' && (r.operator === '<' || r.operator === '<='));
        const exitMinPVP = rules.exit.find(r => r.metric === 'p_vp' && (r.operator === '>' || r.operator === '>='));

        if (entryMaxPVP && exitMinPVP && parseFloat(entryMaxPVP.value) >= parseFloat(exitMinPVP.value)) {
            newConflicts.push(`Conflito P/VP: Entrada (< ${entryMaxPVP.value}) deve ser menor que Saída (> ${exitMinPVP.value}).`);
        }

        setConflicts(newConflicts);
    }, [rules]);

    return (
        <div className="fu-card" style={{ minHeight: '450px', display: 'flex', flexDirection: 'column' }}>
            <h3 className="fu-title-sm" style={{ marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sliders size={18} /> Construtor de Estratégia
            </h3>

            {/* Tabs */}
            <div style={{ display: 'flex', gap: '5px', marginBottom: '15px', borderBottom: '1px solid #333' }}>
                <button
                    className={`tab-btn ${activeTab === 'entry' ? 'active' : ''}`}
                    onClick={() => setActiveTab('entry')}
                    style={{ color: activeTab === 'entry' ? 'var(--color-accent-gold)' : '#666' }}
                >
                    Regras de Entrada
                </button>
                <button
                    className={`tab-btn ${activeTab === 'exit' ? 'active' : ''}`}
                    onClick={() => setActiveTab('exit')}
                    style={{ color: activeTab === 'exit' ? 'var(--color-danger)' : '#666' }}
                >
                    Regras de Saída
                </button>
            </div>

            {/* Logic Toggle */}
            <div style={{ marginBottom: '15px', display: 'flex', justifyContent: 'center' }}>
                <LogicToggle
                    value={activeTab === 'entry' ? entryLogic : exitLogic}
                    onChange={activeTab === 'entry' ? setEntryLogic : setExitLogic}
                    type={activeTab}
                />
            </div>

            {/* Dynamic Rules List */}
            <div style={{ flex: 1, overflowY: 'auto', paddingRight: '4px' }}>
                <div className="params-list animate-fade-in">
                    {rules[activeTab].map(rule => (
                        <div key={rule.id} className="rule-row" style={{
                            display: 'grid',
                            gridTemplateColumns: '1.5fr 1fr 0.8fr auto',
                            gap: '8px',
                            marginBottom: '8px',
                            alignItems: 'center',
                            backgroundColor: '#111',
                            padding: '6px',
                            borderRadius: '6px',
                            border: '1px solid #222'
                        }}>
                            {/* Metric Selector */}
                            <select
                                value={rule.metric}
                                onChange={e => updateRule(activeTab, rule.id, 'metric', e.target.value)}
                                style={{ background: 'transparent', color: '#fff', border: 'none', outline: 'none', fontSize: '0.85rem', width: '100%' }}
                            >
                                {METRICS.map(m => <option key={m.id} value={m.id}>{m.label}</option>)}
                            </select>

                            {/* Operator Selector */}
                            <select
                                value={rule.operator}
                                onChange={e => updateRule(activeTab, rule.id, 'operator', e.target.value)}
                                style={{ background: 'transparent', color: '#aaa', border: 'none', outline: 'none', fontSize: '0.85rem', textAlign: 'center' }}
                            >
                                {OPERATORS.map(op => <option key={op.id} value={op.id}>{op.label}</option>)}
                            </select>

                            {/* Value Input */}
                            <div style={{ display: 'flex', alignItems: 'center' }}>
                                <input
                                    type="number"
                                    value={rule.value}
                                    onChange={e => updateRule(activeTab, rule.id, 'value', e.target.value)}
                                    style={{
                                        background: '#222',
                                        color: activeTab === 'entry' ? 'var(--color-accent-gold)' : 'var(--color-danger)',
                                        border: 'none',
                                        borderRadius: '3px',
                                        padding: '4px',
                                        width: '100%',
                                        fontSize: '0.9rem',
                                        textAlign: 'right'
                                    }}
                                />
                            </div>

                            {/* Delete Button */}
                            <button
                                onClick={() => removeRule(activeTab, rule.id)}
                                style={{ background: 'transparent', border: 'none', color: '#444', cursor: 'pointer', padding: '4px' }}
                                className="delete-btn"
                            >
                                <Trash2 size={14} />
                            </button>
                        </div>
                    ))}

                    <button
                        onClick={() => addRule(activeTab)}
                        style={{
                            width: '100%',
                            padding: '8px',
                            background: 'rgba(255,255,255,0.03)',
                            border: '1px dashed #333',
                            borderRadius: '6px',
                            color: '#666',
                            cursor: 'pointer',
                            fontSize: '0.85rem',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '6px',
                            transition: 'all 0.2s'
                        }}
                        className="add-btn"
                    >
                        <Plus size={14} /> Adicionar Regra
                    </button>
                </div>
            </div>

            {/* Validation Feedback */}
            {conflicts.length > 0 && (
                <div style={{
                    marginTop: '15px',
                    padding: '10px',
                    borderRadius: '4px',
                    backgroundColor: 'rgba(231, 76, 60, 0.15)',
                    border: '1px solid var(--color-danger)',
                    fontSize: '0.85rem',
                    color: '#ff6b6b'
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '5px', fontWeight: 'bold' }}>
                        <AlertTriangle size={14} /> Conflito Detectado:
                    </div>
                    {conflicts.map((msg, i) => (
                        <div key={i} style={{ marginBottom: '2px' }}>• {msg}</div>
                    ))}
                </div>
            )}

            <div style={{ marginTop: 'auto', paddingTop: '15px' }}>
                <button
                    onClick={() => onRun && onRun({ rules, logic: { entry: entryLogic, exit: exitLogic } })}
                    style={{
                        width: '100%',
                        padding: '12px',
                        background: 'var(--color-accent-gold)',
                        color: '#000',
                        border: 'none',
                        borderRadius: '6px',
                        fontWeight: 'bold',
                        cursor: 'pointer',
                        fontSize: '0.95rem',
                        transition: 'opacity 0.2s'
                    }}
                >
                    Simular Estratégia
                </button>
            </div>

            <style>{`
                .tab-btn {
                    background: none;
                    border: none;
                    padding: 8px 12px;
                    cursor: pointer;
                    font-weight: 500;
                    border-bottom: 2px solid transparent;
                    transition: all 0.2s;
                }
                .tab-btn.active {
                    border-bottom-color: currentColor;
                }
                .delete-btn:hover { color: var(--color-danger) !important; }
                .add-btn:hover { background: rgba(255,255,255,0.08) !important; color: #fff !important; border-color: #666 !important; }
            `}</style>
        </div>
    );
};

const LogicToggle = ({ value, onChange, type }) => (
    <div style={{ display: 'flex', items: 'center', backgroundColor: '#111', borderRadius: '20px', padding: '4px', border: '1px solid #333' }}>
        <button
            onClick={() => onChange('AND')}
            style={{
                background: value === 'AND' ? (type === 'entry' ? 'var(--color-accent-gold)' : 'var(--color-danger)') : 'transparent',
                color: value === 'AND' ? '#000' : '#666',
                border: 'none',
                borderRadius: '16px',
                padding: '4px 12px',
                fontSize: '0.75rem',
                fontWeight: 'bold',
                cursor: 'pointer',
                transition: 'all 0.2s'
            }}
        >
            E (Todas)
        </button>
        <button
            onClick={() => onChange('OR')}
            style={{
                background: value === 'OR' ? (type === 'entry' ? 'var(--color-accent-gold)' : 'var(--color-danger)') : 'transparent',
                color: value === 'OR' ? '#000' : '#666',
                border: 'none',
                borderRadius: '16px',
                padding: '4px 12px',
                fontSize: '0.75rem',
                fontWeight: 'bold',
                cursor: 'pointer',
                transition: 'all 0.2s'
            }}
        >
            OU (Qualquer)
        </button>
    </div>
);

export default StrategyParameters;
