import React, { useState, useEffect, useRef } from 'react';
import { Plus, Trash2, ChevronDown, ChevronRight, ListPlus, Info, Copy } from 'lucide-react';

const INDICATORS = [
    { value: 'p_l', label: 'P/L (Preço/Lucro)', type: 'lower_pos', desc: 'Quanto MENOR, melhor (desconto). Evitar negativo.' },
    { value: 'p_vp', label: 'P/VP (Preço/Valor Patrimonial)', type: 'lower_pos', desc: 'Quanto MENOR, melhor (desconto).' },
    { value: 'dy', label: 'Dividend Yield (%)', type: 'higher', desc: 'Quanto MAIOR, melhor (pagamento de proventos).' },
    { value: 'roe', label: 'ROE (%)', type: 'higher', desc: 'Quanto MAIOR, melhor (rentabilidade).' },
    { value: 'net_margin', label: 'Margem Líquida (%)', type: 'higher', desc: 'Quanto MAIOR, melhor (eficiência).' },
    { value: 'avg_margin_5y', label: 'Margem Líq. Média 5 Anos (%)', type: 'higher', desc: 'Média dos últimos 5 anos. Estabilidade.' },
    { value: 'revenue_cagr_5y', label: 'CAGR Receita 5 Anos (%)', type: 'higher', desc: 'Crescimento anual composto da receita.' },
    { value: 'consecutive_profits', label: 'Anos de Lucro Consecutivo', type: 'higher', desc: 'Quantos anos seguidos sem prejuízo.' },
    { value: 'net_debt_ebitda', label: 'Dívida Líquida/EBITDA', type: 'lower_real', desc: 'Quanto MENOR, melhor (menos endividado).' },
    { value: 'ev_ebitda', label: 'EV/EBITDA', type: 'lower_pos', desc: 'Quanto MENOR, melhor (valor da empresa/geração de caixa).' }
];

const DEFAULT_VALUES = {
    p_l: { operator: 'range', value_min: 0, value_max: 12 },
    p_vp: { operator: '<', value: 3 },
    dy: { operator: '>', value: 6 },
    roe: { operator: '>', value: 10 },
    net_margin: { operator: '>', value: 12 },
    avg_margin_5y: { operator: '>', value: 6 },
    revenue_cagr_5y: { operator: '>', value: 6 },
    consecutive_profits: { operator: '>=', value: 5 },
    net_debt_ebitda: { operator: '<=', value: 3.5 },
    ev_ebitda: { operator: 'range', value_min: 0, value_max: 15 }
};

const OPERATORS = [
    { value: '>', label: 'Maior que (>)' },
    { value: '>=', label: 'Maior ou igual (>=)' },
    { value: '<', label: 'Menor que (<)' },
    { value: '<=', label: 'Menor ou igual (<=)' },
    { value: 'range', label: 'Faixa (Entre)' },
    { value: 'outsiderange', label: 'Fora da Faixa (Excluir)' }
];

