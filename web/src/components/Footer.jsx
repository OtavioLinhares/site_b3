import React from 'react';

const Footer = () => {
    return (
        <footer className="site-footer">
            <div className="fu-container">
                <div className="footer-content">
                    <div className="credits">
                        Otavio Linhares • 81 9 8863 5515 • otaviobr@gmail.com
                    </div>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-tertiary)', marginTop: 'var(--spacing-2)' }}>
                        Última atualização: {new Date().toLocaleString('pt-BR')}
                    </div>
                </div>
            </div>

            <style>{`
                .site-footer {
                    padding: var(--spacing-12) 0;
                    margin-top: var(--spacing-16);
                    border-top: 1px solid var(--color-border);
                    background: rgba(10, 10, 10, 0.5); /* Semi-transparent to blend with fixed bg */
                    font-size: var(--font-size-sm);
                    color: var(--color-text-tertiary);
                    text-align: center;
                }

                .footer-content {
                    max-width: 800px;
                    margin: 0 auto;
                }

                .credits {
                    margin-bottom: var(--spacing-4);
                    font-weight: 500;
                    color: var(--color-text-secondary);
                }

                .disclaimer {
                    font-size: var(--font-size-xs);
                    line-height: 1.6;
                    opacity: 0.7;
                }
            `}</style>
        </footer>
    );
};

export default Footer;
