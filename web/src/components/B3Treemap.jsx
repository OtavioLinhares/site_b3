import React, { useState, useEffect, useMemo, useRef } from 'react';
import { ResponsiveContainer, Treemap, Tooltip } from 'recharts';

// --- Constants for Design ---
const NAME_MAPPING = {
    'Petróleo, Gás e Biocombustíveis': 'Petróleo e Gás',
    'Serv. Méd. Hospit. Análises e Diagnósticos': 'Saúde',
    'Serv.Méd.Hospit. Análises e Diagnósticos': 'Saúde',
    'Serv.Méd.Hospit. Análises e Diagnósticos ': 'Saúde',
    'Serv.Med.Hospit. Anílises e Diagnosticos': 'Saúde',
    'Serv.Med.Hospit. Análises e Diagnósticos': 'Saúde',
    'Ser.Med.Hospit. Analise e Diagnosticos': 'Saúde',
    'Ser.Med.Hospt. Analise e Diagnosticos': 'Saúde',
    'Hospit. Análises e Diagnósticos': 'Saúde',
    'Ser.Med.Hospit. Analises e Diagnosticos': 'Saúde',
    'Ser.Med.Hospt. Analises e Diagnosticos': 'Saúde',
    'Exploração de Imóveis': 'Imóveis',
    'Máquinas e Equipamentos': 'Máquinas',
    'Produtos de Uso Pessoal e de Limpeza': 'Uso Pessoal',
    'Tecidos, Vestuário e Calçados': 'Vestuário',
    'Previdência e Seguros': 'Seguros',
    'Siderurgia e Metalurgia': 'Siderurgia',
    'Intermediários Financeiros': 'Financeiro',
    'Utilidade Pública': 'Utilidade',
    'Telecomunicações': 'Telecom',
    'Construção e Engenharia': 'Construção',
    'Transporte': 'Logística',
    'Comércio e Distribuição': 'Varejo',
    'Comércio': 'Varejo',
    'Automóveis e Motocicletas': 'Automotivo',
    'Serviços Financeiros Diversos': 'Serv. Financeiros',
    'Programas e Serviços': 'TI',
    'Computadores e Equipamentos': 'Hardware',
    'Holdings Diversificadas': 'Holdings'
};

const simplifyName = (name) => {
    if (!name) return name;
    const trimmed = name.trim();
    return NAME_MAPPING[trimmed] || trimmed;
};

// Sober, elegant palette (Gemstone Tones)
const getPLColor = (pl) => {
    if (pl < 0) return '#7f1d1d'; // Deep Burgundy (Red 900) - Alert but sober
    if (pl === 0) return '#2d3748'; // Cool Dark Grey

    // Elegant Gradient: Deep Emeralds for "Value" stocks
    // We use rich gemstone greens, avoiding neon/lime variations.
    if (pl <= 6) return '#047857';  // Emerald 700 (Rich Jewel Green) - The "Best" logic
    if (pl <= 12) return '#065f46'; // Emerald 800 (Darker Jewel Green)
    if (pl <= 18) return '#064e3b'; // Emerald 900 (Deepest Green)

    // Transition to extensive/neutral (Slate/Indigo tones)
    if (pl <= 25) return '#334155'; // Slate 700 (Neutral Dark Blue-Grey)
    return '#1e1b4b'; // Indigo 950 (Midnight Blue) - Very expensive/Premium
};

// Contrast logic: returns white or black depending on background luminance
const getContrastColor = (hexColor) => {
    if (!hexColor || hexColor.length < 6) return '#FFFFFF';
    const hex = hexColor.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance > 0.6 ? '#000000' : '#FFFFFF';
};

