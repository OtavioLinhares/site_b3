import React from 'react';

const LegalDisclaimer = () => {
    return (
        <section className="legal-section fu-container" style={{ marginTop: 'var(--spacing-20)', marginBottom: 'var(--spacing-12)' }}>
            {/* Standardized Header "Aviso" */}
            <div style={{ textAlign: 'left', marginBottom: 'var(--spacing-8)', maxWidth: '100%' }}>
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
                    Aviso
                </h2>

                <div style={{
                    marginTop: 'var(--spacing-4)',
                    borderLeft: '2px solid var(--color-accent-gold)',
                    paddingLeft: 'var(--spacing-6)',
                    marginLeft: 'var(--spacing-2)'
                }}>
                    <div style={{
                        textAlign: 'justify',
                        color: 'var(--color-text-tertiary)',
                        fontSize: '1rem',
                        lineHeight: '1.8',
                        maxWidth: '100%',
                        opacity: 0.9
                    }}>
                        <p style={{ marginBottom: '1rem' }}>
                            As informações, análises e conteúdos disponibilizados neste site têm <strong style={{ color: 'var(--color-text-primary)' }}>caráter exclusivamente informativo e educacional</strong>, não constituindo, em nenhuma hipótese, recomendação, oferta, solicitação ou indicação de compra ou venda de ativos financeiros, valores mobiliários ou quaisquer outros instrumentos de investimento.
                        </p>
                        <p style={{ marginBottom: '1rem' }}>
                            As análises apresentadas baseiam-se em dados históricos e públicos, estando sujeitas a limitações, alterações de cenário e interpretações distintas. Rentabilidade passada não representa garantia de resultados futuros.
                        </p>
                        <p style={{ marginBottom: 0 }}>
                            O leitor é integralmente responsável por suas decisões de investimento, devendo, se entender necessário, buscar orientação de profissionais devidamente habilitados antes de realizar qualquer operação no mercado financeiro.
                        </p>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default LegalDisclaimer;
