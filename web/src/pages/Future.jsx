import React from 'react';

const Future = () => {
    return (
        <div className="page-future fu-container section-spacing" style={{ padding: 'var(--spacing-16) 0', textAlign: 'center' }}>
            <h1 className="fu-title" style={{ fontSize: '3rem', marginBottom: 'var(--spacing-6)' }}>Previsões e Tendências</h1>
            <p className="fu-text" style={{ fontSize: 'var(--font-size-lg)', maxWidth: '800px', margin: '0 auto', lineHeight: '1.6' }}>
                Nossos modelos treinados monitoram milhares de dados macroeconômicos nacionais e internacionais para identificar padrões, mudanças, movimentos e tendências que impactam diretamente nos negócios das empresas.
            </p>
            <div style={{ marginTop: 'var(--spacing-12)', opacity: 0.5 }}>
                🔮 Em Desenvolvimento
            </div>
        </div>
    );
};

export default Future;
