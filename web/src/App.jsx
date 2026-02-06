import React from 'react';
import Header from './components/Header';
import WorldComparison from './components/WorldComparison';
import B3Treemap from './components/B3Treemap';

import Rankings from './components/Rankings';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) { return { hasError: true, error }; }
  componentDidCatch(error, errorInfo) { console.error("App Crash:", error, errorInfo); }
  render() {
    if (this.state.hasError) {
      return (
        <div className="fu-container" style={{ padding: '40px', color: '#ff6b6b' }}>
          <h2>Ops! Algo deu errado.</h2>
          <pre>{this.state.error?.message}</pre>
          <button onClick={() => window.location.reload()} className="fu-input">Recarregar Página</button>
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  return (
    <ErrorBoundary>
      <div className="app-layout">
        <Header />

        <main className="main-content">
          <WorldComparison />
          <B3Treemap />
          <Rankings />
        </main>

        <footer className="app-footer">
          <div className="fu-container">
            <p>© {new Date().getFullYear()} Análise Ações.</p>
          </div>
        </footer>

        <style>{`
        .app-footer {
          padding: var(--spacing-8) 0;
          margin-top: var(--spacing-16);
          border-top: 1px solid var(--color-divider);
          text-align: center;
          font-size: var(--font-size-sm);
          color: var(--color-text-tertiary);
        }
      `}</style>
      </div>
    </ErrorBoundary>
  );
}

export default App;