// --- Customized Content Component for Treemap ---
const CustomContent = (props) => {
    const { x, y, width, height, name, p_l, net_margin, roe, roic, dy } = props;
    if (!name || width < 40 || height < 20) return null;

    const simpleName = simplifyName(name);
    const words = simpleName.split(' ');
    const linesArr = [];
    let currentLine = '';

    // Narrow boxes get wrapping
    if (simpleName.length > 8 && width < 120) {
        words.forEach(w => {
            if ((currentLine + w).length > 7) {
                if (currentLine) linesArr.push(currentLine.trim());
                currentLine = w + ' ';
            } else {
                currentLine += w + ' ';
            }
        });
        if (currentLine) linesArr.push(currentLine.trim());
    } else {
        linesArr.push(simpleName);
    }

    // Proportional font sizing based on box dimensions
    // User requested larger font for specific sectors
    const boostedSectors = ['Construção', 'Varejo', 'Alimentos Processados', 'Agua e Saneamento', 'Serviços Diversos', 'Saúde'];
    const isBoosted = boostedSectors.includes(simpleName);

    let fontSizeN = Math.max(10, Math.min(18, width / (linesArr[0].length * 0.7 + 2), height / 4));
    if (isBoosted && width > 100) fontSizeN = Math.min(22, fontSizeN * 1.25);

    const fontSizeM = Math.max(9, fontSizeN * 0.85);
    const textColor = getContrastColor(getPLColor(p_l));
    const showM = width > 75 && height > 55;

    // Tightened vertical stacking (reduced gaps to avoid 'empty line' feel)
    const nameYBase = showM ? (linesArr.length > 1 ? -28 : -14) : (linesArr.length > 1 ? -10 : 0);

    // Fallback Margem for Banks (Net Margin 0% -> ROE)
    // As per user request: "finanças e seguros não esta apresentando margem em nenhuma empresa"
    const displayMargin = (net_margin || (roe && p_l > 0 ? roe : 0)) * 100;

    return (
        <g style={{ cursor: 'pointer' }}>
            <rect
                x={x}
                y={y}
                width={width}
                height={height}
                style={{
                    fill: getPLColor(p_l),
                    stroke: '#0f172a',
                    strokeWidth: 1,
                }}
            />
            {width > 20 && height > 12 && (
                <g style={{ pointerEvents: 'none' }}>
                    {linesArr.map((line, i) => (
                        <text
                            key={i}
                            x={x + width / 2}
                            y={y + height / 2 + nameYBase + (i * (fontSizeN + 2))}
                            textAnchor="middle"
                            fill={textColor}
                            fontSize={fontSizeN}
                            fontWeight={900}
                            style={{
                                whiteSpace: 'pre',
                                textShadow: 'none' // Remove black shadow as requested
                            }}
                        >
                            {line}
                        </text>
                    ))}

                    {showM && (
                        <>
                            <text
                                x={x + width / 2}
                                y={y + height / 2 + (linesArr.length > 1 ? 12 : 6) + 2}
                                textAnchor="middle"
                                fill={textColor}
                                fontSize={fontSizeM}
                                fontWeight={700}
                                style={{
                                    opacity: 0.9,
                                    textShadow: 'none' // Remove black border from font
                                }}
                            >
                                {`P/L: ${p_l ? p_l.toFixed(1) : '-'}`}
                            </text>
                            <text
                                x={x + width / 2}
                                y={y + height / 2 + (linesArr.length > 1 ? 12 : 6) + fontSizeM + 6}
                                textAnchor="middle"
                                fill={textColor}
                                fontSize={fontSizeM}
                                fontWeight={700}
                                style={{
                                    opacity: 0.9,
                                    textShadow: 'none'
                                }}
                            >
                                {`M. Líq: ${displayMargin.toFixed(1)}%`}
                            </text>


                        </>
                    )}
                </g>
            )}
        </g>
    );
};

