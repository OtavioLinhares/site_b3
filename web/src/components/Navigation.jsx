import React from 'react';
import { NavLink } from 'react-router-dom';

const Navigation = () => {
    const navItems = [
        { path: '/', label: 'Hoje' },
        { path: '/passado', label: 'Passado' },
        { path: '/futuro', label: 'Futuro' },
        { path: '/risco', label: 'Risco' },
        { path: '/backtest', label: 'Simulação' }
    ];

    return (
        <nav style={{
            display: 'flex',
            justifyContent: 'center',
            padding: 'var(--spacing-4) 0',
            borderBottom: '1px solid var(--color-border)',
            marginBottom: 'var(--spacing-8)',
            position: 'sticky',
            top: 0,
            zIndex: 100,
            background: 'rgba(10, 10, 10, 0.95)', // Matches global bg but opaque
            backdropFilter: 'blur(10px)'
        }}>
            <div className="fu-container" style={{ display: 'flex', gap: 'var(--spacing-8)', overflowX: 'auto' }}>
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
                        style={({ isActive }) => ({
                            color: isActive ? 'var(--color-accent-gold)' : 'var(--color-text-secondary)',
                            textDecoration: 'none',
                            fontSize: 'var(--font-size-md)',
                            fontWeight: isActive ? '600' : '400',
                            padding: 'var(--spacing-2) var(--spacing-4)',
                            borderBottom: isActive ? '2px solid var(--color-accent-gold)' : '2px solid transparent',
                            transition: 'color 0.2s, border-bottom 0.2s',
                            whiteSpace: 'nowrap'
                        })}
                    >
                        {item.label}
                    </NavLink>
                ))}
            </div>
        </nav>
    );
};

export default Navigation;