// Custom Dual Range Slider Component
const DualRangeSlider = ({ min, max, valueMin, valueMax, onChange }) => {
    // Default range for indicators if not provided
    const rangeMin = min !== undefined ? min : -100;
    const rangeMax = max !== undefined ? max : 100;

    // Ensure values are within range
    const curMin = valueMin !== undefined ? valueMin : rangeMin;
    const curMax = valueMax !== undefined ? valueMax : rangeMax;

    const getPercent = (value) => Math.round(((value - rangeMin) / (rangeMax - rangeMin)) * 100);

    return (
        <div className="dual-slider-container">
            <div className="slider-track"></div>
            <div
                className="slider-range"
                style={{
                    left: `${getPercent(curMin)}%`,
                    width: `${getPercent(curMax) - getPercent(curMin)}%`
                }}
            ></div>
            <input
                type="range"
                min={rangeMin}
                max={rangeMax}
                value={curMin}
                onChange={(event) => {
                    const val = Math.min(Number(event.target.value), curMax - 1);
                    onChange(val, curMax);
                }}
                className="thumb thumb-left"
                style={{ zIndex: curMin > rangeMax - 10 ? 5 : 3 }}
            />
            <input
                type="range"
                min={rangeMin}
                max={rangeMax}
                value={curMax}
                onChange={(event) => {
                    const val = Math.max(Number(event.target.value), curMin + 1);
                    onChange(curMin, val);
                }}
                className="thumb thumb-right"
                style={{ zIndex: 4 }}
            />

            <div className="slider-values">
                <div className="slider-input-wrapper">
                    <input
                        type="number"
                        value={curMin}
                        onChange={(e) => onChange(Number(e.target.value), curMax)}
                        className="fu-input-sm"
                    />
                </div>
                <span style={{ color: 'var(--color-text-tertiary)' }}>até</span>
                <div className="slider-input-wrapper">
                    <input
                        type="number"
                        value={curMax}
                        onChange={(e) => onChange(curMin, Number(e.target.value))}
                        className="fu-input-sm"
                    />
                </div>
            </div>

            <style>{`
                .dual-slider-container {
                    position: relative;
                    width: 100%;
                    height: 50px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }
                .slider-track {
                    position: absolute;
                    border-radius: 3px;
                    top: 15px; /* center of top part */
                    height: 5px;
                    width: 100%;
                    background-color: var(--color-bg-surface);
                    border: 1px solid var(--color-border);
                    z-index: 1;
                }
                .slider-range {
                    position: absolute;
                    border-radius: 3px;
                    top: 15px;
                    height: 5px;
                    background-color: var(--color-accent-gold);
                    z-index: 2;
                }
                .thumb {
                    position: absolute;
                    top: 2px; /* Adjust to align thumb center with track */
                    height: 30px; /* Taller to capture clicks */
                    width: 100%;
                    pointer-events: none;
                    -webkit-appearance: none;
                    -moz-appearance: none;
                    background: none; /* Transparent track */
                    margin: 0;
                }
                .thumb::-webkit-slider-thumb {
                    pointer-events: all;
                    width: 16px;
                    height: 16px;
                    -webkit-appearance: none;
                    border-radius: 50%;
                    background-color: #fff;
                    border: 2px solid var(--color-accent-gold);
                    cursor: pointer;
                    margin-top: 5px; /* Adjust if needed */
                    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                }
                .thumb::-moz-range-thumb {
                    pointer-events: all;
                    width: 16px;
                    height: 16px;
                    border-radius: 50%;
                    background-color: #fff;
                    border: 2px solid var(--color-accent-gold);
                    cursor: pointer;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                }
                .slider-values {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-top: 35px; /* Space for slider */
                    gap: 10px;
                }
                .fu-input-sm {
                    background: var(--color-bg-main);
                    border: 1px solid var(--color-border);
                    color: var(--color-text-primary);
                    padding: 4px 8px;
                    border-radius: 4px;
                    width: 80px;
                    text-align: center;
                    font-size: 0.85rem;
                }
            `}</style>
        </div>
    );
};

