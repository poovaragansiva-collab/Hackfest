import { useCallback } from 'react';
import { AppHeader }      from './components/AppHeader';
import { GenerationForm } from './components/GenerationForm';
import { ResultPanel }    from './components/ResultPanel';
import { useGeneration }  from './hooks/useGeneration';
import './App.css';

/**
 * App
 * Root component — wires the form, generation hook, and result panel together.
 * No prop drilling of service internals; the hook is the only coupling point.
 */
export default function App() {
  const { status, result, error, generate, reset } = useGeneration();

  const handleSubmit = useCallback((params) => {
    generate(params);
  }, [generate]);

  return (
    <div className="app">
      <AppHeader />

      <main className="workspace" aria-label="Image generation workspace">
        <section className="workspace__form" aria-label="Generation settings">
          <GenerationForm onSubmit={handleSubmit} status={status} />
        </section>

        <section className="workspace__result" aria-label="Generation result" aria-live="polite">
          <ResultPanel
            status={status}
            result={result}
            error={error}
            onReset={reset}
          />
        </section>
      </main>

      <footer className="app-footer">
        <p className="footer-note">
          <strong>ResourceAware AI</strong> — Frontend prototype only.
          No real images are generated. No API keys are used. No cost data is shown.
        </p>
        <span className="footer-member">Member 2 · React frontend</span>
      </footer>
    </div>
  );
}