const B3Treemap = () => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [viewState, setViewState] = useState({ level: 'market', parent: null, subParent: null });
    const [selectedSectors, setSelectedSectors] = useState([]);
    const [showSectorFilter, setShowSectorFilter] = useState(false);
    const [sectorSearchTerm, setSectorSearchTerm] = useState('');

    // Controls State
    const [searchTerm, setSearchTerm] = useState('');
    const [highlightedTicker, setHighlightedTicker] = useState(null);
    const [showSuggestions, setShowSuggestions] = useState(false);

    // Top 15 Filters
    const [filterTop15, setFilterTop15] = useState(false);
    const [plFilter, setPlFilter] = useState({ min: 0, max: 20 });
    const [marginFilter, setMarginFilter] = useState({ min: 10, max: 100 }); // In %
    const [roeFilter, setRoeFilter] = useState({ min: 0, max: 100 }); // In %
    const [roicFilter, setRoicFilter] = useState({ min: 0, max: 100 }); // In %
    const [dyFilter, setDyFilter] = useState({ min: 0, max: 100 }); // In %
    const [sortPriority, setSortPriority] = useState('margin'); // 'margin' or 'pl'

    const searchRef = useRef(null);

    useEffect(() => {
        fetch(`${import.meta.env.BASE_URL}data/b3_stocks.json`)
            .then(res => res.json())
            .then(fetched => { setData(fetched.data || []); setLoading(false); })
            .catch(err => { setError(err.message); setLoading(false); });
    }, []);


    const isHolding = (name) => {
        if (!name) return false;
        const lower = name.toLowerCase();
        return lower.includes('holding') || lower.includes('banco') || lower.includes('intermediários') || lower.includes('segur') || lower.includes('financeiro');
    };

    // --- Data processing helpers ---
    const finalize = (node) => {
        if (node.children) {
            node.children = node.children.map(finalize);
            node.value = node.children.reduce((s, c) => s + (c.value || 0), 0);
            const totalMarket = node.children.reduce((s, c) => s + (c.market_cap || c.value || 0), 0);
            node.market_cap = totalMarket;

            // Median P/L Logic
            const plValues = node.children.map(c => c.p_l).sort((a, b) => a - b);
            const midPL = Math.floor(plValues.length / 2);
            node.p_l = plValues.length === 0 ? 0 : (
                plValues.length % 2 !== 0 ? plValues[midPL] : (plValues[midPL - 1] + plValues[midPL]) / 2
            );

            // Median Margin Logic (Robust against outliers)
            // We collect the effective margin of all children and pick the median.
            const isFin = isHolding(node.name);
            const margins = node.children.map(c => {
                // Determine effective margin for this child to be used in median
                // If child is a leaf, apply fallback (ROE) if applicable
                // If child is a group, its net_margin is already the median of its own children
                let val = c.net_margin;
                if (!c.children && (c.is_holding || isFin)) {
                    // Fallback for banks/insurance leaf nodes with 0 margin
                    if (!val && c.roe && c.p_l > 0) val = c.roe;
                }
                return val || 0;
            }).sort((a, b) => a - b);

            const mid = Math.floor(margins.length / 2);
            node.net_margin = margins.length === 0 ? 0 : (
                margins.length % 2 !== 0 ? margins[mid] : (margins[mid - 1] + margins[mid]) / 2
            );

            node.roe = totalMarket > 0 ? node.children.reduce((s, c) => s + ((c.roe || 0) * (c.market_cap || c.value || 0)), 0) / totalMarket : 0;
            node.roic = totalMarket > 0 ? node.children.reduce((s, c) => s + ((c.roic || 0) * (c.market_cap || c.value || 0)), 0) / totalMarket : 0;
            node.dy = totalMarket > 0 ? node.children.reduce((s, c) => s + ((c.dy || 0) * (c.market_cap || c.value || 0)), 0) / totalMarket : 0;
            node.is_holding = isFin;
        }
        return node;
    };

    const getLeafCount = (node) => {
        if (node.is_ticker) return 1;
        if (!node.children) return 0;
        return node.children.reduce((acc, child) => acc + getLeafCount(child), 0);
    };

    // --- Data processing shared across filters and treemap ---
    const processedData = useMemo(() => {
        if (!data.length) return [];
        const LIQUIDITY_MIN = 1000000; // 1 M
        const TARGET_HOLDINGS = ['ITSA3', 'ITSA4', 'BRAP3', 'BRAP4', 'SIMH3'];

        const tickerGroups = {};
        data.forEach(stock => {
            // FIX: Strict check for missing liquidity to avoid including dead stocks
            if (!stock.liq_2m || stock.liq_2m < LIQUIDITY_MIN) return;
            const companyBase = stock.ticker.substring(0, 4);

            const s = { ...stock }; // Clone to avoid mutation of source data
            s.sector = simplifyName(s.sector);

            // Force holding grouping - include 'Holdings Diversificadas' sector
            const sLower = (s.sector || '').toLowerCase();
            if (TARGET_HOLDINGS.includes(s.ticker) || sLower.includes('holdings diversificadas')) {
                s.sector = 'Holdings e Investimentos';
            }

            // User priority for PETR4 over PETR3
            const isPreferred = (tick) => tick.endsWith('4') || tick.endsWith('11'); // 4 and Units are often more liquid
            const existing = tickerGroups[companyBase];

            if (!existing) {
                tickerGroups[companyBase] = s;
            } else {
                // If PETR4 vs PETR3, choose PETR4
                if (s.ticker === 'PETR4' && existing.ticker === 'PETR3') {
                    tickerGroups[companyBase] = s;
                } else if (s.ticker === 'PETR3' && existing.ticker === 'PETR4') {
                    // keep PETR4
                } else if (s.market_cap > existing.market_cap) {
                    // Default to higher market cap if no special priority
                    tickerGroups[companyBase] = s;
                }
            }
        });

        // User mentioned ITSA4, BRAP4, SIMH3 specifically, let's ensure other Diversified Holdings are also included if they meet criteria
        return Object.values(tickerGroups);
    }, [data]);

    const treeData = useMemo(() => {
        if (!processedData.length) return [];
        const MIN_ITEMS = 3;
        const MAX_BOXES = 15;

        let allFilteredStocks = [...processedData];

        // Apply Sector Filter first (so Top 15 honors it as requested)
        if (selectedSectors.length > 0) {
            allFilteredStocks = allFilteredStocks.filter(s => selectedSectors.includes(s.sector));
        }

        // Apply Top 15 Filter Logic
        if (filterTop15) {
            allFilteredStocks = allFilteredStocks.filter(stockItem =>
                (stockItem.p_l >= plFilter.min && stockItem.p_l <= plFilter.max) &&
                (stockItem.net_margin * 100 >= marginFilter.min && stockItem.net_margin * 100 <= marginFilter.max) &&
                (stockItem.roe * 100 >= roeFilter.min && stockItem.roe * 100 <= roeFilter.max) &&
                (stockItem.roic * 100 >= roicFilter.min && stockItem.roic * 100 <= roicFilter.max) &&
                (stockItem.dy * 100 >= dyFilter.min && stockItem.dy * 100 <= dyFilter.max)
            );

            // Sort by priority
            allFilteredStocks.sort((a, b) => {
                if (sortPriority === 'margin') return (b.net_margin || 0) - (a.net_margin || 0);
                if (sortPriority === 'dy') return (b.dy || 0) - (a.dy || 0);
                if (sortPriority === 'roe') return (b.roe || 0) - (a.roe || 0);
                if (sortPriority === 'roic') return (b.roic || 0) - (a.roic || 0);

                const valA = a.p_l <= 0 ? 999 : a.p_l;
                const valB = b.p_l <= 0 ? 999 : b.p_l;
                return valA - valB;
            });

            allFilteredStocks = allFilteredStocks.slice(0, 15);

            // Special Case: Flat list for Top 15
            return allFilteredStocks.map(s => {
                return {
                    name: s.ticker,
                    value: Math.sqrt(s.market_cap || 1),
                    market_cap: s.market_cap,
                    p_l: s.p_l || 0,
                    net_margin: s.net_margin || 0,
                    roe: s.roe || 0,
                    roic: s.roic || 0,
                    dy: s.dy || 0,
                    is_holding: isHolding(s.ticker),
                    is_ticker: true
                };
            }).sort((a, b) => b.value - a.value);
        }

        const stocks = allFilteredStocks;

        // 2. Build Raw Hierarchy
        const raw = {};
        stocks.forEach(s => {
            const sec = s.sector || 'Outros Setores';
            const sub = s.subsector || 'Outros Subsetores';
            if (!raw[sec]) raw[sec] = {};
            if (!raw[sec][sub]) raw[sec][sub] = [];

            const visualVal = Math.sqrt(s.market_cap || 0);

            raw[sec][sub].push({
                name: s.ticker,
                value: visualVal,
                market_cap: s.market_cap,
                p_l: s.p_l || 0,
                net_margin: s.net_margin || 0,
                roe: s.roe || 0,
                roic: s.roic || 0,
                dy: s.dy || 0,
                is_holding: isHolding(s.ticker) || isHolding(s.subsector) || isHolding(s.sector),
                is_ticker: true
            });
        });

        const groupLevel = (items, label = 'Outros Setores') => {
            if (items.length <= MAX_BOXES) return items;
            const sorted = [...items].sort((a, b) => b.value - a.value);
            const top = sorted.slice(0, MAX_BOXES - 1);
            const others = sorted.slice(MAX_BOXES - 1);

            return [...top, finalize({
                name: label,
                children: others,
                is_consolidated: true
            })];
        };

        // 3. Process Levels
        let sectorsList = Object.entries(raw).map(([secName, subsRaw]) => {
            let subsectors = Object.entries(subsRaw).map(([subName, companies]) => ({
                name: subName,
                children: groupLevel(companies, 'Outras Empresas')
            }));

            const smallSubs = subsectors.filter(s => s.children.length < MIN_ITEMS && s.name !== 'Outros Subsetores');
            if (smallSubs.length > 0 && subsectors.length > 1) {
                let othersSub = subsectors.find(s => s.name === 'Outros Subsetores');
                if (!othersSub) { othersSub = { name: 'Outros Subsetores', children: [] }; subsectors.push(othersSub); }
                smallSubs.forEach(s => othersSub.children.push(...s.children));
                subsectors = subsectors.filter(s => !smallSubs.includes(s));
                othersSub.children = groupLevel(othersSub.children.sort((a, b) => b.value - a.value), 'Outras Empresas');
            }

            if (subsectors.length === 1 || (simplifyName(secName) === 'Petróleo e Gás' && subsectors.some(s => s.name.includes('Exploração')))) {
                return { name: secName, children: subsectors[0].children, is_promoted: true };
            }
            return { name: secName, children: subsectors, is_promoted: false };
        });

        let processedSectors = sectorsList.map(finalize);

        // Consolidation: Min 3 companies per sector. EXEMPT key sectors to ensure they show at top level.
        const smallSectors = processedSectors.filter(s =>
            getLeafCount(s) < MIN_ITEMS &&
            s.name !== 'Outros Setores' &&
            s.name !== 'Holdings e Investimentos' &&
            s.name !== 'Saúde' &&
            simplifyName(s.name) !== 'Saúde' &&
            s.name !== 'Petróleo e Gás'
        );

        if (smallSectors.length > 0) {
            const largeSectors = processedSectors.filter(s => !smallSectors.includes(s));
            const consolidatedNodes = [];
            smallSectors.forEach(s => {
                if (s.is_promoted) consolidatedNodes.push(...s.children);
                else s.children.forEach(sub => consolidatedNodes.push(...sub.children));
            });

            const othersNode = finalize({
                name: 'Outros Setores',
                children: consolidatedNodes,
                is_consolidated: true
            });

            const existingOthers = largeSectors.find(s => s.name === 'Outros Setores');
            if (existingOthers) {
                existingOthers.children.push(...consolidatedNodes);
                finalize(existingOthers);
                processedSectors = largeSectors;
            } else {
                processedSectors = [...largeSectors, othersNode];
            }
        }

        const sortedSectors = processedSectors.sort((a, b) => b.value - a.value);
        if (sortedSectors.length > MAX_BOXES) {
            const top = sortedSectors.slice(0, MAX_BOXES - 1);
            const others = sortedSectors.slice(MAX_BOXES - 1);

            let existingOthers = top.find(s => s.name === 'Outros Setores');
            if (existingOthers) {
                existingOthers.children.push(...others);
                finalize(existingOthers);
                return top;
            } else {
                return [...top, finalize({
                    name: 'Outros Setores',
                    children: others,
                    is_consolidated: true
                })];
            }
        }
        return sortedSectors;
    }, [processedData, filterTop15, plFilter, marginFilter, roeFilter, roicFilter, dyFilter, sortPriority, selectedSectors]);

    const availableSectors = useMemo(() => {
        const sectorsWithStocks = new Set(processedData
            .map(s => s.sector)
            .filter(Boolean)
        );
        return Array.from(sectorsWithStocks).sort();
    }, [processedData]);

    const filteredAvailableSectors = useMemo(() => {
        if (!sectorSearchTerm) return availableSectors;
        return availableSectors.filter(sec =>
            sec.toLowerCase().includes(sectorSearchTerm.toLowerCase()) ||
            simplifyName(sec).toLowerCase().includes(sectorSearchTerm.toLowerCase())
        );
    }, [availableSectors, sectorSearchTerm]);

    // Reset view if current parent/subParent is missing in treeData (e.g. after filter change)
    useEffect(() => {
        if (viewState.level === 'market') return;

        const sectorExists = (treeData || []).find(s => s.name === viewState.parent);
        if (!sectorExists) {
            setViewState({ level: 'market', parent: null, subParent: null });
            return;
        }

        if (viewState.level === 'subsector') {
            const subExists = sectorExists.children?.find(s => s.name === viewState.subParent);
            if (!subExists) {
                setViewState({ level: 'sector', parent: viewState.parent, subParent: null });
            }
        }
    }, [treeData, viewState, setViewState]);

    const currentData = useMemo(() => {
        let list = [];
        if (viewState.level === 'market') list = treeData;
        else if (viewState.level === 'sector') list = treeData.find(s => s.name === viewState.parent)?.children || [];
        else if (viewState.level === 'subsector') {
            const sec = treeData.find(s => s.name === viewState.parent);
            list = sec?.children.find(s => s.name === viewState.subParent)?.children || [];
        }

        // CRITICAL: Flatten the children for Recharts to prevent automatic drill-down
        const treemapCompatible = list.map(node => {
            const { children, ...rest } = node;
            return { ...rest, _origChildren: children }; // Keep reference for manual drill-down
        });

        // Ensure we always return a root-like node that Recharts can handle
        return [{ name: 'B3', children: treemapCompatible.length > 0 ? treemapCompatible : [{ name: 'Vazio', value: 1 }] }];
    }, [treeData, viewState]);

    const handleNodeClick = (node) => {
        if (!node || node.name === 'B3' || node.name === 'Vazio') return;
        setHighlightedTicker(null);
        if (viewState.level === 'market') {
            const target = treeData.find(s => s.name === node.name);
            if (target?._origChildren || target?.children) setViewState({ level: 'sector', parent: node.name, subParent: null });
        } else if (viewState.level === 'sector') {
            const sec = treeData.find(s => s.name === viewState.parent);
            const sub = sec?.children.find(s => s.name === node.name);
            if (sub?._origChildren || sub?.children) setViewState({ level: 'subsector', parent: viewState.parent, subParent: node.name });
        }
    };

    const handleSelectTicker = (t) => {
        setHighlightedTicker(t); setSearchTerm(t); setShowSuggestions(false);
        for (const sec of treeData) {
            if (sec.children?.some(c => c.name === t)) { setViewState({ level: 'sector', parent: sec.name, subParent: null }); return; }
            if (sec.children?.some(sub => sub.children?.some(c => c.name === t))) {
                const subName = sec.children.find(s => s.children?.some(c => c.name === t)).name;
                setViewState({ level: 'subsector', parent: sec.name, subParent: subName }); return;
            }
        }
    };

    if (loading) return <div className="fu-card" style={{ padding: '40px', textAlign: 'center' }}>Carregando dados...</div>;

    const allTickers = processedData.map(d => d.ticker);
    const suggestions = searchTerm.length >= 2 ? allTickers.filter(t => t.toLowerCase().includes(searchTerm.toLowerCase())).slice(0, 8) : [];

    return (
        <div className="treemap-section fu-container">
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
                        Mapa de Valor da B3
                    </h2>

                    <div className="search-container" ref={searchRef} style={{ position: 'relative', marginTop: '10px' }}>
                        <input type="text" placeholder="Buscar Ação..." className="fu-input" value={searchTerm}
                            onChange={e => { setSearchTerm(e.target.value); setShowSuggestions(true); }} onFocus={() => setShowSuggestions(true)} />
                        {showSuggestions && suggestions.length > 0 && (
                            <div style={{
                                position: 'absolute', top: '100%', left: 0, right: 0,
                                background: '#1a202c', border: '1px solid #2d3748',
                                zIndex: 1000, borderRadius: '4px', overflow: 'hidden'
                            }}>
                                {suggestions.map(t => <div key={t} style={{ padding: '8px 12px', cursor: 'pointer', borderBottom: '1px solid #2d3748' }} onClick={() => handleSelectTicker(t)}>{t}</div>)}
                            </div>
                        )}
                    </div>
                </div>

                <div style={{
                    marginTop: 'var(--spacing-4)',
                    borderLeft: '2px solid var(--color-accent-gold)',
                    paddingLeft: 'var(--spacing-6)',
                    marginLeft: 'var(--spacing-2)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px'
                }}>
                    <div style={{
                        textAlign: 'justify',
                        color: 'var(--color-text-tertiary)',
                        fontSize: 'var(--font-size-lg)',
                        lineHeight: '1.8',
                        maxWidth: '100%'
                    }}>
                        <p style={{ marginBottom: '0' }}>
                            P/L: Verde (Baixo) → Amarelo (Alto) | Vermelho (Negativo) | Liq. {">"} R$ 1M |
                            <span style={{ marginLeft: '8px', color: '#4a90e2' }}>Margem Financeiro = ROE</span>
                        </p>
                    </div>

                    {/* Sector Multi-filter moved here for flow */}
                    <div style={{ position: 'relative', alignSelf: 'flex-start' }}>
                        <button
                            className="fu-input"
                            style={{ cursor: 'pointer', minWidth: '160px' }}
                            onClick={() => setShowSectorFilter(!showSectorFilter)}
                        >
                            {selectedSectors.length === 0 ? 'Filtrar por Setores (Todos)' : `${selectedSectors.length} Setores Selecionados`}
                        </button>
                        {showSectorFilter && (
                            <div style={{
                                position: 'absolute', top: '100%', left: 0,
                                background: '#1a202c', border: '1px solid #2d3748',
                                padding: '10px', zIndex: 1100, borderRadius: '4px',
                                maxHeight: '400px', overflowY: 'auto', minWidth: '300px',
                                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.7)'
                            }}>
                                <div style={{ marginBottom: '10px' }}>
                                    <input
                                        type="text"
                                        placeholder="Pesquisar setor..."
                                        className="fu-input"
                                        style={{ width: '100%', fontSize: '12px', padding: '6px' }}
                                        value={sectorSearchTerm}
                                        onChange={e => setSectorSearchTerm(e.target.value)}
                                        onClick={e => e.stopPropagation()}
                                    />
                                </div>
                                <div style={{
                                    marginBottom: '10px', paddingBottom: '10px',
                                    borderBottom: '1px solid #2d3748', display: 'flex',
                                    justifyContent: 'space-between', alignItems: 'center'
                                }}>
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '13px' }}>
                                        <input
                                            type="checkbox"
                                            checked={selectedSectors.length === availableSectors.length && availableSectors.length > 0}
                                            onChange={() => {
                                                if (selectedSectors.length === availableSectors.length) setSelectedSectors([]);
                                                else setSelectedSectors(availableSectors);
                                            }}
                                        />
                                        Selecionar Todos
                                    </label>
                                    <button
                                        style={{ fontSize: '10px', padding: '3px 8px', background: '#2d3748', color: '#fff', border: 'none', borderRadius: '3px', cursor: 'pointer' }}
                                        onClick={() => { setSelectedSectors([]); setSectorSearchTerm(''); }}
                                    >
                                        Limpar
                                    </button>
                                </div>
                                {filteredAvailableSectors.map(sec => (
                                    <label key={sec} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 0', cursor: 'pointer', transition: 'background 0.2s' }}>
                                        <input
                                            type="checkbox"
                                            checked={selectedSectors.includes(sec)}
                                            onChange={() => {
                                                setSelectedSectors(prev =>
                                                    prev.includes(sec) ? prev.filter(x => x !== sec) : [...prev, sec]
                                                );
                                            }}
                                        />
                                        <span style={{ fontSize: '13px' }}>{sec}</span>
                                    </label>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Advanced Filters for Top 15 - Reorganized Layout */}
            <div className="fu-card" style={{ padding: '20px', marginBottom: '15px', background: '#1a202c', border: '1px solid #2d3748' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px', borderBottom: '1px solid #2d3748', paddingBottom: '10px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontWeight: 700, cursor: 'pointer', color: '#4a90e2', fontSize: '1.1rem' }}>
                        <input type="checkbox" checked={filterTop15} onChange={e => setFilterTop15(e.target.checked)} style={{ transform: 'scale(1.2)' }} />
                        ATIVAR FILTRO (TOP 15)
                    </label>

                    <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                        <span style={{ fontSize: '13px', fontWeight: 600, color: '#e2e8f0' }}>Ordenar por:</span>
                        <select className="fu-input" style={{ padding: '6px' }} value={sortPriority} onChange={e => setSortPriority(e.target.value)}>
                            <option value="pl">Preço/Lucro (Menor)</option>
                            <option value="margin">Margem Líq. (Maior)</option>
                            <option value="dy">Dividend Yield (Maior)</option>
                            <option value="roe">ROE (Maior)</option>
                            <option value="roic">ROIC (Maior)</option>
                        </select>
                    </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '15px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                        <span style={{ fontSize: '12px', fontWeight: 600, color: '#a0aec0' }}>Preço/Lucro (P/L)</span>
                        <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
                            <input type="number" step="0.5" className="fu-input" style={{ width: '100%', padding: '6px' }} value={plFilter.min} onChange={e => setPlFilter({ ...plFilter, min: parseFloat(e.target.value) })} />
                            <span style={{ color: '#718096' }}>a</span>
                            <input type="number" step="0.5" className="fu-input" style={{ width: '100%', padding: '6px' }} value={plFilter.max} onChange={e => setPlFilter({ ...plFilter, max: parseFloat(e.target.value) })} />
                        </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                        <span style={{ fontSize: '12px', fontWeight: 600, color: '#a0aec0' }}>Margem Líquida (%)</span>
                        <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
                            <input type="number" className="fu-input" style={{ width: '100%', padding: '6px' }} value={marginFilter.min} onChange={e => setMarginFilter({ ...marginFilter, min: parseFloat(e.target.value) })} />
                            <span style={{ color: '#718096' }}>a</span>
                            <input type="number" className="fu-input" style={{ width: '100%', padding: '6px' }} value={marginFilter.max} onChange={e => setMarginFilter({ ...marginFilter, max: parseFloat(e.target.value) })} />
                        </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                        <span style={{ fontSize: '12px', fontWeight: 600, color: '#a0aec0' }}>ROE (%)</span>
                        <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
                            <input type="number" className="fu-input" style={{ width: '100%', padding: '6px' }} value={roeFilter.min} onChange={e => setRoeFilter({ ...roeFilter, min: parseFloat(e.target.value) })} />
                            <span style={{ color: '#718096' }}>a</span>
                            <input type="number" className="fu-input" style={{ width: '100%', padding: '6px' }} value={roeFilter.max} onChange={e => setRoeFilter({ ...roeFilter, max: parseFloat(e.target.value) })} />
                        </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                        <span style={{ fontSize: '12px', fontWeight: 600, color: '#a0aec0' }}>ROIC (%)</span>
                        <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
                            <input type="number" className="fu-input" style={{ width: '100%', padding: '6px' }} value={roicFilter.min} onChange={e => setRoicFilter({ ...roicFilter, min: parseFloat(e.target.value) })} />
                            <span style={{ color: '#718096' }}>a</span>
                            <input type="number" className="fu-input" style={{ width: '100%', padding: '6px' }} value={roicFilter.max} onChange={e => setRoicFilter({ ...roicFilter, max: parseFloat(e.target.value) })} />
                        </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                        <span style={{ fontSize: '12px', fontWeight: 600, color: '#a0aec0' }}>Dividend Yield (%)</span>
                        <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
                            <input type="number" className="fu-input" style={{ width: '100%', padding: '6px' }} value={dyFilter.min} onChange={e => setDyFilter({ ...dyFilter, min: parseFloat(e.target.value) })} />
                            <span style={{ color: '#718096' }}>a</span>
                            <input type="number" className="fu-input" style={{ width: '100%', padding: '6px' }} value={dyFilter.max} onChange={e => setDyFilter({ ...dyFilter, max: parseFloat(e.target.value) })} />
                        </div>
                    </div>
                </div>
            </div>

            <div className="breadcrumb" style={{ marginBottom: '12px', display: 'flex', gap: '8px', fontSize: '0.9rem' }}>
                <span onClick={() => setViewState({ level: 'market', parent: null })} style={{ cursor: 'pointer', color: viewState.level === 'market' ? '#4a90e2' : '' }}>B3</span>
                {viewState.level !== 'market' && (
                    <><span>/</span><span onClick={() => setViewState({ level: 'sector', parent: viewState.parent })} style={{ cursor: 'pointer', color: viewState.level === 'sector' ? '#4a90e2' : '' }}>{viewState.parent}</span></>
                )}
                {viewState.level === 'subsector' && (
                    <><span>/</span><span style={{ color: '#4a90e2' }}>{viewState.subParent}</span></>
                )}
            </div>

            <div className="treemap-container fu-card" style={{ background: '#0f172a', borderRadius: '8px', overflow: 'hidden' }}>
                <ResponsiveContainer width="100%" height={600}>
                    <Treemap
                        key={`${viewState.level}-${viewState.parent}-${viewState.subParent}-${filterTop15}`}
                        data={currentData[0].children}
                        dataKey="value"
                        ratio={4 / 3}
                        stroke="#010101"
                        content={<CustomContent />}
                        onClick={handleNodeClick}
                    >
                        <Tooltip content={({ active, payload }) => {
                            if (active && payload?.length) {
                                const d = payload[0].payload;
                                return (
                                    <div style={{ background: '#1a202c', padding: '12px', border: '1px solid #4a5568', borderRadius: '4px', boxShadow: '0 4px 6px rgba(0,0,0,0.5)' }}>
                                        <p style={{ fontWeight: 700, margin: 0, fontSize: '1.1rem' }}>{d.name}</p>
                                        <p style={{ margin: '4px 0', color: '#cbd5e0' }}>Valor de Mercado: R$ {((d.market_cap || d.value) / 1e9).toFixed(1)} Bi</p>
                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '10px', borderTop: '1px solid #4a5568', paddingTop: '10px' }}>
                                            <span>P/L: <strong>{d.p_l ? d.p_l.toFixed(1) : '-'}</strong></span>
                                            <span>Margem: <strong>{((d.net_margin || (d.roe && d.p_l > 0 ? d.roe : 0)) * 100).toFixed(1) + '%'}</strong></span>
                                            <span>ROE: <strong>{(d.roe * 100).toFixed(1)}%</strong></span>
                                            <span>ROIC: <strong>{(d.roic * 100).toFixed(1)}%</strong></span>
                                            <span>DY: <strong>{(d.dy * 100).toFixed(1)}%</strong></span>
                                        </div>
                                    </div>
                                );
                            }
                            return null;
                        }} />
                    </Treemap>
                </ResponsiveContainer>
            </div>
            <style>{`
                .breadcrumb span:hover { text-decoration: underline; }
                .section-title { margin: 0; font-size: 1.5rem; }
                .section-subtitle { margin: 4px 0 0; font-size: 0.9rem; opacity: 0.8; line-height: 1.2; }
                .section-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem; }
                .fu-input { background: #1a202c; border: 1px solid #2d3748; color: white; padding: 0.5rem; border-radius: 4px; }
            `}</style>
        </div>
    );
};

export default B3Treemap;
