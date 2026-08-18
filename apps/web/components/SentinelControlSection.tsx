'use client';

import React, { useState, useEffect } from 'react';
import {
  fetchSentinelStatus,
  startSentinel,
  stopSentinel,
  pauseSentinel,
  resumeSentinel,
  ingestTelemetryEvent,
  fetchSentinelDecisions,
  SentinelHealthResponse,
} from '@/lib/api';

export default function SentinelControlSection() {
  const [loading, setLoading] = useState(false);
  const [statusData, setStatusData] = useState<SentinelHealthResponse | null>(null);
  const [decisions, setDecisions] = useState<any[]>([]);
  const [selectedMode, setSelectedMode] = useState<string>('DETECT_INVESTIGATE_AND_PLAN');
  const [simMetricValue, setSimMetricValue] = useState<number>(92.5);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const loadSentinelState = async () => {
    try {
      const st = await fetchSentinelStatus();
      if (st) {
        setStatusData(st);
        setSelectedMode(st.mode);
      }
      const decs = await fetchSentinelDecisions(10);
      setDecisions(decs);
    } catch (err: any) {
      console.error('Failed to load sentinel state:', err);
    }
  };

  useEffect(() => {
    loadSentinelState();
    const interval = setInterval(loadSentinelState, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleStart = async () => {
    setLoading(true);
    setError(null);
    setActionSuccess(null);
    try {
      const res = await startSentinel({ mode: selectedMode, poll_interval_seconds: 30 });
      setStatusData(res);
      setActionSuccess(`Sentinel started in mode '${res.mode}'.`);
    } catch (err: any) {
      setError(err.message || 'Failed to start sentinel');
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    setError(null);
    setActionSuccess(null);
    try {
      const res = await stopSentinel();
      setStatusData(res);
      setActionSuccess('Sentinel stopped cleanly.');
    } catch (err: any) {
      setError(err.message || 'Failed to stop sentinel');
    } finally {
      setLoading(false);
    }
  };

  const handlePause = async () => {
    setLoading(true);
    setError(null);
    setActionSuccess(null);
    try {
      const res = await pauseSentinel({ duration_seconds: 300 });
      setStatusData(res);
      setActionSuccess('Sentinel paused for 300s.');
    } catch (err: any) {
      setError(err.message || 'Failed to pause sentinel');
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateEvent = async () => {
    setLoading(true);
    setError(null);
    setActionSuccess(null);
    try {
      const res = await ingestTelemetryEvent({
        source: 'CloudWatch',
        event_type: 'CPU_SPIKE_CRITICAL',
        resource_id: 'i-auth-ec2-01',
        severity: 'HIGH',
        metric_name: 'CPUUtilization',
        metric_value: simMetricValue,
        baseline_value: 30.0,
        region: 'us-east-1',
      });
      setActionSuccess(`Simulated Telemetry Event Ingested! Decision: ${res.decision}. Incident ID: ${res.incident_id || 'None'}`);
      loadSentinelState();
    } catch (err: any) {
      setError(err.message || 'Telemetry simulation failed');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadgeClass = (st?: string) => {
    switch (st) {
      case 'RUNNING':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
      case 'PAUSED':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
      case 'STOPPED':
        return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
      case 'FAILED':
      case 'DEGRADED':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/30';
      default:
        return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    }
  };

  return (
    <div className="space-y-6 pt-4 border-t border-slate-800">
      {/* Header & Controls */}
      <div className="p-5 bg-slate-900/60 rounded-xl border border-slate-800 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h4 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <span className={`w-3 h-3 rounded-full ${statusData?.status === 'RUNNING' ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`}></span>
              Stage 9 Continuous Autonomous Sentinel
            </h4>
            <p className="text-xs text-slate-400">
              Continuously monitors telemetry, computes anomaly scores, suppresses duplicate alert storms, correlates signals into incidents & safely triggers Stage 4-8 pipelines.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className={`px-3 py-1 rounded text-xs font-bold font-mono border uppercase ${getStatusBadgeClass(statusData?.status)}`}>
              {statusData?.status || 'STOPPED'}
            </span>

            {statusData?.status === 'RUNNING' ? (
              <>
                <button
                  onClick={handlePause}
                  disabled={loading}
                  className="px-3.5 py-1.5 bg-amber-600/80 hover:bg-amber-600 text-white font-medium text-xs rounded transition"
                >
                  ⏸ Pause
                </button>
                <button
                  onClick={handleStop}
                  disabled={loading}
                  className="px-3.5 py-1.5 bg-rose-600/80 hover:bg-rose-600 text-white font-medium text-xs rounded transition"
                >
                  ⏹ Stop
                </button>
              </>
            ) : (
              <button
                onClick={handleStart}
                disabled={loading}
                className="px-4 py-1.5 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-semibold text-xs rounded shadow-lg shadow-emerald-500/20 transition flex items-center gap-1.5"
              >
                ▶ Start Sentinel
              </button>
            )}
          </div>
        </div>

        {/* Mode Selector */}
        <div className="flex items-center gap-4 text-xs font-mono text-slate-300 pt-2 border-t border-slate-800">
          <span>Sentinel Mode:</span>
          {['OBSERVE_ONLY', 'DETECT_AND_INVESTIGATE', 'DETECT_INVESTIGATE_AND_PLAN'].map((mode) => (
            <label key={mode} className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="radio"
                name="sentinelMode"
                value={mode}
                checked={selectedMode === mode}
                onChange={() => setSelectedMode(mode)}
                className="text-emerald-500 focus:ring-0"
              />
              <span className={selectedMode === mode ? 'text-emerald-400 font-bold' : 'text-slate-400'}>
                {mode}
              </span>
            </label>
          ))}
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs font-mono">
          ⚠️ {error}
        </div>
      )}

      {actionSuccess && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-300 text-xs font-mono">
          ✓ {actionSuccess}
        </div>
      )}

      {/* Live Metrics Grid */}
      {statusData && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3 font-mono text-xs">
          <div className="p-3 bg-slate-900/40 rounded-xl border border-slate-800 text-center">
            <div className="text-[10px] text-slate-500 uppercase">Events Processed</div>
            <div className="text-base font-bold text-slate-200 mt-1">{statusData.metrics.events_processed}</div>
          </div>
          <div className="p-3 bg-slate-900/40 rounded-xl border border-slate-800 text-center">
            <div className="text-[10px] text-slate-500 uppercase">Alerts Created</div>
            <div className="text-base font-bold text-cyan-400 mt-1">{statusData.metrics.alerts_created}</div>
          </div>
          <div className="p-3 bg-slate-900/40 rounded-xl border border-slate-800 text-center">
            <div className="text-[10px] text-slate-500 uppercase">Alerts Suppressed</div>
            <div className="text-base font-bold text-amber-400 mt-1">{statusData.metrics.alerts_suppressed}</div>
          </div>
          <div className="p-3 bg-slate-900/40 rounded-xl border border-slate-800 text-center">
            <div className="text-[10px] text-slate-500 uppercase">Correlated Incidents</div>
            <div className="text-base font-bold text-emerald-400 mt-1">{statusData.metrics.incidents_correlated}</div>
          </div>
          <div className="p-3 bg-slate-900/40 rounded-xl border border-slate-800 text-center">
            <div className="text-[10px] text-slate-500 uppercase">Investigations</div>
            <div className="text-base font-bold text-purple-400 mt-1">{statusData.metrics.investigations_triggered}</div>
          </div>
          <div className="p-3 bg-slate-900/40 rounded-xl border border-slate-800 text-center">
            <div className="text-[10px] text-slate-500 uppercase">Plans Proposed</div>
            <div className="text-base font-bold text-teal-400 mt-1">{statusData.metrics.plans_created}</div>
          </div>
        </div>
      )}

      {/* Simulated Telemetry Event Ingestor */}
      <div className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-3 font-mono text-xs">
        <h5 className="font-semibold text-emerald-400 uppercase tracking-wider">
          📡 Telemetry Event Ingestion Simulator
        </h5>
        <div className="flex items-center gap-3">
          <span className="text-slate-400 text-[11px]">Simulate Metric Value (CPUUtilization %):</span>
          <input
            type="number"
            value={simMetricValue}
            onChange={(e) => setSimMetricValue(parseFloat(e.target.value))}
            className="w-24 px-3 py-1.5 bg-slate-950 border border-slate-700 rounded text-slate-100 font-mono text-xs"
          />
          <button
            onClick={handleSimulateEvent}
            disabled={loading}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs rounded border border-slate-700 transition"
          >
            ⚡ Emit Telemetry Event
          </button>
        </div>
      </div>

      {/* Recent Sentinel Decisions Audit Log */}
      {decisions.length > 0 && (
        <div className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-3 font-mono text-xs">
          <h5 className="font-semibold text-cyan-400 uppercase tracking-wider">
            📜 Recent Sentinel Decisions Audit Trail
          </h5>
          <div className="space-y-2">
            {decisions.map((dec, i) => (
              <div key={i} className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg flex items-center justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 px-2 py-0.5 rounded text-[10px] font-bold uppercase">
                      {dec.decision_type}
                    </span>
                    <span className="text-slate-200 font-bold">{dec.decision}</span>
                  </div>
                  <p className="text-slate-400 text-[11px]">{dec.reason}</p>
                </div>
                <div className="text-right">
                  <div className="text-slate-300 text-[11px]">Confidence: {(dec.confidence * 100).toFixed(0)}%</div>
                  <div className="text-slate-500 text-[10px]">{new Date(dec.created_at).toLocaleTimeString()}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
