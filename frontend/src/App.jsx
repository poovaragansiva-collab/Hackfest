import { useState, useEffect, useCallback } from 'react';
import { AppHeader } from './components/AppHeader';
import { HeroSection } from './components/HeroSection';
import { GenerationForm } from './components/GenerationForm';
import { ResultPanel } from './components/ResultPanel';
import { StudioTelemetry } from './components/StudioTelemetry';
import { RecentGenerations } from './components/RecentGenerations';
import { GenerationHistory } from './components/GenerationHistory';
import { AnalyticsDashboard } from './components/AnalyticsDashboard';
import { CompareModal } from './components/CompareModal';
import { useGeneration } from './hooks/useGeneration';
import { fetchHistoryApi, clearHistoryApi } from './services/apiService';
import './App.css';

/**
 * App
 * Root component coordinating EcoGen AI Studio:
 * - Studio: Hero, 2-column generator & image preview, 4-card telemetry row & savings banner, and recent generations grid
 * - Resource Telemetry: Real generation analytics & 300 Schools District impact projection
 * - Recent: Full real persisted history & side-by-side comparison
 */
export default function App() {
  const [theme, setTheme] = useState(() => {
    try {
      const saved = localStorage.getItem('resourceaware-theme');
      if (saved === 'light' || saved === 'dark') return saved;
      return window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    } catch {
      return 'light';
    }
  });

  const [activeTab, setActiveTab] = useState('studio');

  // Real persisted generation history (starts empty, loads from backend SQLite)
  const [history, setHistory] = useState([]);
  const [viewedResult, setViewedResult] = useState(null);

  // Side-by-side compare state
  const [selectedForCompare, setSelectedForCompare] = useState([]);
  const [isCompareModalOpen, setIsCompareModalOpen] = useState(false);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    try {
      localStorage.setItem('resourceaware-theme', theme);
    } catch {
      // LocalStorage unavailable
    }
  }, [theme]);

  // Load genuine persistent records from backend on mount
  const refreshHistory = useCallback(async () => {
    try {
      const records = await fetchHistoryApi(20);
      if (records && Array.isArray(records) && records.length > 0) {
        const mapped = records.map(r => ({
          id: r.job_id,
          timestamp: r.timestamp,
          prompt: r.prompt,
          negative_prompt: r.negative_prompt,
          intended_use: r.inferred_purpose,
          tier: r.selected_tier,
          image: { url: r.image_url, width: r.width, height: r.height, format: 'png' },
          appliedConfiguration: {
            quality_tier: r.selected_tier,
            effective_resolution: `${r.width}x${r.height}`,
            steps: r.steps,
            model: r.model,
          },
          resourceMetrics: {
            latency_seconds: r.elapsed_seconds,
            measured_elapsed_seconds: r.elapsed_seconds,
            estimated_compute_work_units: r.compute_work_units,
            compute_savings_percent: r.savings_percent,
            relative_resource_units: r.compute_work_units,
            resource_savings_percent: r.savings_percent,
            generation_time_label: 'measured',
          },
          decisionRationale: {
            purpose_identified: r.inferred_purpose,
            recommended_tier: r.recommended_tier,
            selected_tier: r.selected_tier,
            tier_overridden: r.tier_overridden,
          },
        }));
        setHistory(mapped);
        setViewedResult(prev => prev || {
          job_id: mapped[0].id,
          status: 'success',
          image: mapped[0].image,
          applied_configuration: mapped[0].appliedConfiguration,
          resource_metrics: mapped[0].resourceMetrics,
          decision_rationale: mapped[0].decisionRationale,
          request_params: {
            prompt: mapped[0].prompt,
            intended_use: mapped[0].intended_use,
          },
        });
      } else {
        setHistory([]);
      }
    } catch {
      setHistory([]);
    }
  }, []);

  useEffect(() => {
    refreshHistory();
  }, [refreshHistory]);

  const toggleTheme = useCallback(() => {
    setTheme(curr => (curr === 'dark' ? 'light' : 'dark'));
  }, []);

  const { status, result, error, errorDetails, generate, reset } = useGeneration();

  const handleSubmit = useCallback(async (params) => {
    const data = await generate(params);
    if (data && data.job_id) {
      setViewedResult({
        ...data,
        request_params: {
          prompt: params.prompt,
          intended_use: data.decision_rationale?.purpose_identified,
        },
      });
      await refreshHistory();
    }
  }, [generate, refreshHistory]);

  const handleSelectForView = useCallback((item) => {
    setViewedResult({
      job_id: item.id,
      status: 'success',
      image: item.image,
      request_params: {
        prompt: item.prompt,
        intended_use: item.intended_use,
      },
      applied_configuration: item.appliedConfiguration,
      resource_metrics: item.resourceMetrics,
      decision_rationale: item.decisionRationale,
    });
    setActiveTab('studio');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const toggleCompare = useCallback((item) => {
    setSelectedForCompare(prev => {
      const exists = prev.some(c => c.id === item.id);
      if (exists) {
        return prev.filter(c => c.id !== item.id);
      }
      if (prev.length >= 2) {
        const next = [prev[0], item];
        setIsCompareModalOpen(true);
        return next;
      }
      const next = [...prev, item];
      if (next.length === 2) {
        setIsCompareModalOpen(true);
      }
      return next;
    });
  }, []);

  const handleClearHistory = useCallback(async () => {
    try {
      await clearHistoryApi();
    } catch {
      // Ignore
    }
    setHistory([]);
    setViewedResult(null);
    setSelectedForCompare([]);
  }, []);

  const handleSwitchTier = useCallback((targetTier) => {
    const curResult = viewedResult || result;
    if (!curResult) return;

    const curPrompt = curResult.request_params?.prompt || curResult.applied_configuration?.prompt_refinement || 'A simple educational illustration';

    handleSubmit({
      prompt: curPrompt,
      quality_tier: targetTier,
      color_preference: 'auto',
      mode: 'optimized',
    });
  }, [viewedResult, result, handleSubmit]);

  const activeResult = viewedResult || result;

  return (
    <div className="app">
      <AppHeader
        theme={theme}
        onToggleTheme={toggleTheme}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        historyCount={history.length}
      />

      <main className="main-content" aria-label="EcoGen AI Studio Workspace">
        {/* ── STUDIO TAB ────────────────────────────────────── */}
        {activeTab === 'studio' && (
          <div className="studio-container">
            {/* Hero Header */}
            <HeroSection />

            {/* 2-Column Generator Workspace */}
            <div className="workspace">
              <section className="workspace__form" aria-label="Generation settings">
                <GenerationForm onSubmit={handleSubmit} status={status} />
              </section>

              <section className="workspace__result" aria-label="Generation result" aria-live="polite">
                <ResultPanel
                  status={status}
                  result={activeResult}
                  error={error}
                  errorDetails={errorDetails}
                  onReset={() => {
                    reset();
                  }}
                  onSwitchTier={handleSwitchTier}
                />
              </section>
            </div>

            {/* Telemetry KPI Cards & Green Savings Banner */}
            {activeResult && <StudioTelemetry result={activeResult} />}

            {/* Recent Generations Grid */}
            <RecentGenerations
              history={history}
              activeResultId={activeResult?.job_id}
              onSelectForView={handleSelectForView}
              onToggleCompare={toggleCompare}
              selectedForCompare={selectedForCompare}
              onOpenCompareModal={() => setIsCompareModalOpen(true)}
            />
          </div>
        )}

        {/* ── RESOURCE TELEMETRY TAB (District Analytics) ───── */}
        {activeTab === 'analytics' && (
          <div className="tab-view-container">
            <AnalyticsDashboard sessionHistory={history} />
          </div>
        )}

        {/* ── RECENT TAB (Dedicated Real History & Compare) ─── */}
        {activeTab === 'history' && (
          <div className="tab-view-container">
            <GenerationHistory
              history={history}
              onSelectForView={handleSelectForView}
              onClearHistory={handleClearHistory}
            />
          </div>
        )}
      </main>

      {/* Side-by-Side Comparison Modal */}
      {isCompareModalOpen && selectedForCompare.length === 2 && (
        <CompareModal
          items={selectedForCompare}
          onClose={() => setIsCompareModalOpen(false)}
          onClear={() => {
            setSelectedForCompare([]);
            setIsCompareModalOpen(false);
          }}
        />
      )}

      <footer className="app-footer">
        <p className="footer-note">
          <strong>ResourceAware</strong> — Resource-Aware Image Generation for 300 Schools District.
        </p>
        <span className="footer-member">Production Local Integration · ROTCREW</span>
      </footer>
    </div>
  );
}
