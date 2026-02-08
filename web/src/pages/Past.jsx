import React from 'react';

const Past = () => {
    return (
        <div className="page-past fu-container section-spacing" style={{ padding: 'var(--spacing-16) 0', textAlign: 'center' }}>
            <h1 className="fu-title" style={{ fontSize: '3rem', marginBottom: 'var(--spacing-6)' }}>Simulador de Resultados</h1>
            <p className="fu-text" style={{ fontSize: 'var(--font-size-lg)', maxWidth: '600px', margin: '0 auto' }}>
                Em breve: Ferramenta de backtesting para simular estratégias de investimento com base em dados históricos.
            </p>
            <div style={{ marginTop: 'var(--spacing-12)', opacity: 0.5 }}>
                🚧 Em Desenvolvimento
            </div>
        </div>
    );
};

export default Past;