const CriteriaRow = ({ criterion, onChange, onRemove }) => {
    const handleFieldChange = (field, value) => {
        let updates = { [field]: value };

        // Apply smart defaults when indicator changes
        if (field === 'indicator' && DEFAULT_VALUES[value]) {
            updates = { ...updates, ...DEFAULT_VALUES[value] };
        }

        onChange({ ...criterion, ...updates });
    };

    const currentIndicator = INDICATORS.find(i => i.value === criterion.indicator);

    // Determines reasonable defaults for slider based on indicator
    const getSliderDefaults = () => {
        // User requested standardized 0-100 range
        if (!currentIndicator) return { min: 0, max: 100 };

        // Exceptional cases that strictly need different scales can be handled here, 
        // but defaulting to 0-100 as requested for standard metrics (%, ratios)
        if (currentIndicator.value === 'consecutive_profits') return { min: 0, max: 10 }; // Years

        return { min: 0, max: 100 };
    };

    const sliderDefaults = getSliderDefaults();

    return (
        <div style={{ marginBottom: '15px', padding: '15px', background: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1.5fr auto', gap: '10px', alignItems: 'center', marginBottom: '10px' }}>
                {/* Indicator Select */}
                <select
                    value={criterion.indicator}
                    onChange={(e) => handleFieldChange('indicator', e.target.value)}
                    className="fu-input"
                    style={{ width: '100%' }}
                >
                    <option value="">Selecione Indicador...</option>
                    {INDICATORS.map(ind => (
                        <option key={ind.value} value={ind.value}>{ind.label}</option>
                    ))}
                </select>

                {/* Operator Select */}
                <select
                    value={criterion.operator}
                    onChange={(e) => handleFieldChange('operator', e.target.value)}
                    className="fu-input"
                >
                    {OPERATORS.map(op => (
                        <option key={op.value} value={op.value}>{op.label}</option>
                    ))}
                </select>

                <button onClick={onRemove} className="icon-button danger">
                    <Trash2 size={16} />
                </button>
            </div>

            {/* Description/Legend */}
            {currentIndicator && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px', fontSize: '0.8rem', color: currentIndicator.type.includes('lower') ? '#ef5350' : '#66bb6a' }}>
                    <Info size={14} />
                    <span>{currentIndicator.desc}</span>
                </div>
            )}

            {/* Value Inputs - Render Slider if 'range', else normal input */}
            <div style={{ padding: '0 5px' }}>
                {criterion.operator === 'range' || criterion.operator === 'outsiderange' ? (
                    <DualRangeSlider
                        min={sliderDefaults.min}
                        max={sliderDefaults.max}
                        valueMin={criterion.value_min}
                        valueMax={criterion.value_max}
                        onChange={(min, max) => {
                            handleFieldChange('value_min', min);
                            handleFieldChange('value_max', max);
                        }}
                        mode={criterion.operator === 'outsiderange' ? 'outside' : 'inside'}
                    />
                ) : (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <input
                            type="number"
                            value={criterion.value || ''}
                            onChange={(e) => handleFieldChange('value', e.target.value)}
                            placeholder="Valor"
                            className="fu-input"
                            style={{ width: '100%' }}
                        />
                        <span style={{ fontSize: '0.8rem', color: 'var(--color-text-tertiary)', whiteSpace: 'nowrap' }}>
                            {currentIndicator?.label.includes('(%)') ? '%' : ''}
                        </span>
                    </div>
                )}
            </div>
        </div>
    );
};

const LogicToggle = ({ value, onChange, label }) => (
    <div className="logic-toggle-container">
        {label && <span className="toggle-label">{label}</span>}
        <div className="toggle-group">
            <button
                className={`toggle-btn ${value === 'AND' ? 'active' : ''}`}
                onClick={() => onChange('AND')}
            >
                E (AND)
            </button>
            <button
                className={`toggle-btn ${value === 'OR' ? 'active' : ''}`}
                onClick={() => onChange('OR')}
            >
                OU (OR)
            </button>
        </div>
        <style>{`
            .logic-toggle-container {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .toggle-label {
                font-size: 0.85rem;
                color: var(--color-text-secondary);
            }
            .toggle-group {
                display: flex;
                background-color: var(--color-bg-surface);
                border: 1px solid var(--color-border);
                border-radius: var(--radius-sm);
                padding: 2px;
            }
            .toggle-btn {
                background: transparent;
                border: none;
                color: var(--color-text-tertiary);
                padding: 6px 14px;
                cursor: pointer;
                font-size: 0.8rem;
                font-weight: 600;
                border-radius: 2px;
                transition: all 0.2s;
            }
            .toggle-btn.active {
                background-color: var(--color-bg-main);
                color: var(--color-accent-gold);
                box-shadow: 0 1px 3px rgba(0,0,0,0.2);
            }
        `}</style>
    </div>
);

const CriteriaGroup = ({ group, onChange, onRemove, isFirst }) => {
    const updateCriterion = (index, newCrit) => {
        const newItems = [...group.items];
        newItems[index] = newCrit;
        onChange({ ...group, items: newItems });
    };

    const removeCriterion = (index) => {
        const newItems = group.items.filter((_, i) => i !== index);
        onChange({ ...group, items: newItems });
    };

    const addCriterion = () => {
        onChange({
            ...group,
            items: [...group.items, { indicator: 'p_l', operator: 'range', value_min: 0, value_max: 12 }]
        });
    };

    return (
        <div style={{ border: '1px dashed var(--color-border)', borderRadius: 'var(--radius-md)', padding: '20px', marginBottom: '20px', position: 'relative', background: 'rgba(20, 20, 20, 0.4)' }}>
            <div style={{ position: 'absolute', top: '-12px', left: '15px', background: 'var(--color-bg-card)', padding: '0 8px', fontSize: '0.8rem', fontWeight: 'bold', color: 'var(--color-text-secondary)', border: '1px solid var(--color-border)', borderRadius: '4px' }}>
                GRUPO {group.id}
            </div>

            {/* Group Logic Selector (Internal) */}
            <div style={{ marginBottom: '15px', display: 'flex', justifyContent: 'flex-end' }}>
                <LogicToggle
                    label="Lógica interna:"
                    value={group.logic}
                    onChange={(val) => onChange({ ...group, logic: val })}
                />
            </div>

            {group.items.map((item, idx) => (
                <CriteriaRow
                    key={idx}
                    criterion={item}
                    onChange={(c) => updateCriterion(idx, c)}
                    onRemove={() => removeCriterion(idx)}
                />
            ))}

            <div style={{ display: 'flex', gap: '10px', marginTop: '15px', alignItems: 'center', justifyContent: 'space-between' }}>
                <button onClick={addCriterion} className="fu-btn-secondary list-item" style={{ padding: '8px 16px', fontSize: '0.85rem' }}>
                    <Plus size={16} style={{ marginRight: '6px' }} /> Adicionar Regra
                </button>

                <button onClick={onRemove} className="fu-btn-text danger" style={{ fontSize: '0.85rem' }}>
                    Remover Grupo
                </button>
            </div>

            <style>{`
                .icon-button {
                    background: none;
                    border: none;
                    color: var(--color-text-tertiary);
                    cursor: pointer;
                    padding: 4px;
                    border-radius: 4px;
                    transition: all 0.2s;
                }
                .icon-button:hover {
                    background-color: rgba(255,255,255,0.1);
                    color: var(--color-text-primary);
                }
                .icon-button.danger:hover {
                    color: var(--color-negative);
                    background-color: rgba(239, 83, 80, 0.1);
                }
                .fu-btn-text.danger {
                    color: var(--color-text-tertiary);
                }
                .fu-btn-text.danger:hover {
                    color: var(--color-negative);
                }
            `}</style>
        </div>
    );
};

const CriteriaBuilder = ({ value, onChange }) => {
    // Value structure: [{ id: 1, logic: 'AND', items: [], groupLogic: 'AND' }]
    // Added 'groupLogic' to the groups? Or manage it as a separate state?
    // User requested "AND" between groups to be changeable to "OR".
    // Usually this logic is "Inter-group logic".

    // Simplification: We add `nextGroupLogic` to each group to determine how it connects to the next one?
    // Or we keep a global logic "All Groups AND" or "All Groups OR".
    // The user said: "Entre os grupo de regras voce esta colocando 'E' obrigatoriamente... pode ser 'OU' tambem."
    // Let's assume a global switch for simplicity first, or per-separator switch.
    // Per-separator is most flexible (Group 1 [AND] Group 2 [OR] Group 3).
    // Let's implement per-separator logic storage. We can store it in the group itself: `connectionOperator` (how it connects to the PREVIOUS or NEXT).
    // Let's store `connectionToNext` in each group (except last).

    const addGroup = () => {
        const newGroup = {
            id: (value.length > 0 ? Math.max(...value.map(g => g.id)) : 0) + 1,
            logic: 'AND',
            connectionToNext: 'AND', // Default connection
            items: [{ indicator: 'p_l', operator: 'range', value_min: 0, value_max: 12 }]
        };
        onChange([...value, newGroup]);
    };

    const updateGroup = (index, newGroup) => {
        const newGroups = [...value];
        newGroups[index] = newGroup;
        onChange(newGroups);
    };

    const removeGroup = (index) => {
        const newGroups = value.filter((_, i) => i !== index);
        onChange(newGroups);
    };

    return (
        <div className="criteria-builder">
            {value.map((group, idx) => (
                <div key={group.id}>
                    <CriteriaGroup
                        group={group}
                        onChange={(g) => updateGroup(idx, g)}
                        onRemove={() => removeGroup(idx)}
                    />

                    {idx < value.length - 1 && (
                        <div style={{ textAlign: 'center', margin: '20px 0', position: 'relative', display: 'flex', justifyContent: 'center' }}>
                            <div style={{ position: 'absolute', left: 0, top: '50%', width: '100%', height: '1px', background: 'var(--color-border)', zIndex: 0 }}></div>
                            <div style={{ position: 'relative', zIndex: 1, background: 'var(--color-bg-card)', padding: '0 10px' }}>
                                <LogicToggle
                                    value={group.connectionToNext || 'AND'}
                                    onChange={(val) => updateGroup(idx, { ...group, connectionToNext: val })}
                                />
                            </div>
                        </div>
                    )}
                </div>
            ))}

            <button onClick={addGroup} className="fu-btn-primary" style={{ width: '100%', marginTop: '10px', borderStyle: 'dashed', background: 'transparent', borderColor: 'var(--color-border)', color: 'var(--color-text-secondary)' }}>
                <ListPlus size={18} style={{ marginRight: '8px' }} /> Novo Grupo de Regras
            </button>
        </div>
    );
};

export default CriteriaBuilder;
