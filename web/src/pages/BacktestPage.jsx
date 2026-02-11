import React, { useState, useEffect, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Activity, RotateCcw } from 'lucide-react';

import StrategyInspector from '../components/StrategyInspector';
import SimulationWizard from '../components/SimulationWizard';
import SimulationResults from '../components/SimulationResults';

const BacktestPage = () => {
    // Mode: 'wizard' | 'running' | 'results'
    const [mode, setMode] = useState('wizard');
    const [config, setConfig] = useState(null);
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleRunSimulation = async (userConfig) => {
        setConfig(userConfig);
        setMode('running');
        setLoading(true);
        setResults(null); // Clear previous

        console.log("Starting Simulation with:", userConfig);

        try {
            const response = await fetch('http://localhost:8000/api/backtest/run', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userConfig),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Unknown Error' }));
                throw new Error(errorData.detail || 'Simulation Failed');
            }

            const data = await response.json();
            setResults(data);
            setMode('results');
        } catch (err) {
            console.error("Simulation Error:", err);
            alert(`Erro na simulação: ${err.message}`);
            setMode('wizard');
        } finally {
            setLoading(false);
        }
    };

    const handleReset = () => {
        setMode('wizard');
        setResults(null);
        setConfig(null);
    };

    const chartData = useMemo(() => {
        if (!results) return [];
        const scenarioKey = '21'; // Default to Monthly for now
        if (!results.scenarios || !results.scenarios[scenarioKey]) return [];

        const userHist = results.scenarios[scenarioKey].history;
        const benchmarks = results.benchmarks || {};
        const merged = {};

        // 1. User Strategy
        userHist.forEach(pt => {
            const d = pt.date.split('T')[0];
            if (!merged[d]) merged[d] = { date: d };
            merged[d]['Strategy'] = pt.total_value;
        });

        // 2. Benchmarks (Normalized)
        const initialCapital = userHist[0]?.total_value || 100000;
        ['IBOV', 'SELIC_Rate'].forEach(bench => {
            const bData = benchmarks[bench];
            if (bData && bData.length > 0) {
                const startVal = bData[0].value;
                bData.forEach(pt => {
                    const d = pt.date.split('T')[0];
                    if (merged[d]) {
                        merged[d][bench] = (pt.value / startVal) * initialCapital;
                    }
                });
            }
        });

        return Object.values(merged).sort((a, b) => new Date(a.date) - new Date(b.date));
    }, [results]);

    return (
        <div className="fu-container animate-fade-in" style={{ paddingBottom: '80px', paddingTop: '20px' }}>
            <header style={{ marginBottom: 'var(--spacing-8)', textAlign: 'center' }}>
                <h1 className="fu-title-lg">
                    <Activity style={{ verticalAlign: 'middle', marginRight: '10px' }} />
                    Simulador de Estratégias
                </h1>
                <p className="fu-text-secondary">Backtesting avançado com regras dinâmicas e análise de riscos.</p>
            </header>

            {mode === 'wizard' && (
                <div className="fu-card glow-blue" style={{ maxWidth: '800px', margin: '0 auto' }}>
                    <SimulationWizard onRun={handleRunSimulation} />
                </div>
            )}

            {mode === 'running' && (
                <div className="fu-card" style={{ textAlign: 'center', padding: '60px' }}>
                    <div className="loading-spinner" style={{ margin: '0 auto 20px', width: '30px', height: '30px', border: '3px solid #333', borderTop: '3px solid var(--color-accent-gold)', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
                    <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
                    <h3 className="fu-title-sm">Executando Simulação...</h3>
                    <p className="fu-text-secondary">Processando dados históricos dia-a-dia...</p>
                </div>
            )}

            {mode === 'results' && results && (
                <SimulationResults results={results} onReset={handleReset} />
            )}
        </div>
    );
};

export default BacktestPage;
