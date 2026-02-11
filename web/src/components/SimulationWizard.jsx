import React, { useState, useEffect } from 'react';
import { Play, Settings, Filter, DollarSign, PieChart, ArrowRight, Save, AlertCircle, Info, Copy, Calendar, X, CheckCircle, XCircle, Percent, Award, TrendingUp } from 'lucide-react';
import CriteriaBuilder from './CriteriaBuilder';
import MultiSelect from './MultiSelect';

// Removed static SECTORS constant

const SimulationWizard = ({ onRun }) => {
    const [step, setStep] = useState(1);
    const [availableTickers, setAvailableTickers] = useState([]);
    const [availableSectors, setAvailableSectors] = useState([]);
    const [config, setConfig] = useState({
        // Basic
        initial_capital: 100000,
        start_date: new Date(new Date().setFullYear(new Date().getFullYear() - 10)).toISOString().split('T')[0],
        end_date: '2024-12-31',
        min_liquidity: 1000000,
        exit_tolerance_margin: 25, // Default 25%

        // Structure
        min_assets: 8,
        max_assets: 12,
        min_sectors: 3,
        max_sectors: 6,
        max_assets_per_sector: 2,

        // Filters
        prohibited_assets: [],
        // Filters
        prohibited_assets: [],
        forced_assets: [], // Renamed from mandatory_assets to match usage
        prohibited_sectors: [], // New

        // Weights
        weight_strategy: 'equal', // equal | markowitz

        // Strategy
        entry_criteria: [
            { id: 1, logic: 'AND', connectionToNext: 'AND', items: [{ indicator: 'p_l', operator: 'range', value_min: 0, value_max: 12 }] }
        ],
        entry_score_weights: 'balanced', // p_l | roe | balanced | growth

        // Money Management
        rebalance_freq: 21, // Days
        contribution_freq: 21, // Days (Monthly)
        contribution_amount: 1000,
        grace_period_days: 5,

        stop_loss: 0,
        take_profit: 0
    });

    useEffect(() => {
        const loadData = async () => {
            try {
                // Try loading structured metadata first (Preferred)
                const resStruct = await fetch('/data/b3_stocks.json');
                if (resStruct.ok) {
                    const json = await resStruct.json();
                    const stockList = json.data || [];

                    if (stockList.length > 0) {
                        const tickers = stockList
                            .map(s => ({ value: s.ticker, label: s.ticker }))
                            .sort((a, b) => a.value.localeCompare(b.value));
                        setAvailableTickers(tickers);

                        const sectors = [...new Set(stockList.map(s => s.sector).filter(Boolean))].sort();
                        const sectorOptions = sectors.map(s => ({ value: s, label: s }));
                        setAvailableSectors(sectorOptions);
                        console.log("Loaded from b3_stocks:", tickers.length, "tickers,", sectorOptions.length, "sectors");
                        return;
                    }
                }
            } catch (e) {
                console.warn("Failed to load b3_stocks.json, trying fallback...", e);
            }

            // Fallback to data.json
            try {
                const resData = await fetch('/data.json');
                if (resData.ok) {
                    const data = await resData.json();
                    const tickers = Object.keys(data).sort().map(t => ({ value: t, label: t }));
                    setAvailableTickers(tickers);
                    console.log("Loaded from data.json (fallback):", tickers.length, "tickers");
                }
            } catch (e) {
                console.error("Critical: Failed to load any stock data.", e);
            }
        };

        loadData();
    }, []);

    const handleNext = () => setStep(step + 1);
    const handlePrev = () => setStep(step - 1);

    const [exitMode, setExitMode] = useState('auto_transpose'); // 'auto_transpose' | 'manual'

    // Auto-transpose logic whenever entry criteria changes, IF enabled
    // Auto-transpose logic whenever entry criteria changes, IF enabled
    useEffect(() => {
        if (exitMode === 'auto_transpose') {
            const margin = (config.exit_tolerance_margin || 0) / 100;

            const transposedGroups = config.entry_criteria.map(group => {
                const newItems = group.items.map(item => {
                    let newOp = item.operator;
                    let newVal = item.value;
                    let newValMin = item.value_min;
                    let newValMax = item.value_max;

                    // Apply Margin Logic
                    if (item.operator === 'range') {
                        newOp = 'outsiderange';
                        // Widen the "Safe Zone" means lowering min and raising max
                        if (newValMin !== undefined) newValMin = newValMin - (Math.abs(newValMin) * margin);
                        if (newValMax !== undefined) newValMax = newValMax + (Math.abs(newValMax) * margin);
                    } else if (item.operator === '>') {
                        newOp = '<';
                        // Entry > 10. Exit < 10. With margin, allow drop to 7.5. Exit < 7.5
                        if (newVal !== undefined) newVal = newVal - (Math.abs(newVal) * margin);
                    } else if (item.operator === '>=') {
                        newOp = '<';
                        if (newVal !== undefined) newVal = newVal - (Math.abs(newVal) * margin);
                    } else if (item.operator === '<') {
                        newOp = '>';
                        // Entry < 10. Exit > 10. With margin, allow rise to 12.5. Exit > 12.5
                        if (newVal !== undefined) newVal = newVal + (Math.abs(newVal) * margin);
                    } else if (item.operator === '<=') {
                        newOp = '>';
                        if (newVal !== undefined) newVal = newVal + (Math.abs(newVal) * margin);
                    }

                    return {
                        ...item,
                        operator: newOp,
                        value: newVal,
                        value_min: newValMin,
                        value_max: newValMax
                    };
                });
                return { ...group, logic: 'OR', connectionToNext: 'OR', items: newItems };
            });
            setConfig(prev => ({ ...prev, exit_criteria: transposedGroups }));
        }
    }, [config.entry_criteria, exitMode, config.exit_tolerance_margin]);

    const handleExitModeChange = (mode) => {
        setExitMode(mode);
        if (mode === 'manual') {
            // Check if we should clear or keep? User said "Limpar Critérios" (Clear)
            // "Coloque uma seleção Transpor da Entrada e Limpar Criterios de saida"
            setConfig(prev => ({ ...prev, exit_criteria: [] }));
        } else {
            // Trigger auto transpose immediately handled by useEffect dependency
        }
    };



    // Renders...
    const renderStep1_Basics = () => (
        <div className="wizard-step animate-fade-in">
            <h3 className="fu-title-sm" style={{ marginBottom: '20px', color: 'var(--color-text-primary)' }}>
                <Settings size={18} style={{ marginRight: '8px', verticalAlign: 'text-bottom' }} /> Configurações Gerais
            </h3>

            <div className="wizard-section">
                <h4 className="section-label">Parâmetros da Simulação</h4>
                <div className="grid-2-col">
                    <div className="form-group">
                        <label>Capital Inicial (R$)</label>
                        <NumberInput
                            value={config.initial_capital}
                            onChange={val => setConfig({ ...config, initial_capital: val })}
                            className="fu-input"
                        />
                    </div>
                    <div className="form-group">
                        <label>Início da Simulação</label>
                        <div style={{ position: 'relative' }}>
                            <input
                                type="date"
                                value={config.start_date}
                                onChange={e => setConfig({ ...config, start_date: e.target.value })}
                                className="fu-input date-input"
                                style={{ colorScheme: 'dark' }}
                            />
                            {/* Calendar icon fix handled by colorScheme: dark or specific CSS */}
                        </div>
                        <small style={{ color: 'var(--color-accent-gold)', marginTop: '5px', display: 'block', fontSize: '0.75rem' }}>
                            <Info size={12} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
                            Escolha um dia entre 2011 aos dias atuais.
                        </small>
                    </div>
                    <div className="form-group">
                        <label>Fim da Simulação</label>
                        <input
                            type="date"
                            value={config.end_date}
                            onChange={e => setConfig({ ...config, end_date: e.target.value })}
                            className="fu-input date-input"
                            style={{ colorScheme: 'dark' }}
                        />
                    </div>
                    <div className="form-group">
                        <label>Liquidez Mínima Diária (R$)</label>
                        <NumberInput
                            value={config.min_liquidity}
                            onChange={val => setConfig({ ...config, min_liquidity: val })}
                            className="fu-input"
                        />
                        <small style={{ color: 'var(--color-text-tertiary)', marginTop: '5px', display: 'block', fontSize: '0.75rem' }}>
                            Volume financeiro médio diário negociado. Filtra ações com pouca negociação para garantir que você consiga comprar/vender.
                        </small>
                    </div>
                </div>
            </div>

            <div className="wizard-section">
                <h4 className="section-label">Restrições de Diversificação</h4>
                <div className="grid-2-col">
                    <div className="form-group">
                        <label>Mín. Ativos</label>
                        <input type="number" value={config.min_assets} onChange={e => setConfig({ ...config, min_assets: parseInt(e.target.value) })} className="fu-input" />
                    </div>
                    <div className="form-group">
                        <label>Máx. Ativos</label>
                        <input type="number" value={config.max_assets} onChange={e => setConfig({ ...config, max_assets: parseInt(e.target.value) })} className="fu-input" />
                    </div>
                    <div className="form-group">
                        <label>Mín. Setores</label>
                        <input type="number" value={config.min_sectors} onChange={e => setConfig({ ...config, min_sectors: parseInt(e.target.value) })} className="fu-input" />
                    </div>
                    <div className="form-group">
                        <label>Máx. Setores</label>
                        <input type="number" value={config.max_sectors} onChange={e => setConfig({ ...config, max_sectors: parseInt(e.target.value) })} className="fu-input" />
                    </div>
                    <div className="form-group">
                        <label>Máx. Ativos por Setor</label>
                        <input type="number" value={config.max_assets_per_sector} onChange={e => setConfig({ ...config, max_assets_per_sector: parseInt(e.target.value) })} className="fu-input" />
                    </div>
                </div>

                <div className="grid-2-col" style={{ marginTop: '15px' }}>
                    <MultiSelect
                        label="Ativos Proibidos (Blacklist)"
                        options={availableTickers}
                        value={config.prohibited_assets}
                        onChange={(val) => setConfig({ ...config, prohibited_assets: val })}
                        placeholder="Selecione ativos..."
                    />

                    <MultiSelect
                        label="Ativos Obrigatórios (Forçar Compra)"
                        options={availableTickers}
                        value={config.forced_assets}
                        onChange={(val) => setConfig({ ...config, forced_assets: val })}
                        placeholder="Selecione ativos..."
                    />

                    <MultiSelect
                        label="Setores Proibidos"
                        options={availableSectors}
                        value={config.prohibited_sectors}
                        onChange={(val) => setConfig({ ...config, prohibited_sectors: val })}
                        placeholder="Selecione setores..."
                    />
                </div>
            </div>
        </div>
    );

    const renderStep2_Entry = () => (
        <div className="wizard-step animate-fade-in">
            <h3 className="fu-title-sm" style={{ marginBottom: '10px' }}>
                <Filter size={18} style={{ marginRight: '8px', verticalAlign: 'text-bottom' }} /> Critérios de Entrada (Compra)
            </h3>
            <p className="fu-text-secondary" style={{ fontSize: '0.9rem', marginBottom: '20px' }}>
                Defina as regras para selecionar ativos. O sistema irá pontuar e rankear os candidatos que passarem nestes filtros.
            </p>

            <div style={{ marginBottom: '20px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <span style={{ width: '100%', fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: '5px' }}>Templates Rápidos:</span>
                <button className="fu-btn-secondary" style={{ fontSize: '0.8rem', padding: '6px 12px', display: 'flex', alignItems: 'center' }} onClick={() => setConfig({
                    ...config,
                    entry_criteria: [{
                        id: 1, logic: 'AND', connectionToNext: 'AND', items: [
                            { indicator: 'p_vp', operator: '<', value: 0.7 },
                            { indicator: 'consecutive_profits', operator: '>=', value: 5 } // 5 Anos de lucro
                        ]
                    }],
                    entry_score_weights: 'value' // Suggest value ranking
                })}>
                    <Percent size={14} style={{ marginRight: '6px' }} /> Pontinha de Cigarro
                </button>

                <button className="fu-btn-secondary" style={{ fontSize: '0.8rem', padding: '6px 12px', display: 'flex', alignItems: 'center' }} onClick={() => setConfig({
                    ...config,
                    entry_criteria: [{
                        id: 1, logic: 'AND', connectionToNext: 'AND', items: [
                            { indicator: 'p_l', operator: '<', value: 15 },
                            { indicator: 'net_margin_avg_5y', operator: '>', value: 10 },
                            { indicator: 'dy', operator: '>', value: 6 }
                        ]
                    }],
                    entry_score_weights: 'balanced'
                })}>
                    <Award size={14} style={{ marginRight: '6px' }} /> Bom, Bonito e Barato
                </button>

                <button className="fu-btn-secondary" style={{ fontSize: '0.8rem', padding: '6px 12px', display: 'flex', alignItems: 'center' }} onClick={() => setConfig({
                    ...config,
                    entry_criteria: [{
                        id: 1, logic: 'AND', connectionToNext: 'AND', items: [
                            { indicator: 'revenue_cagr_5y', operator: '>', value: 10 },
                            { indicator: 'avg_margin_5y', operator: '>', value: 10 },
                            { indicator: 'consecutive_profits', operator: '>=', value: 5 } // 5 Anos de lucro
                        ]
                    }],
                    entry_score_weights: 'growth'
                })}>
                    <TrendingUp size={14} style={{ marginRight: '6px' }} /> Crescimento e Lucro
                </button>
            </div>

            <div style={{ background: 'var(--color-bg-surface-hover)', padding: '20px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                <CriteriaBuilder
                    value={config.entry_criteria}
                    onChange={(val) => setConfig({ ...config, entry_criteria: val })}
                />
            </div>

            <div className="fu-alert note" style={{ marginTop: '20px', display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                <AlertCircle size={18} style={{ color: 'var(--color-accent-gold)', marginTop: '2px' }} />
                <small style={{ color: 'var(--color-text-secondary)' }}>
                    <strong>Nota de Ranking:</strong> Ativos são automaticamente pontuados com base nos indicadores escolhidos (Melhores indicadores = Menor pontuação).
                    Indicadores usados aqui na entrada têm peso 3x na nota final.
                </small>
            </div>
        </div>
    );

    const renderStep3_Exit = () => (
        <div className="wizard-step animate-fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <h3 className="fu-title-sm" style={{ marginBottom: 0 }}>
                    <ArrowRight size={18} style={{ marginRight: '8px', verticalAlign: 'text-bottom' }} /> Critérios de Saída (Venda)
                </h3>

                {/* Custom Toggle for Exit Mode */}
                <div style={{ display: 'flex', background: 'var(--color-bg-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', padding: '2px' }}>
                    <button
                        onClick={() => handleExitModeChange('auto_transpose')}
                        style={{
                            background: exitMode === 'auto_transpose' ? 'var(--color-bg-main)' : 'transparent',
                            color: exitMode === 'auto_transpose' ? 'var(--color-accent-gold)' : 'var(--color-text-tertiary)',
                            border: 'none',
                            padding: '6px 14px',
                            borderRadius: '2px',
                            cursor: 'pointer',
                            fontSize: '0.8rem',
                            fontWeight: 600,
                            boxShadow: exitMode === 'auto_transpose' ? '0 1px 3px rgba(0,0,0,0.2)' : 'none',
                            transition: 'all 0.2s',
                            display: 'flex', alignItems: 'center', gap: '6px'
                        }}
                    >
                        <Copy size={12} /> Transpor da Entrada
                    </button>
                    <button
                        onClick={() => handleExitModeChange('manual')}
                        style={{
                            background: exitMode === 'manual' ? 'var(--color-bg-main)' : 'transparent',
                            color: exitMode === 'manual' ? 'var(--color-accent-gold)' : 'var(--color-text-tertiary)',
                            border: 'none',
                            padding: '6px 14px',
                            borderRadius: '2px',
                            cursor: 'pointer',
                            fontSize: '0.8rem',
                            fontWeight: 600,
                            boxShadow: exitMode === 'manual' ? '0 1px 3px rgba(0,0,0,0.2)' : 'none',
                            transition: 'all 0.2s'
                        }}
                    >
                        Manual / Limpar
                    </button>
                </div>
            </div>

            <p className="fu-text-secondary" style={{ fontSize: '0.9rem', marginBottom: '20px' }}>
                Defina quando vender o ativo. <br />
                {exitMode === 'auto_transpose' ? (
                    <div style={{ background: 'var(--color-bg-surface)', padding: '10px', borderRadius: '4px', marginTop: '10px', borderLeft: '3px solid var(--color-accent-gold)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-accent-gold)', marginBottom: '5px', fontWeight: 600 }}>
                            <Info size={14} /> Modo Automático Ativo
                        </div>
                        <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                            As regras de saída são geradas invertendo a entrada. Recomendamos aplicar uma margem de segurança para evitar operações desnecessárias causadas por pequenas oscilações.
                        </p>

                        <div style={{ marginTop: '10px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <label style={{ fontSize: '0.85rem', color: 'var(--color-text-primary)' }}>Margem de Tolerância (%):</label>
                            <input
                                type="number"
                                value={config.exit_tolerance_margin}
                                onChange={(e) => setConfig({ ...config, exit_tolerance_margin: parseFloat(e.target.value) })}
                                className="fu-input"
                                style={{ width: '80px', padding: '4px 8px' }}
                            />
                            <span style={{ fontSize: '0.8rem', color: 'var(--color-text-tertiary)' }}>
                                (Expande os limites em {config.exit_tolerance_margin}%)
                            </span>
                        </div>
                    </div>
                ) : (
                    <small style={{ color: 'var(--color-text-tertiary)' }}>
                        Modo manual: Defina suas próprias regras de saída.
                    </small>
                )}
            </p>

            <div style={{
                background: 'var(--color-bg-surface-hover)',
                padding: '20px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--color-border)',
                // Removed opacity and pointerEvents to allow editing even in auto mode
            }}>
                <CriteriaBuilder
                    value={config.exit_criteria}
                    onChange={(val) => setConfig({ ...config, exit_criteria: val })}
                />
            </div>
        </div>
    );

    const renderStep4_Management = () => (
        <div className="wizard-step animate-fade-in">
            <h3 className="fu-title-sm" style={{ marginBottom: '20px' }}>
                <DollarSign size={18} style={{ marginRight: '8px', verticalAlign: 'text-bottom' }} /> Gestão de Capital e Rebalanceamento
            </h3>

            <div className="wizard-section">
                <div className="grid-2-col">
                    <div className="form-group">
                        <label>Frequência de Rebalanceamento</label>
                        <select
                            value={config.rebalance_freq}
                            onChange={e => setConfig({ ...config, rebalance_freq: parseInt(e.target.value) })}
                            className="fu-input"
                        >
                            <option value="1">Diário (Todo pregão)</option>
                            <option value="5">Semanal</option>
                            <option value="21">Mensal</option>
                            <option value="63">Trimestral</option>
                            <option value="126">Semestral</option>
                            <option value="252">Anual</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label>Carência (Dias) para Desenquadramento</label>
                        <input
                            type="number"
                            value={config.grace_period_days}
                            onChange={e => setConfig({ ...config, grace_period_days: parseInt(e.target.value) })}
                            className="fu-input"
                        />
                        <small style={{ display: 'block', marginTop: '5px', color: 'var(--color-text-tertiary)', fontSize: '0.75rem' }}>
                            Tempo que o ativo pode ficar fora da regra antes de vender.
                        </small>
                    </div>
                </div>
            </div>

            <div className="wizard-section">
                <h4 className="section-label">Aportes Recorrentes</h4>
                <div className="grid-2-col">
                    <div className="form-group">
                        <label>Frequência</label>
                        <select
                            value={config.contribution_freq}
                            onChange={e => setConfig({ ...config, contribution_freq: parseInt(e.target.value) })}
                            className="fu-input"
                        >
                            <option value="0">Sem Aportes</option>
                            <option value="21">Mensal</option>
                            <option value="63">Trimestral</option>
                            <option value="126">Semestral</option>
                            <option value="252">Anual</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label>Valor do Aporte (R$)</label>
                        <NumberInput
                            value={config.contribution_amount}
                            onChange={val => setConfig({ ...config, contribution_amount: val })}
                            className="fu-input"
                            disabled={config.contribution_freq == 0}
                            style={{ opacity: config.contribution_freq == 0 ? 0.5 : 1 }}
                        />
                    </div>
                </div>
            </div>
        </div>
    );

    // State for review step
    const [reviewState, setReviewState] = useState({
        qualified: [],
        selected: [],
    });

    // State for Asset Detail Modal
    const [selectedAssetDetail, setSelectedAssetDetail] = useState(null);

    const generateReviewData = () => {
        // Mock data generation for review step
        // In real app, this would call a backend "dry-run" endpoint
        let pool = availableTickers.length > 0 ? availableTickers.map(t => t.value) : ['PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'BBAS3', 'WEGE3', 'ABEV3', 'JBSS3', 'SUZB3', 'BPAC1', 'ELET3', 'RENT3', 'PRIO3', 'UGPA3', 'GGBR4', 'CSAN3', 'RDOR3', 'RAIL3', 'SBSP3', 'VIBRA3'];

        // Filter prohibited
        pool = pool.filter(t => !config.prohibited_assets.some(p => p.value === t));

        // Ensure forced assets are in
        const forced = config.forced_assets.map(f => f.value);

        // Mock scoring logic (random for UI demo)
        const scored = pool.map(ticker => {
            // Mock indicators based on criteria for realism in modal
            const mockIndicators = {};
            config.entry_criteria.forEach(group => {
                group.items.forEach(item => {
                    // Generate a "passable" value usually, sometimes fail if not selected
                    let val = 0;
                    if (item.operator === 'range') val = (item.value_min + item.value_max) / 2;
                    else if (['>', '>='].includes(item.operator)) val = item.value * 1.2;
                    else if (['<', '<='].includes(item.operator)) val = item.value * 0.8;

                    // Add some noise
                    val = val * (0.9 + Math.random() * 0.2);
                    mockIndicators[item.indicator] = parseFloat(val.toFixed(2));
                });
            });

            return {
                ticker,
                score: Math.floor(Math.random() * 100), // Lower is better
                price: parseFloat((Math.random() * 50 + 10).toFixed(2)),
                sector: availableSectors.length > 0 ? availableSectors[Math.floor(Math.random() * availableSectors.length)].value : 'Outros',
                indicators: mockIndicators // Attach mock data
            };
        }).sort((a, b) => a.score - b.score); // Sort by score ASCENDING (Lower is better)

        // Selection Logic
        let selected = [];
        let qualified = [];

        // Add forced first
        scored.forEach(item => {
            if (forced.includes(item.ticker)) selected.push(item);
        });

        // Fill remaining with top scored
        for (let item of scored) {
            if (selected.length >= config.max_assets) break;
            if (!selected.includes(item)) selected.push(item);
        }

        // Rest go to qualified 
        qualified = scored.filter(item => !selected.includes(item)).slice(0, 20); // Show top 20 remaining

        // Calculate Position Sizing with Cash Sweep
        const totalCapital = config.initial_capital;
        let remainingCapital = totalCapital;

        // 1. Initial Equal Allocation (Floor to nearest 100)
        let assetsWithAllocation = selected.map(item => {
            const idealPerAsset = totalCapital / (selected.length || 1);
            let rawShares = Math.floor(idealPerAsset / item.price);
            let lotShares = Math.floor(rawShares / 100) * 100;
            if (lotShares === 0 && rawShares > 0 && idealPerAsset > item.price) lotShares = 100; // Minimum 100 if affordable

            return {
                ...item,
                shares: lotShares,
                currValue: lotShares * item.price
            };
        });

        // Update Remaining Capital
        remainingCapital -= assetsWithAllocation.reduce((acc, curr) => acc + curr.currValue, 0);

        // 2. Cash Sweep: Add extra lots to top ranked assets (Lower score is better)
        // Sort by score ascending to prioritize top picks
        assetsWithAllocation.sort((a, b) => a.score - b.score);

        let iter = 0;
        let purchasedMore = true;
        while (remainingCapital > 0 && purchasedMore && iter < 100) { // Limit iterations for safety
            purchasedMore = false;
            for (let i = 0; i < assetsWithAllocation.length; i++) {
                const asset = assetsWithAllocation[i];
                const costOfLot = asset.price * 100;

                if (remainingCapital >= costOfLot) {
                    asset.shares += 100;
                    asset.currValue += costOfLot;
                    remainingCapital -= costOfLot;
                    purchasedMore = true;
                }
            }
            iter++;
        }

        // Format for State
        const finalSelected = assetsWithAllocation.map(item => ({
            ...item,
            volume: item.currValue.toFixed(2)
        })).sort((a, b) => a.score - b.score); // Keep sorted by rank

        // Qualified remains simple
        const qualifiedWithEst = qualified.map(item => {
            const idealPerAsset = totalCapital / (selected.length || 1);
            return {
                ...item,
                shares: 0,
                volume: "0.00" // Not allocated
            };
        });

        setReviewState({
            selected: finalSelected,
            qualified: qualifiedWithEst
        });
    };

    // Toggle asset selection
    const toggleAssetSelection = (asset, isSelected) => {
        if (isSelected) {
            // Remove from selected, move to qualified
            setReviewState(prev => ({
                selected: prev.selected.filter(a => a.ticker !== asset.ticker),
                qualified: [...prev.qualified, asset].sort((a, b) => b.score - a.score)
            }));
        } else {
            // Move from qualified to selected (Check limit)
            if (reviewState.selected.length >= config.max_assets) {
                alert(`Máximo de ${config.max_assets} ativos atingido. Remova um para adicionar.`);
                return;
            }
            setReviewState(prev => ({
                qualified: prev.qualified.filter(a => a.ticker !== asset.ticker),
                selected: [...prev.selected, asset]
            }));
        }
    };

    // Handle manual share change
    const handleShareChange = (ticker, newShares) => {
        const shares = parseInt(newShares) || 0;
        setReviewState(prev => ({
            ...prev,
            selected: prev.selected.map(item => {
                if (item.ticker === ticker) {
                    return {
                        ...item,
                        shares: shares,
                        volume: (shares * item.price).toFixed(2)
                    };
                }
                return item;
            })
        }));
    };

    // Step 5 Review Render
    const renderStep5_Review = () => {
        const totalAllocated = reviewState.selected.reduce((acc, curr) => acc + parseFloat(curr.volume), 0);
        const remaining = config.initial_capital - totalAllocated;
        const isOverBudget = remaining < 0;

        return (
            <div className="wizard-step animate-fade-in">
                <h3 className="fu-title-sm" style={{ marginBottom: '10px' }}>
                    <PieChart size={18} style={{ marginRight: '8px', verticalAlign: 'text-bottom' }} /> Revisão da Carteira Inicial
                </h3>
                <p className="fu-text-secondary" style={{ fontSize: '0.9rem', marginBottom: '20px' }}>
                    Baseado nos critérios de entrada, estes são os ativos selecionados. Você pode ajustar manualmente antes de iniciar.
                </p>

                <div className="grid-2-col">
                    {/* Selected Box */}
                    <div style={{ background: 'var(--color-bg-surface)', padding: '15px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-accent-gold)' }}>
                        <h4 className="section-label" style={{ color: 'var(--color-accent-gold)', borderBottomColor: 'var(--color-accent-gold)' }}>
                            Carteira Selecionada ({reviewState.selected.length}/{config.max_assets})
                        </h4>
                        <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                            <table style={{ width: '100%', fontSize: '0.85rem', borderCollapse: 'collapse' }}>
                                <thead>
                                    <tr style={{ color: 'var(--color-text-secondary)', textAlign: 'left' }}>
                                        <th style={{ padding: '5px' }}>Ativo</th>
                                        <th>Preço</th>
                                        <th>Qtd</th>
                                        <th>Total</th>
                                        <th style={{ textAlign: 'center' }}>Ação</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {reviewState.selected.map(asset => (
                                        <tr key={asset.ticker} style={{ borderBottom: '1px solid var(--color-border)' }}>
                                            <td style={{ padding: '8px 5px', fontWeight: 600, cursor: 'pointer', color: 'var(--color-accent-gold)' }} onClick={() => setSelectedAssetDetail(asset)}>
                                                {asset.ticker}
                                            </td>
                                            <td>R$ {asset.price}</td>
                                            <td style={{ width: '80px' }}>
                                                <input
                                                    type="number"
                                                    value={asset.shares}
                                                    onChange={(e) => handleShareChange(asset.ticker, e.target.value)}
                                                    className="fu-input"
                                                    style={{ padding: '2px 5px', fontSize: '0.85rem', height: '26px' }}
                                                />
                                            </td>
                                            <td>R$ {asset.volume}</td>
                                            <td style={{ textAlign: 'center' }}>
                                                <button
                                                    onClick={() => toggleAssetSelection(asset, true)}
                                                    style={{ color: '#ef5350', background: 'none', border: 'none', cursor: 'pointer' }}
                                                    title="Excluir"
                                                >
                                                    <div style={{ width: '16px', height: '16px', border: '1px solid #ef5350', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>-</div>
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        <div style={{ marginTop: '10px', textAlign: 'right', fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
                            Disponível: <span style={{ color: isOverBudget ? '#ef5350' : 'var(--color-text-primary)' }}>R$ {remaining.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span> <br />
                            Total Alocado: <strong>R$ {totalAllocated.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</strong>
                        </div>
                    </div>

                    {/* Candidates Box */}
                    <div style={{ background: 'var(--color-bg-surface)', padding: '15px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                        <h4 className="section-label">Outros Candidatos Aprovados</h4>
                        <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                            <table style={{ width: '100%', fontSize: '0.85rem', borderCollapse: 'collapse' }}>
                                <thead>
                                    <tr style={{ color: 'var(--color-text-secondary)', textAlign: 'left' }}>
                                        <th style={{ padding: '5px' }}>Ativo</th>
                                        <th>Setor</th>
                                        <th>Score</th>
                                        <th style={{ textAlign: 'center' }}>Ação</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {reviewState.qualified.map(asset => (
                                        <tr key={asset.ticker} style={{ borderBottom: '1px solid var(--color-border)' }}>
                                            <td style={{ padding: '8px 5px', cursor: 'pointer', color: 'var(--color-text-primary)' }} onClick={() => setSelectedAssetDetail(asset)}>{asset.ticker}</td>
                                            <td style={{ fontSize: '0.8rem', color: 'var(--color-text-tertiary)' }}>{asset.sector}</td>
                                            <td>{asset.score}</td>
                                            <td style={{ textAlign: 'center' }}>
                                                <button
                                                    onClick={() => toggleAssetSelection(asset, false)}
                                                    style={{ color: 'var(--color-accent-green)', background: 'none', border: 'none', cursor: 'pointer' }}
                                                    title="Adicionar"
                                                >
                                                    <div style={{ width: '16px', height: '16px', border: '1px solid var(--color-accent-green)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>+</div>
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                {/* Asset Detail Modal */}
                {selectedAssetDetail && (
                    <div style={{
                        position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                        background: 'rgba(0,0,0,0.7)', zIndex: 1000,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        animation: 'fadeIn 0.2s'
                    }} onClick={() => setSelectedAssetDetail(null)}>
                        <div style={{
                            background: 'var(--color-bg-main)',
                            border: '1px solid var(--color-border)',
                            borderRadius: 'var(--radius-md)',
                            width: '90%', maxWidth: '500px',
                            padding: '20px',
                            position: 'relative'
                        }} onClick={e => e.stopPropagation()}>
                            <button
                                onClick={() => setSelectedAssetDetail(null)}
                                style={{ position: 'absolute', top: '10px', right: '10px', background: 'none', border: 'none', color: 'var(--color-text-tertiary)', cursor: 'pointer' }}
                            >
                                <X size={20} />
                            </button>

                            <h3 className="fu-title-sm" style={{ marginBottom: '15px' }}>
                                <span style={{ color: 'var(--color-accent-gold)' }}>{selectedAssetDetail.ticker}</span> - Detalhes
                            </h3>

                            <div style={{ marginBottom: '20px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                                <div>
                                    <small style={{ color: 'var(--color-text-tertiary)' }}>Preço Atual</small>
                                    <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>R$ {selectedAssetDetail.price}</div>
                                </div>
                                <div>
                                    <small style={{ color: 'var(--color-text-tertiary)' }}>Nota de Ranking</small>
                                    <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>{selectedAssetDetail.score}</div>
                                </div>
                                <div>
                                    <small style={{ color: 'var(--color-text-tertiary)' }}>Setor</small>
                                    <div>{selectedAssetDetail.sector}</div>
                                </div>
                            </div>

                            <h4 className="section-label">Critérios de Entrada</h4>
                            <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                                <table style={{ width: '100%', fontSize: '0.85rem' }}>
                                    <tbody>
                                        {config.entry_criteria.map(group => (
                                            group.items.map((item, idx) => {
                                                const assetVal = selectedAssetDetail.indicators && selectedAssetDetail.indicators[item.indicator];
                                                // Check passes logic (mock)
                                                let passes = true;
                                                if (item.operator === 'range') passes = assetVal >= item.value_min && assetVal <= item.value_max;

                                                // Format Criteria Text
                                                let criteriaText = "";
                                                if (item.operator === 'range') criteriaText = `Entre ${item.value_min} e ${item.value_max}`;
                                                else if (item.operator === '>') criteriaText = `> ${item.value}`;
                                                else if (item.operator === '>=') criteriaText = `>= ${item.value}`;
                                                else if (item.operator === '<') criteriaText = `< ${item.value}`;
                                                else if (item.operator === '<=') criteriaText = `<= ${item.value}`;

                                                return (
                                                    <tr key={idx} style={{ borderBottom: '1px solid var(--color-divide)' }}>
                                                        <td style={{ padding: '8px 0' }}>
                                                            <div style={{ color: 'var(--color-text-secondary)', fontWeight: 500 }}>{item.indicator.toUpperCase()}</div>
                                                            <div style={{ color: 'var(--color-text-tertiary)', fontSize: '0.75rem' }}>Critério: {criteriaText}</div>
                                                        </td>
                                                        <td style={{ padding: '8px 0', textAlign: 'right', verticalAlign: 'middle' }}>
                                                            <span style={{ marginRight: '10px', fontWeight: 'bold' }}>
                                                                {assetVal !== undefined ? assetVal.toFixed(2) : '-'}
                                                            </span>
                                                            {/* Visual Indicator of Pass/Fail (Mock) */}
                                                            <CheckCircle size={14} color="var(--color-accent-green)" style={{ verticalAlign: 'middle' }} />
                                                        </td>
                                                    </tr>
                                                );
                                            })
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        );
    };

    const mapFreqToString = (freq) => {
        if (freq == 252) return 'yearly';
        if (freq == 63) return 'quarterly';
        if (freq == 21) return 'monthly';
        if (freq == 5) return 'weekly'; // Not in backend explicitly but good to have
        if (freq == 0 || freq == '0') return 'none';
        return 'monthly'; // Default
    };

    const handleRunClick = () => {
        const payload = {
            ...config,
            blacklisted_assets: config.prohibited_assets.map(a => a.value),
            forced_assets: config.forced_assets.map(a => a.value),
            initial_portfolio: reviewState.selected.map(a => ({
                ticker: a.ticker,
                shares: a.shares,
                price: a.price,
                volume: parseFloat(a.volume) || 0,
                score: a.score
            })),
            rebalance_period: mapFreqToString(config.rebalance_freq),
            contribution_frequency: mapFreqToString(config.contribution_freq),
            entry_logic: "AND",
            exit_mode: exitMode
        };
        onRun(payload);
    };

    return (
        <div className="simulation-wizard active-step">
            {/* Steps Indicator */}
            <div className="steps-indicator" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '30px', padding: '0 10px', position: 'relative' }}>
                {/* Progress Bar Background */}
                <div style={{ position: 'absolute', bottom: '0', left: '10px', right: '10px', height: '2px', background: 'var(--color-border)', zIndex: 0 }}></div>

                {['Configuração', 'Entrada', 'Saída', 'Gestão'].map((label, idx) => (
                    <div key={idx} style={{
                        position: 'relative',
                        zIndex: 1,
                        opacity: step === idx + 1 ? 1 : (step > idx + 1 ? 0.8 : 0.4),
                        fontWeight: step === idx + 1 ? 'bold' : 'normal',
                        color: step === idx + 1 ? 'var(--color-accent-gold)' : 'var(--color-text-primary)',
                        borderBottom: step === idx + 1 ? '2px solid var(--color-accent-gold)' : '2px solid transparent',
                        paddingBottom: '8px',
                        cursor: 'pointer',
                        transition: 'all 0.3s'
                    }} onClick={() => {
                        if (idx + 1 === 5) generateReviewData(); // If clicking review direct (not implemented in loop but logic holds)
                        setStep(idx + 1);
                    }}>
                        <span style={{ marginRight: '5px' }}>{idx + 1}.</span>
                        <span className="step-label">{label}</span>
                    </div>
                ))}
                {/* Review Step Indicator (Hidden from loop but shown if active) */}
                <div style={{
                    position: 'relative',
                    zIndex: 1,
                    opacity: step === 5 ? 1 : 0.4,
                    fontWeight: step === 5 ? 'bold' : 'normal',
                    color: step === 5 ? 'var(--color-accent-gold)' : 'var(--color-text-primary)',
                    borderBottom: step === 5 ? '2px solid var(--color-accent-gold)' : '2px solid transparent',
                    paddingBottom: '8px',
                    cursor: 'pointer',
                    transition: 'all 0.3s',
                    display: step === 5 ? 'block' : 'none' // Only show when active or can assume it's part of flow
                }}>
                    <span style={{ marginRight: '5px' }}>5.</span>
                    <span className="step-label">Revisão</span>
                </div>

            </div>

            {/* Step Content */}
            <div className="step-content" style={{ minHeight: '400px' }}>
                {step === 1 && renderStep1_Basics()}
                {step === 2 && renderStep2_Entry()}
                {step === 3 && renderStep3_Exit()}
                {step === 4 && renderStep4_Management()}
                {step === 5 && renderStep5_Review()}
            </div>

            {/* Navigation Actions */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '40px', borderTop: '1px solid var(--color-border)', paddingTop: '20px' }}>
                <button
                    onClick={handlePrev}
                    disabled={step === 1}
                    className="fu-btn-secondary"
                    style={{ visibility: step === 1 ? 'hidden' : 'visible' }}
                >
                    Voltar
                </button>

                {step < 5 ? (
                    <button onClick={() => {
                        if (step === 4) {
                            generateReviewData();
                            setStep(5);
                        } else {
                            handleNext();
                        }
                    }} className="fu-btn-primary">
                        Próximo <ArrowRight size={16} style={{ marginLeft: '5px' }} />
                    </button>
                ) : (
                    <button className="fu-btn-primary glow-green" onClick={handleRunClick}>
                        <Play size={16} style={{ marginRight: '5px' }} /> Iniciar Simulação
                    </button>
                )}
            </div>

            <style>{`
                .wizard-section {
                    margin-bottom: 25px;
                }
                .section-label {
                    font-size: 0.85rem;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    color: var(--color-text-tertiary);
                    margin-bottom: 12px;
                    border-bottom: 1px solid var(--color-divide);
                    padding-bottom: 5px;
                }
                .grid-2-col {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                }
                .form-group label {
                    display: block;
                    font-size: 0.85rem;
                    color: var(--color-text-secondary);
                    margin-bottom: 6px;
                    font-weight: 500;
                }
                .help-text {
                    font-size: 0.75rem;
                    color: var(--color-text-tertiary);
                    margin-top: 4px;
                    display: block;
                }
                .fu-input {
                    background-color: var(--color-bg-main);
                    border: 1px solid var(--color-border);
                    color: var(--color-text-primary);
                    padding: 10px;
                    border-radius: var(--radius-sm);
                    font-family: var(--font-family-sans);
                    font-size: 0.95rem;
                    width: 100%;
                    transition: border-color 0.2s;
                }
                .fu-input:focus {
                    outline: none;
                    border-color: var(--color-accent-gold);
                }
                .fu-btn-primary {
                    background-color: var(--color-accent-gold);
                    color: #000;
                    border: none;
                    padding: 10px 24px;
                    border-radius: var(--radius-sm);
                    font-weight: 600;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    transition: all 0.2s;
                }
                .fu-btn-primary:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 4px 12px rgba(212, 175, 55, 0.2);
                }
                .fu-btn-secondary {
                    background-color: transparent;
                    border: 1px solid var(--color-border);
                    color: var(--color-text-primary);
                    padding: 10px 20px;
                    border-radius: var(--radius-sm);
                    cursor: pointer;
                    font-weight: 500;
                    transition: all 0.2s;
                }
                .fu-btn-secondary:hover {
                    background-color: var(--color-bg-surface-hover);
                    border-color: var(--color-text-secondary);
                }
                
                @media (max-width: 600px) {
                    .grid-2-col { grid-template-columns: 1fr; }
                    .step-label { display: none; }
                }
                .wizard-step, .wizard-section, .grid-2-col, .form-group {
                    overflow: visible !important;
                }
            `}</style>
        </div>
    );
};

const NumberInput = ({ value, onChange, className, disabled, style }) => {
    const handleChange = (e) => {
        // Remove dots (thousands) and replace comma with dot (decimal) if any
        // But for Capital/Liquidity we usually want integers.
        // Let's assume standard integer input with dots.
        const rawValue = e.target.value.replace(/\./g, '');

        if (/^\d*$/.test(rawValue)) { // Integers only
            onChange(rawValue === '' ? 0 : parseInt(rawValue, 10));
        }
    };

    const displayValue = value !== undefined && value !== null ? value.toLocaleString('pt-BR') : '';

    return (
        <input
            type="text"
            className={className}
            value={displayValue}
            onChange={handleChange}
            disabled={disabled}
            style={style}
        />
    );
};

export default SimulationWizard;
