import { useState, useEffect, useMemo } from 'react';
import {
  calculateSessionMetrics,
  BASELINE_HQ_UNITS,
} from '../services/resourceEstimation';
import { fetchAnalyticsApi } from '../services/apiService';
import './AnalyticsDashboard.css';

/**
 * AnalyticsDashboard
 *
 * Visualizes generation metrics, tier distribution, total relative resource units,
 * and savings vs High Quality baseline.
 * Features:
 * 1. Real Database Telemetry (aggregated strictly from genuine SQLite generation records)
 * 2. District 300 Schools Projection (interactive curriculum planning model, clearly labeled)
 */
export function AnalyticsDashboard({ sessionHistory = [] }) {
  const [districtSchoolsCount, setDistrictSchoolsCount] = useState(300);
  const [backendAnalytics, setBackendAnalytics] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    fetchAnalyticsApi()
      .then((data) => {
        if (isMounted && data) {
          setBackendAnalytics(data);
        }
      })
      .catch(() => {})
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [sessionHistory.length]);

  // Derive active live metrics: prefer real backend persistence records
  const sessionFallback = useMemo(() => {
    return calculateSessionMetrics(sessionHistory);
  }, [sessionHistory]);

  const activeMetrics = useMemo(() => {
    if (backendAnalytics && !backendAnalytics.is_empty && backendAnalytics.total_generations > 0) {
      return {
        totalGenerations: backendAnalytics.total_generations,
        totalUnits: backendAnalytics.total_compute_units,
        baselineUnits: backendAnalytics.baseline_units,
        unitsSaved: backendAnalytics.units_saved,
        overallSavingsPercent: backendAnalytics.overall_savings_percent,
        measuredAvgLatency: backendAnalytics.avg_elapsed_seconds,
        ecoCount: backendAnalytics.eco_count,
        standardCount: backendAnalytics.standard_count,
        highQualityCount: backendAnalytics.high_count,
        overriddenCount: backendAnalytics.overridden_count || 0,
        source: 'database',
      };
    }
    return {
      ...sessionFallback,
      overriddenCount: sessionHistory.filter(s => s.decisionRationale?.tier_overridden).length,
      source: 'session',
    };
  }, [backendAnalytics, sessionFallback, sessionHistory]);

  // Dynamically compute simulated district metrics based on school slider
  const dynamicDistrictData = useMemo(() => {
    const imagesPerSchool = 40;
    const totalGen = districtSchoolsCount * imagesPerSchool;
    const ecoCount = Math.round(totalGen * 0.75);
    const stdCount = Math.round(totalGen * 0.20);
    const hqCount = Math.round(totalGen * 0.05);

    const actualUnits = (ecoCount * 0.1339) + (stdCount * 0.4286) + (hqCount * 1.0);
    const naiveUnits = totalGen * BASELINE_HQ_UNITS;
    const savedUnits = Math.round((naiveUnits - actualUnits) * 10) / 10;
    const savingsPct = Math.round((savedUnits / naiveUnits) * 100);

    return {
      totalSchools: districtSchoolsCount,
      totalGen,
      ecoCount,
      stdCount,
      hqCount,
      actualUnits: Math.round(actualUnits * 10) / 10,
      naiveUnits: Math.round(naiveUnits * 10) / 10,
      savedUnits,
      savingsPct,
    };
  }, [districtSchoolsCount]);

  return (
    <div className="analytics-container">
      {/* ── SECTION 1: REAL GENERATION TELEMETRY ─────────────────── */}
      <section className="analytics-section" aria-labelledby="session-analytics-title">
        <div className="section-header">
          <div>
            <span className="section-kicker">
              {activeMetrics.source === 'database' ? 'Persistent Database Telemetry' : 'Live Session Telemetry'}
            </span>
            <h2 id="session-analytics-title">Real Generation Resource Telemetry</h2>
          </div>
          <span className="live-status-pill">
            <span className="live-dot" />{' '}
            {isLoading
              ? 'Synchronizing Database…'
              : activeMetrics.totalGenerations > 0
                ? `${activeMetrics.totalGenerations} Real Records (${activeMetrics.source === 'database' ? 'persisted' : 'session'})`
                : '0 Records (Empty State)'}
          </span>
        </div>

        {/* Top 4 KPI Metric Cards */}
        <div className="kpi-grid">
          <div className="kpi-card">
            <span className="kpi-card__label">Total Generations</span>
            <span className="kpi-card__val">{activeMetrics.totalGenerations}</span>
            <span className="kpi-card__caption">
              {activeMetrics.source === 'database' ? 'Persisted SQLite database records' : 'Active browser session records'}
            </span>
          </div>

          <div className="kpi-card">
            <span className="kpi-card__label">Total Resource Units</span>
            <span className="kpi-card__val">{activeMetrics.totalUnits}</span>
            <span className="kpi-card__caption">
              vs {activeMetrics.baselineUnits} baseline units (High = 1.0)
            </span>
          </div>

          <div className="kpi-card kpi-card--green">
            <span className="kpi-card__label">Resource Units Conserved</span>
            <span className="kpi-card__val kpi-card__val--green">
              {activeMetrics.unitsSaved}
            </span>
            <span className="kpi-card__caption">
              {activeMetrics.overallSavingsPercent}% overall relative savings
            </span>
          </div>

          <div className="kpi-card">
            <span className="kpi-card__label">Avg Measured Latency</span>
            <span className="kpi-card__val">
              {activeMetrics.measuredAvgLatency}s
            </span>
            <span className="kpi-card__caption">Measured backend server elapsed time</span>
          </div>
        </div>

        {/* Tier Distribution Visual Bar */}
        <div className="distribution-panel panel">
          <div className="dist-header">
            <h3>Tier Distribution ({activeMetrics.source === 'database' ? 'Database Records' : 'Session'})</h3>
            <span className="dist-total">
              Eco: {activeMetrics.ecoCount} • Standard: {activeMetrics.standardCount} • High Quality: {activeMetrics.highQualityCount}
              {activeMetrics.overriddenCount > 0 && ` • Overrides: ${activeMetrics.overriddenCount}`}
            </span>
          </div>

          {activeMetrics.totalGenerations > 0 ? (
            <>
              <div className="tier-dist-track" role="progressbar" aria-label="Tier distribution bar">
                {activeMetrics.ecoCount > 0 && (
                  <div
                    className="dist-segment dist-segment--eco"
                    style={{ width: `${(activeMetrics.ecoCount / activeMetrics.totalGenerations) * 100}%` }}
                    title={`Eco: ${activeMetrics.ecoCount}`}
                  />
                )}
                {activeMetrics.standardCount > 0 && (
                  <div
                    className="dist-segment dist-segment--standard"
                    style={{ width: `${(activeMetrics.standardCount / activeMetrics.totalGenerations) * 100}%` }}
                    title={`Standard: ${activeMetrics.standardCount}`}
                  />
                )}
                {activeMetrics.highQualityCount > 0 && (
                  <div
                    className="dist-segment dist-segment--hq"
                    style={{ width: `${(activeMetrics.highQualityCount / activeMetrics.totalGenerations) * 100}%` }}
                    title={`High Quality: ${activeMetrics.highQualityCount}`}
                  />
                )}
              </div>

              <div className="dist-legend">
                <div className="legend-item">
                  <span className="legend-dot legend-dot--eco" />
                  <span>Eco (0.134 units): {activeMetrics.ecoCount} ({Math.round((activeMetrics.ecoCount / activeMetrics.totalGenerations) * 100)}%)</span>
                </div>
                <div className="legend-item">
                  <span className="legend-dot legend-dot--standard" />
                  <span>Standard (0.429 units): {activeMetrics.standardCount} ({Math.round((activeMetrics.standardCount / activeMetrics.totalGenerations) * 100)}%)</span>
                </div>
                <div className="legend-item">
                  <span className="legend-dot legend-dot--hq" />
                  <span>High (1.000 unit): {activeMetrics.highQualityCount} ({Math.round((activeMetrics.highQualityCount / activeMetrics.totalGenerations) * 100)}%)</span>
                </div>
                {activeMetrics.overriddenCount > 0 && (
                  <div className="legend-item">
                    <span className="legend-dot" style={{ backgroundColor: 'var(--amber-500, #f59e0b)' }} />
                    <span>User Overrides: {activeMetrics.overriddenCount}</span>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="dist-empty">
              <span>No generations executed yet. Generate images in Studio to view real telemetry and compute metrics.</span>
            </div>
          )}
        </div>
      </section>

      {/* ── SECTION 2: 300 SCHOOLS DISTRICT SIMULATION ──────────── */}
      <section className="analytics-section analytics-section--demo" aria-labelledby="district-demo-title">
        {/* Mandatory Explicit Disclaimer Badge */}
        <div className="demo-data-banner" role="note">
          <span className="demo-badge">SAMPLE DEMO DATA</span>
          <span className="demo-banner-text">
            <strong>Sample demo data:</strong> Illustrative educational district simulation based on {dynamicDistrictData.totalSchools} schools.
            Uses the unified normalized compute-work model (Eco=0.134, Standard=0.429, High=1.000).
          </span>
        </div>

        <div className="section-header">
          <div>
            <span className="section-kicker">District Projection</span>
            <h2 id="district-demo-title">District-Wide Educational Impact (300 Schools)</h2>
            <p className="section-desc">
              Education offices support teachers generating worksheets, colouring sheets, and posters.
              Compare right-sizing vs. naive all-High-Quality generation across {dynamicDistrictData.totalSchools} schools.
            </p>
          </div>

          {/* Interactive School Count Slider */}
          <div className="schools-slider-wrap">
            <label htmlFor="schools-slider">
              Simulated District Schools: <strong>{districtSchoolsCount}</strong>
            </label>
            <input
              id="schools-slider"
              type="range"
              min="50"
              max="500"
              step="25"
              value={districtSchoolsCount}
              onChange={(e) => setDistrictSchoolsCount(Number(e.target.value))}
            />
          </div>
        </div>

        {/* District KPI Grid */}
        <div className="kpi-grid">
          <div className="kpi-card">
            <span className="kpi-card__label">Monthly District Images</span>
            <span className="kpi-card__val">
              {dynamicDistrictData.totalGen.toLocaleString()}
            </span>
            <span className="kpi-card__caption">
              ~40 instructional assets / school / month
            </span>
          </div>

          <div className="kpi-card">
            <span className="kpi-card__label">ResourceAware Consumption</span>
            <span className="kpi-card__val">
              {dynamicDistrictData.actualUnits.toLocaleString()}
            </span>
            <span className="kpi-card__caption">
              Total estimated relative units
            </span>
          </div>

          <div className="kpi-card kpi-card--green">
            <span className="kpi-card__label">Relative Units Conserved</span>
            <span className="kpi-card__val kpi-card__val--green">
              {dynamicDistrictData.savedUnits.toLocaleString()}
            </span>
            <span className="kpi-card__caption">
              <strong>{dynamicDistrictData.savingsPct}% reduction</strong> vs naive HQ baseline
            </span>
          </div>

          <div className="kpi-card">
            <span className="kpi-card__label">Naive Baseline (Unmanaged)</span>
            <span className="kpi-card__val">
              {dynamicDistrictData.naiveUnits.toLocaleString()}
            </span>
            <span className="kpi-card__caption">If every image requested 4 units</span>
          </div>
        </div>

        {/* Visual Comparison: District Savings Bar */}
        <div className="district-comparison-card panel">
          <h3>District Monthly Compute Comparison</h3>
          
          <div className="district-bars">
            <div className="district-bar-row">
              <div className="district-bar-row__header">
                <span>Naive Legacy Practice (All images at High Quality)</span>
                <span className="bar-val">{dynamicDistrictData.naiveUnits.toLocaleString()} units</span>
              </div>
              <div className="district-bar-track">
                <div className="district-bar-fill district-bar-fill--baseline" style={{ width: '100%' }} />
              </div>
            </div>

            <div className="district-bar-row">
              <div className="district-bar-row__header">
                <span>ResourceAware Purpose-Tailored Allocation</span>
                <span className="bar-val bar-val--green">{dynamicDistrictData.actualUnits.toLocaleString()} units</span>
              </div>
              <div className="district-bar-track">
                <div
                  className="district-bar-fill district-bar-fill--optimized"
                  style={{ width: `${(dynamicDistrictData.actualUnits / dynamicDistrictData.naiveUnits) * 100}%` }}
                />
              </div>
            </div>
          </div>

          <div className="district-breakdown-table-wrap">
            <table className="district-table" aria-label="300 schools purpose breakdown table">
              <thead>
                <tr>
                  <th>Educational Purpose</th>
                  <th>Share</th>
                  <th>Monthly Volume</th>
                  <th>Quality Tier</th>
                  <th>Units / Gen</th>
                  <th>Total Units</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Colouring Sheets &amp; Line Outlines</td>
                  <td>40%</td>
                  <td>{(dynamicDistrictData.totalGen * 0.4).toLocaleString()}</td>
                  <td><span className="table-badge table-badge--eco">Eco</span></td>
                  <td>0.134</td>
                  <td>{Math.round(dynamicDistrictData.totalGen * 0.4 * 0.1339).toLocaleString()}</td>
                </tr>
                <tr>
                  <td>Flashcards &amp; Worksheet Illustrations</td>
                  <td>35%</td>
                  <td>{(dynamicDistrictData.totalGen * 0.35).toLocaleString()}</td>
                  <td><span className="table-badge table-badge--eco">Eco</span></td>
                  <td>0.134</td>
                  <td>{Math.round(dynamicDistrictData.totalGen * 0.35 * 0.1339).toLocaleString()}</td>
                </tr>
                <tr>
                  <td>Classroom Educational Posters</td>
                  <td>20%</td>
                  <td>{(dynamicDistrictData.totalGen * 0.20).toLocaleString()}</td>
                  <td><span className="table-badge table-badge--std">Standard</span></td>
                  <td>0.429</td>
                  <td>{Math.round(dynamicDistrictData.totalGen * 0.20 * 0.4286).toLocaleString()}</td>
                </tr>
                <tr>
                  <td>Premium Auditorium &amp; District Posters</td>
                  <td>5%</td>
                  <td>{(dynamicDistrictData.totalGen * 0.05).toLocaleString()}</td>
                  <td><span className="table-badge table-badge--hq">High Quality</span></td>
                  <td>1.000</td>
                  <td>{Math.round(dynamicDistrictData.totalGen * 0.05 * 1.0).toLocaleString()}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="district-summary-note">
            <span className="summary-icon">🌱</span>
            <span>
              <strong>District Impact Takeaway:</strong> By defaulting colouring sheets, flashcards, and worksheet diagrams to Eco tier (0.134 units) and reserving High Quality (1.000 unit) strictly for official print posters, <strong>{dynamicDistrictData.totalSchools} schools eliminate {dynamicDistrictData.savedUnits.toLocaleString()} compute-work units every month</strong> — saving {dynamicDistrictData.savingsPct}% of inference compute.
            </span>
          </div>
        </div>
      </section>
    </div>
  );
}
