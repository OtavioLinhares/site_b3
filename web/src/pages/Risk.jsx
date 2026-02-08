import React from 'react';

const Risk = () => {
    return (
        <div className="page-risk fu-container section-spacing" style={{ padding: 'var(--spacing-16) 0', textAlign: 'center' }}>
            <h1 className="fu-title" style={{ fontSize: '3rem', marginBottom: 'var(--spacing-6)' }}>Análise de Risco</h1>
            <p className="fu-text" style={{ fontSize: 'var(--font-size-lg)', maxWidth: '800px', margin: '0 auto', lineHeight: '1.6' }}>
                Você sabe o risco que está correndo ao investir em determinada ação? É comum se falar popularmente na expressão 'risco calculado', mas você realmente já calculou o risco dos seus investimentos? Nesta seção, é possível fazer isso utilizando as técnicas mais modernas existentes.
            </p>
            <div style={{ marginTop: 'var(--spacing-12)', opacity: 0.5 }}>
                ⚠️ Em Desenvolvimento
            </div>
        </div>
    );
};

export default Risk;
