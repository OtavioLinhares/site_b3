import React, { useState, useRef, useEffect } from 'react';
import { Search, X, Check, ChevronDown } from 'lucide-react';

const MultiSelect = ({ options, value, onChange, placeholder, label }) => {
    // options: [{ value, label }]
    // value: array of strings (values)
    const [isOpen, setIsOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const wrapperRef = useRef(null);

    // Parse CSV value if string is passed
    const selectedValues = typeof value === 'string' ? value.split(',').map(s => s.trim()).filter(Boolean) : (value || []);

    const toggleOption = (optValue) => {
        const newValues = selectedValues.includes(optValue)
            ? selectedValues.filter(v => v !== optValue)
            : [...selectedValues, optValue];
        onChange(newValues);
    };

    const handleSelectAll = () => {
        onChange(filteredOptions.map(o => o.value));
    };

    const handleDeselectAll = () => {
        onChange([]);
    };

    const filteredOptions = (options || []).filter(opt =>
        opt.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
        opt.value.toLowerCase().includes(searchTerm.toLowerCase())
    );

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [wrapperRef]);

    return (
        <div className="form-group" ref={wrapperRef} style={{ position: 'relative' }}>
            {label && <label>{label}</label>}
            <div
                className="fu-input multi-select-trigger"
                onClick={(e) => { e.preventDefault(); e.stopPropagation(); setIsOpen(!isOpen); }}
                style={{
                    cursor: 'pointer',
                    minHeight: '40px',
                    display: 'flex',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: '5px',
                    paddingRight: '30px',
                    position: 'relative'
                }}
            >
                {selectedValues.length === 0 && <span style={{ color: 'var(--color-text-tertiary)' }}>{placeholder}</span>}
                {selectedValues.slice(0, 5).map(val => (
                    <span key={val} style={{ background: 'var(--color-bg-surface-hover)', border: '1px solid var(--color-border)', borderRadius: '3px', padding: '2px 6px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        {val}
                        <X size={12} style={{ cursor: 'pointer' }} onClick={(e) => { e.stopPropagation(); toggleOption(val); }} />
                    </span>
                ))}
                {selectedValues.length > 5 && <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>+{selectedValues.length - 5} selecionados</span>}

                <ChevronDown size={16} style={{ position: 'absolute', right: '10px', top: '12px', color: 'var(--color-text-tertiary)' }} />
            </div>

            {isOpen && (
                <div className="multi-select-dropdown animate-fade-in" style={{
                    position: 'absolute',
                    top: '100%',
                    left: 0,
                    right: 0,
                    background: '#1a202c',
                    border: '1px solid #2d3748',
                    borderRadius: 'var(--radius-sm)',
                    zIndex: 9999,
                    marginTop: '5px',
                    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.7)',
                    maxHeight: '300px',
                    display: 'flex',
                    flexDirection: 'column'
                }}>
                    <div style={{ padding: '10px', display: 'flex', flexDirection: 'column', gap: '10px', borderBottom: '1px solid #2d3748' }}>
                        <div style={{ position: 'relative' }}>
                            <Search size={14} style={{ position: 'absolute', left: '10px', top: '10px', color: '#718096' }} />
                            <input
                                type="text"
                                placeholder="Buscar..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                style={{
                                    width: '100%',
                                    background: '#2d3748',
                                    border: '1px solid #4a5568',
                                    padding: '8px 8px 8px 32px',
                                    borderRadius: '4px',
                                    color: '#e2e8f0',
                                    fontSize: '0.9rem',
                                    outline: 'none'
                                }}
                                onClick={(e) => e.stopPropagation()}
                                autoFocus
                            />
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.85rem', color: '#cbd5e0', userSelect: 'none' }} onClick={(e) => e.stopPropagation()}>
                                <input
                                    type="checkbox"
                                    checked={filteredOptions.length > 0 && filteredOptions.every(o => selectedValues.includes(o.value))}
                                    onChange={handleSelectAll}
                                    style={{ cursor: 'pointer', accentColor: 'var(--color-accent-gold)' }}
                                />
                                Selecionar Todos
                            </label>
                            <button
                                onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleDeselectAll(); }}
                                className="fu-btn-text"
                                style={{
                                    fontSize: '0.8rem',
                                    color: '#e2e8f0',
                                    background: '#2d3748',
                                    border: '1px solid #4a5568',
                                    padding: '4px 12px',
                                    borderRadius: '4px',
                                    cursor: 'pointer',
                                    transition: 'background 0.2s'
                                }}
                                onMouseOver={(e) => e.target.style.background = '#4a5568'}
                                onMouseOut={(e) => e.target.style.background = '#2d3748'}
                            >
                                Limpar
                            </button>
                        </div>
                    </div>

                    <div style={{ overflowY: 'auto', padding: '5px 0' }}>
                        {filteredOptions.length === 0 ? (
                            <div style={{ padding: '15px', textAlign: 'center', color: '#718096', fontSize: '0.85rem' }}>Nenhum item encontrado</div>
                        ) : (
                            filteredOptions.map(opt => (
                                <label
                                    key={opt.value}
                                    className="dropdown-item"
                                    style={{
                                        padding: '8px 12px',
                                        cursor: 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '10px',
                                        fontSize: '0.9rem',
                                        color: '#e2e8f0',
                                        transition: 'background 0.2s',
                                        userSelect: 'none'
                                    }}
                                    onClick={(e) => e.stopPropagation()}
                                >
                                    <input
                                        type="checkbox"
                                        checked={selectedValues.includes(opt.value)}
                                        onChange={() => toggleOption(opt.value)}
                                        onClick={(e) => e.stopPropagation()}
                                        style={{ accentColor: 'var(--color-accent-gold)', cursor: 'pointer' }}
                                    />
                                    <span>{opt.label}</span>
                                </label>
                            ))
                        )}
                    </div>
                </div>
            )}
            <style>{`
                .dropdown-item:hover {
                    background-color: #2d3748 !important;
                }
            `}</style>
        </div>
    );
};

export default MultiSelect;
