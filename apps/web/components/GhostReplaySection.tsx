'use client';

import React, { useState } from 'react';
import {
  triggerIncidentReplay,
  triggerCounterfactualReplay,
  triggerDriftSimulation,
  fetchReplayProvenance,
  ReplayResultResponse,
  ReplayProvenanceResponse,
} from '@/lib/api';

interface GhostReplaySectionProps {
  incidentId?: string;
}

export default function GhostReplaySection({ incidentId = 'inc-sample-01' }: GhostReplaySectionProps) {
  const [loading, setLoading] = useState(false);
  const [replayData, setReplayData] = useState<ReplayResultResponse | null>(null);
  const [provenanceData, setProvenanceData] = useState<ReplayProvenanceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const handleHistoricalReplay = async () => {
    setLoading(true);
    setError(null);
    setActionSuccess(null);
    try {
      const res = await triggerIncidentReplay(incidentId, { mode: 'HISTORICAL_REPLAY' });
      setReplayData(res);
      const prov = await fetchReplayProvenance(res.replay_id);
      setProvenanceData(prov);
      setActionSuccess(`Historical replay completed cleanly. Score: ${(res.score.overall_score * 100).toFixed(1)}% (${res.score.classification})`);
    } catch (err: any) {
      setError(err.message || 'Historical replay failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCounterfactualReplay = async () => {
    setLoading(true);
    setError(null);
    setActionSuccess(null);
    try {
      const res = await triggerCounterfactualReplay({
        counterfactual_parameters: { service_version: 'v4.3.0', db_version: 'CockroachDB v24.1.0' },
      });
      setReplayData(res);
      const prov = await fetchReplayProvenance(res.replay_id);
      setProvenanceData(prov);
      setActionSuccess(`Counterfactual simulation completed. Score: ${(res.score.overall_score * 100).toFixed(1)}% (${res.score.classification})`);
    } catch (err: any) {
      setError(err.message || 'Counterfactual simulation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDriftSimulation = async () => {
    setLoading(true);
    setError(null);
    setActionSuccess(null);
    try {
      const res = await triggerDriftSimulation({
        counterfactual_parameters: { drift_dimension: 'capacity_characteristics', capacity_ratio: 0.50 },
      });
      setReplayData(res);
      const prov = await fetchReplayProvenance(res.replay_id);
      setProvenanceData(prov);
      setActionSuccess(`Infrastructure drift simulation completed. Score: ${(res.score.overall_score * 100).toFixed(1)}% (${res.score.classification})`);
    } catch (err: any) {
      setError(err.message || 'Drift simulation failed');
    } finally {
      setLoading(false);
    }
  };

  const getScoreBadgeClass = (cls?: string) => {
    switch (cls) {
      case 'EXCELLENT':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
      case 'RELIABLE':
        return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30';
      case 'DEGRADED':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
      case 'FAILED':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/30';
      default:
        return 'bg-slate-500/20 text-slate-300 border-slate-500/30';
    }
  };

  return (
    <div className="space-y-6 pt-4 border-t border-slate-800">
      {/* Top Header & Actions */}
      <div className="flex items-center justify-between p-4 bg-slate-900/60 rounded-xl border border-slate-800">
        <div>
          <h4 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-400 animate-pulse"></span>
            Stage 8 Ghost Replay & Simulation Engine
          </h4>
          <p className="text-xs text-slate-400">
            Replays past incidents, simulates counterfactual drift, evaluates reasoning reliability & detects memory regressions without mutating production
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleHistoricalReplay}
            disabled={loading}
            className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs rounded border border-slate-700 transition"
          >
            🧪 Historical Replay
          </button>
          <button
            onClick={handleCounterfactualReplay}
            disabled={loading}
            className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs rounded border border-slate-700 transition"
          >
            🔀 Counterfactual
          </button>
          <button
            onClick={handleDriftSimulation}
            disabled={loading}
            className="px-4 py-1.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 disabled:opacity-50 text-white font-semibold text-xs rounded shadow-lg shadow-indigo-500/20 transition flex items-center gap-1.5"
          >
            {loading ? 'Simulating...' : '⚡ Drift Simulation'}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs font-mono">
          ⚠️ {error}
        </div>
      )}

      {actionSuccess && (
        <div className="p-4 bg-indigo-500/10 border border-indigo-500/30 rounded-xl text-indigo-300 text-xs font-mono">
          ✓ {actionSuccess}
        </div>
      )}

      {replayData && (
        <div className="space-y-6">
          {/* Replay Score Breakdown Card */}
          <div className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4 font-mono text-xs">
            <div className="flex items-center justify-between">
              <span className="text-indigo-300 font-bold uppercase">📊 Deterministic Replay Score Breakdown</span>
              <span className={`px-2.5 py-1 rounded font-bold border uppercase ${getScoreBadgeClass(replayData.score.classification)}`}>
                {replayData.score.classification} ({(replayData.score.overall_score * 100).toFixed(1)}%)
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-6 gap-3 text-[11px] text-center">
              <div className="p-2.5 bg-slate-950/60 rounded border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase">Diagnosis</div>
                <div className="text-slate-200 font-bold mt-1">{(replayData.score.diagnosis_accuracy * 100).toFixed(0)}%</div>
              </div>
              <div className="p-2.5 bg-slate-950/60 rounded border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase">Evidence</div>
                <div className="text-slate-200 font-bold mt-1">{(replayData.score.evidence_accuracy * 100).toFixed(0)}%</div>
              </div>
              <div className="p-2.5 bg-slate-950/60 rounded border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase">Remediation</div>
                <div className="text-slate-200 font-bold mt-1">{(replayData.score.remediation_accuracy * 100).toFixed(0)}%</div>
              </div>
              <div className="p-2.5 bg-slate-950/60 rounded border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase">Outcome</div>
                <div className="text-slate-200 font-bold mt-1">{(replayData.score.outcome_accuracy * 100).toFixed(0)}%</div>
              </div>
              <div className="p-2.5 bg-slate-950/60 rounded border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase">Temporal</div>
                <div className="text-slate-200 font-bold mt-1">{(replayData.score.temporal_compatibility * 100).toFixed(0)}%</div>
              </div>
              <div className="p-2.5 bg-slate-950/60 rounded border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase">Provenance</div>
                <div className="text-slate-200 font-bold mt-1">{(replayData.score.provenance_completeness * 100).toFixed(0)}%</div>
              </div>
            </div>
          </div>

          {/* Simulation Timeline & Step Diffs */}
          {provenanceData && (
            <div className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4">
              <h5 className="text-xs font-mono font-semibold text-indigo-400 uppercase tracking-wider flex items-center justify-between">
                <span>⚙️ Simulation Timeline (Zero Live Mutation)</span>
                <span className="text-[10px] bg-slate-800 text-indigo-300 px-2 py-0.5 rounded border border-slate-700">
                  simulated_only = true
                </span>
              </h5>

              <div className="space-y-3 font-mono text-xs">
                {provenanceData.steps?.map((step, idx) => (
                  <div key={idx} className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center text-[10px] font-bold">
                          {step.step_order}
                        </span>
                        <span className="font-bold text-slate-200 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                          {step.action_type}
                        </span>
                        <span className="text-slate-400 text-[11px]">{step.target_resource}</span>
                      </div>
                      <span className="text-emerald-400 text-[10px] uppercase font-bold">{step.status}</span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px]">
                      <div className="p-3 bg-slate-900/60 rounded border border-slate-800">
                        <div className="text-[10px] text-slate-500 uppercase">Simulated Pre-State</div>
                        <pre className="text-slate-300 mt-1 overflow-x-auto">{JSON.stringify(step.simulated_pre_state, null, 2)}</pre>
                      </div>
                      <div className="p-3 bg-slate-900/60 rounded border border-slate-800">
                        <div className="text-[10px] text-indigo-400 uppercase">Simulated Post-State</div>
                        <pre className="text-slate-300 mt-1 overflow-x-auto">{JSON.stringify(step.simulated_post_state, null, 2)}</pre>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Memory Regression Panel */}
          {provenanceData && provenanceData.regressions && provenanceData.regressions.length > 0 && (
            <div className="p-5 bg-slate-900/40 border border-amber-500/30 rounded-xl space-y-3">
              <h5 className="text-xs font-mono font-semibold text-amber-400 uppercase tracking-wider">
                ⚠️ Memory Regression Panel (Stage 7 Governance Review Queue)
              </h5>
              <div className="space-y-2 font-mono text-xs">
                {provenanceData.regressions.map((reg, i) => (
                  <div key={i} className="p-3 bg-slate-950/60 border border-amber-500/30 rounded-lg flex items-center justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded text-[10px] font-bold">
                          {reg.regression_type}
                        </span>
                        <span className="text-slate-200 font-bold">Memory ID: {reg.memory_id}</span>
                      </div>
                      <p className="text-slate-400 text-[11px]">{reg.explanation}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-rose-400 font-bold">Delta: {reg.score_delta.toFixed(2)}</div>
                      <div className="text-slate-500 text-[10px]">Score: {reg.previous_confidence.toFixed(2)} → {reg.observed_confidence.toFixed(2)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
