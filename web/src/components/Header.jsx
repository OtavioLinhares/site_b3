import React from 'react';
import { TrendingUp, Globe, BarChart3 } from 'lucide-react';

const Header = () => {
  return (
    <header className="header-section">
      <div className="fu-container">
        <div className="header-content">
          <div className="header-brand">
            <TrendingUp size={32} color="var(--color-accent-gold)" />
            <span className="brand-name">Análise Ações</span>
          </div>

          <h1 className="main-title">
            Clareza em um Mar de Ruído.
          </h1>

          <h2 className="subtitle">
            Uma visão serena e fundamentalista da Bolsa Brasileira (B3).
          </h2>

          <p className="intro-text">
            Este projeto busca reduzir a complexidade do mercado financeiro através de uma
            <strong> abordagem objetiva, simples e holística</strong>.
            Porque o simples funciona: se ficar complicado, é porque não está certo.
            Aqui, unimos o passado, presente e futuro: comparamos a B3 globalmente e identificamos valor real (<strong>Hoje</strong>),
            simulamos estratégias históricas (<strong>Passado</strong>), projetamos tendências com IA (<strong>Futuro</strong>)
            e quantificamos a exposição real dos seus investimentos (<strong>Risco</strong>).
          </p>

          <div className="header-stats">
            <div className="stat-item">
              <Globe size={20} className="stat-icon" />
              <span>Comparação Global</span>
            </div>
            <div className="stat-item">
              <BarChart3 size={20} className="stat-icon" />
              <span>Dados Diários</span>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        .header-section {
          padding: var(--spacing-16) 0;
          border-bottom: 1px solid var(--color-border);
          position: relative;
        }

        .fu-container {
          position: relative;
          z-index: 1;
        }
        
        .header-content {
          max-width: 100%; /* Full width to match chart/container */
        }
        
        .header-brand {
          display: flex;
          align-items: center;
          gap: var(--spacing-3);
          margin-bottom: var(--spacing-8);
          opacity: 0.8;
        }
        
        .brand-name {
          font-family: var(--font-family-serif);
          font-size: var(--font-size-lg);
          letter-spacing: 0.05em;
          text-transform: uppercase;
          color: var(--color-text-secondary);
        }
        
        .main-title {
          font-family: var(--font-family-serif);
          font-size: 3.5rem;
          line-height: 1.1;
          margin-bottom: var(--spacing-4);
          background: linear-gradient(to right, var(--color-text-primary), var(--color-text-secondary));
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }
        
        .subtitle {
          font-size: var(--font-size-xl);
          font-weight: 400;
          color: var(--color-text-secondary);
          margin-bottom: var(--spacing-6);
          max-width: 100%; /* Full width */
        }
        
        .intro-text {
          font-size: var(--font-size-lg);
          color: var(--color-text-tertiary);
          line-height: 1.8;
          max-width: 100%; /* Match chart width */
          margin-bottom: var(--spacing-8);
          border-left: 2px solid var(--color-accent-gold);
          padding-left: var(--spacing-4);
        }
        
        .intro-text strong {
          color: var(--color-text-primary);
          font-weight: 600;
        }
        
        .header-stats {
          display: flex;
          gap: var(--spacing-8);
        }
        
        .stat-item {
          display: flex;
          align-items: center;
          gap: var(--spacing-2);
          color: var(--color-accent-blue);
          font-size: var(--font-size-sm);
          font-weight: 500;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        
        .stat-icon {
          opacity: 0.8;
        }
        
        @media (max-width: 768px) {
          .main-title {
            font-size: 2.5rem;
          }
          .subtitle {
            font-size: var(--font-size-lg);
          }
        }
      `}</style>
    </header>
  );
};

export default Header;
