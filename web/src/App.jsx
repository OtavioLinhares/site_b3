import React from 'react';
import Header from './components/Header';
import WorldComparison from './components/WorldComparison';
import SelicAnalysis from './components/SelicAnalysis';
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

import LegalDisclaimer from './components/LegalDisclaimer';
import Footer from './components/Footer';

function App() {
  return (
    <ErrorBoundary>
      <div className="app-layout" style={{ position: 'relative', zIndex: 1 }}>
        <div className="global-bg" style={{ position: 'fixed', zIndex: -1 }} />
        <Header />

        <main className="main-content">
          <SelicAnalysis />
          <WorldComparison />
          <B3Treemap />
          <Rankings />
          <LegalDisclaimer />
        </main>

        <Footer />
      </div>
    </ErrorBoundary>
  );
}

export default App;
