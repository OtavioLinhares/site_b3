import React from 'react';

const SelicAnalysis = () => {
    const cards = [
        {
            title: "O que é (e o que não é) o Ibovespa",
            text: "O Ibovespa reflete as ações mais negociadas da bolsa, não necessariamente as melhores empresas. Empresas em condições adversas costumam ser intensamente negociadas, sobretudo por operações de curto prazo, o que contribui para sua inclusão e relevância no índice.",
            color: "var(--color-accent-blue)"
        },
        {
            title: "Ciclos de juros e retorno das ações",
            text: "Nos períodos em que a taxa Selic está em trajetória de queda, o Ibovespa tende a apresentar retornos superiores à renda fixa, impulsionado pela redução do custo de capital e maior apetite ao risco.",
            color: "var(--color-accent-blue)"
        },
        {
            title: "Quando a lógica não funcionou",
            text: "Entre 2011 e 2013, o Ibovespa teve desempenho fraco apesar da queda dos juros. Dois fatores foram determinantes: controle de preços da principal estatal do país e crise no ciclo das commodities.",
            color: "var(--color-negative)"
        },
        {
            title: "Fluxo estrangeiro como fator-chave",
            text: "A partir de 2025, uma crise de confiança internacional levou a forte entrada de capital estrangeiro no Brasil, sustentando o Ibovespa mesmo em um ambiente doméstico menos favorável sob a ótica dos juros.",
            color: "var(--color-accent-blue)"
        },
        {
            title: "O longo prazo traz uma lição clara",
            text: "No acumulado de cerca de 20 anos, a taxa Selic superou o Ibovespa. Isso mostra que investir em ações exige escolher bem os ativos, e não apenas replicar um índice amplo.",
            color: "var(--color-warning)"
        },
        {
            title: "Onde entra a análise de dados",
            text: "Este site existe para trazer clareza aos números, ajudando o investidor a entender ciclos, identificar distorções e selecionar ações com base em dados, não em narrativas.",
            color: "var(--color-positive)"
        }
    ];

    return (
        <section className="selic-analysis" style={{ padding: 'var(--spacing-16) 0' }}>
            <div className="fu-container">

                {/* Header & Hero - Replicating Header.jsx Style */}
                <div style={{ textAlign: 'left', marginBottom: 'var(--spacing-12)', maxWidth: '100%' }}>
                    <h2 style={{
                        fontFamily: 'var(--font-family-serif)',
                        fontSize: '2.5rem', // Matches Header responsive size or close to 3.5rem
                        lineHeight: '1.2',
                        marginBottom: 'var(--spacing-6)',
                        background: 'linear-gradient(to right, var(--color-text-primary), var(--color-text-secondary))',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        display: 'inline-block' // Needed for gradient text sometimes
                    }}>
                        Renda Variável vs Renda Fixa
                    </h2>

                    <div style={{
                        marginTop: 'var(--spacing-4)',
                        borderLeft: '2px solid var(--color-accent-gold)', // The "yellow trace"
                        paddingLeft: 'var(--spacing-6)',
                        marginLeft: 'var(--spacing-2)'
                    }}>
                        <div style={{
                            textAlign: 'justify',
                            color: 'var(--color-text-tertiary)', // As per Header intro-text
                            fontSize: 'var(--font-size-lg)',
                            lineHeight: '1.8',
                            maxWidth: '100%' // Match chart width
                        }}>
                            <p style={{ marginBottom: 'var(--spacing-4)' }}>
                                <strong style={{ color: 'var(--color-text-primary)' }}>O Ibovespa não representa as melhores ações da bolsa brasileira</strong>, mas sim as mais negociadas. Ainda assim, ao longo do tempo, observa-se uma relação consistente entre a tendência da taxa Selic e o desempenho do mercado acionário.
                            </p>
                            <p style={{ marginBottom: 'var(--spacing-4)' }}>
                                De forma geral, ciclos de queda da Selic favorecem retornos superiores do Ibovespa, enquanto exceções históricas podem ser explicadas por fatores específicos, como intervenções em empresas relevantes do índice, crises no ciclo das commodities ou movimentos extraordinários de capital estrangeiro.
                            </p>
                            <p>
                                No longo prazo, a análise mostra que a Selic superou o Ibovespa, reforçando que investir em ações exige seleção criteriosa e leitura correta dos ciclos econômicos — e não apenas acompanhar um índice amplo.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Chart */}
                <div className="fu-card" style={{
                    padding: '0',
                    overflow: 'hidden',
                    marginBottom: 'var(--spacing-12)',
                    border: 'none', // Removed border per user request "borda do grafico ficou muito grande" (assuming HTML border)
                    height: '600px',
                    // background: '#fff' // Removed white theme per user request
                }}>
                    <iframe
                        src={`${import.meta.env.BASE_URL}selic_analysis.html`}
                        title="Selic Analysis Chart"
                        style={{ width: '100%', height: '100%', border: 'none' }}
                    />
                </div>

                {/* Cards Grid */}
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                    gap: 'var(--spacing-6)'
                }}>
                    {cards.map((card, index) => (
                        <div key={index} className="fu-card" style={{
                            borderTop: `4px solid ${card.color}`,
                            transition: 'transform 0.2s ease',
                            cursor: 'default'
                        }}>
                            <h3 style={{
                                fontSize: 'var(--font-size-lg)',
                                marginBottom: 'var(--spacing-2)',
                                color: 'var(--color-text-primary)'
                            }}>
                                {card.title}
                            </h3>
                            <p style={{
                                fontSize: 'var(--font-size-sm)',
                                color: 'var(--color-text-secondary)',
                                lineHeight: '1.6'
                            }}>
                                {card.text}
                            </p>
                        </div>
                    ))}
                </div>

            </div>
        </section>
    );
};

export default SelicAnalysis;
