import React from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Navigation from './components/Navigation';
import Today from './pages/Today';
import Past from './pages/Past';
import Future from './pages/Future';
import Risk from './pages/Risk';
import Footer from './components/Footer';
import LegalDisclaimer from './components/LegalDisclaimer';

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
      <HashRouter>
        <div className="app-layout" style={{ position: 'relative', zIndex: 1, minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
          <div className="global-bg" style={{ position: 'fixed', zIndex: -1 }} />

          <Header />
          <Navigation />

          <main className="main-content" style={{ flex: 1 }}>
            <Routes>
              <Route path="/" element={<Today />} />
              <Route path="/passado" element={<Past />} />
              <Route path="/futuro" element={<Future />} />
              <Route path="/risco" element={<Risk />} />
            </Routes>
            <LegalDisclaimer />
          </main>

          <Footer />
        </div>
      </HashRouter>
    </ErrorBoundary>
  );
}

export default App;
