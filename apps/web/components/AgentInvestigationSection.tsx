'use client';

import React, { useState } from 'react';
import { runAgentInvestigation, fetchTraceDetails, InvestigationResponse, TraceDetailResponse } from '@/lib/api';

interface AgentInvestigationSectionProps {
  incidentId: string;
}

export default function AgentInvestigationSection({ incidentId }: AgentInvestigationSectionProps) {
  const [loading, setLoading] = useState(false);
  const [investigationData, setInvestigationData] = useState<InvestigationResponse | null>(null);
  const [traceData, setTraceData] = useState<TraceDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRunInvestigation = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await runAgentInvestigation(incidentId, {
        max_steps: 20,
        max_retrieval_rounds: 3,
        max_reflection_rounds: 2,
      });
      setInvestigationData(res);

      if (res.run_id) {
        const trace = await fetchTraceDetails(res.run_id);
        setTraceData(trace);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to execute agent investigation');
    } finally {
      setLoading(false);
    }
  };

  const getClassificationBadgeClass = (classification?: string) => {
    switch (classification) {
      case 'HIGHLY_COMPATIBLE':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
      case 'COMPATIBLE_WITH_DIFFERENCES':
        return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30';
      case 'LOW_COMPATIBILITY':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
      case 'INAPPLICABLE':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/30';
      default:
        return 'bg-slate-500/20 text-slate-300 border-slate-500/30';
    }
  };

  const getStatusBadgeClass = (status?: string) => {
    switch (status) {
      case 'SUPPORTED':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
      case 'PLAUSIBLE':
        return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30';
      case 'CONTRADICTED':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/30';
      default:
        return 'bg-slate-500/20 text-slate-300 border-slate-500/30';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex items-center justify-between p-4 bg-slate-900/60 rounded-xl border border-slate-800">
        <div>
          <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse"></span>
            Stage 4 Evidence-Backed Agentic Investigation Engine
          </h3>
          <p className="text-sm text-slate-400">
            Supervisor-routed multi-agent investigation comparing 9 infrastructure dimensions & competing hypotheses
          </p>
        </div>
        <button
          onClick={handleRunInvestigation}
          disabled={loading}
          className="px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 text-white font-medium rounded-lg shadow-lg shadow-cyan-500/20 transition-all flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
              Running Agents...
            </>
          ) : (
            <>⚡ Run Agent Investigation</>
          )}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-sm">
          ⚠️ {error}
        </div>
      )}

      {investigationData && (
        <div className="space-y-6">
          {/* Status & Confidence Summary Banner */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
              <div className="text-xs font-mono text-slate-400 uppercase">Run Status</div>
              <div className="text-lg font-semibold text-emerald-400 mt-1">{investigationData.status}</div>
            </div>
            <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
              <div className="text-xs font-mono text-slate-400 uppercase">Calibrated Confidence</div>
              <div className="text-2xl font-bold text-cyan-300 mt-1">
                {(investigationData.confidence * 100).toFixed(1)}%
              </div>
            </div>
            <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
              <div className="text-xs font-mono text-slate-400 uppercase">Termination Reason</div>
              <div className="text-xs font-mono text-slate-300 mt-2 truncate">
                {investigationData.termination_reason}
              </div>
            </div>
            <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
              <div className="text-xs font-mono text-slate-400 uppercase">Disagreements Persisted</div>
              <div className="text-2xl font-bold text-amber-400 mt-1">
                {investigationData.agent_disagreements?.length || 0}
              </div>
            </div>
          </div>

          {/* Competing Hypotheses Section */}
          <div className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl">
            <h4 className="text-sm font-mono font-semibold text-cyan-400 uppercase tracking-wider mb-4">
              🧪 Competing Hypotheses Evaluation
            </h4>
            {investigationData.selected_hypothesis && (
              <div className="space-y-3">
                <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                      {investigationData.selected_hypothesis.hypothesis_id}
                    </span>
                    <span className={`text-xs px-2.5 py-0.5 rounded-full border ${getStatusBadgeClass(investigationData.selected_hypothesis.status)}`}>
                      {investigationData.selected_hypothesis.status}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-slate-200 mt-2">
                    {investigationData.selected_hypothesis.statement}
                  </p>
                  <div className="mt-3 flex items-center gap-3">
                    <div className="flex-1 bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-cyan-400 h-full rounded-full"
                        style={{ width: `${investigationData.selected_hypothesis.confidence * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-xs font-mono text-cyan-400">
                      {(investigationData.selected_hypothesis.confidence * 100).toFixed(0)}% confidence
                    </span>
                  </div>
                  {investigationData.selected_hypothesis.supporting_evidence.length > 0 && (
                    <div className="mt-3 text-xs text-slate-400">
                      <span className="font-semibold text-emerald-400">Supporting Evidence Refs:</span>{' '}
                      {investigationData.selected_hypothesis.supporting_evidence.join(', ')}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* 9-Dimension Temporal Comparison Table */}
          <div className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl">
            <h4 className="text-sm font-mono font-semibold text-cyan-400 uppercase tracking-wider mb-4">
              ⏳ 9-Dimension Temporal Infrastructure Comparison
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-mono">
                    <th className="py-2.5 px-3">Dimension</th>
                    <th className="py-2.5 px-3">Historical Value</th>
                    <th className="py-2.5 px-3">Current Value</th>
                    <th className="py-2.5 px-3">Match</th>
                    <th className="py-2.5 px-3">Impact</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {investigationData.temporal_comparisons?.map((dim, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 font-mono text-cyan-300 capitalize">{dim.dimension.replace('_', ' ')}</td>
                      <td className="py-2.5 px-3 text-slate-300 font-mono">{JSON.stringify(dim.historical_value)}</td>
                      <td className="py-2.5 px-3 text-slate-300 font-mono">{JSON.stringify(dim.current_value)}</td>
                      <td className="py-2.5 px-3">
                        {dim.match ? (
                          <span className="text-emerald-400 font-semibold">✓ Match</span>
                        ) : (
                          <span className="text-amber-400 font-semibold">⚠ Drift</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-400">{dim.impact}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Historical Remediation Applicability */}
          {investigationData.remediation_applicability && (
            <div className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-mono font-semibold text-cyan-400 uppercase tracking-wider">
                  🛠️ Remediation Applicability Evaluation
                </h4>
                <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getClassificationBadgeClass(investigationData.remediation_applicability.classification)}`}>
                  {investigationData.remediation_applicability.classification}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
                  <div className="text-xs font-mono text-slate-400">Compatibility Score</div>
                  <div className="text-2xl font-bold text-cyan-300 mt-1">
                    {(investigationData.remediation_applicability.compatibility_score * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
                  <div className="text-xs font-mono text-slate-400">Target Historical Incident</div>
                  <div className="text-sm font-mono text-slate-200 mt-1">
                    {investigationData.remediation_applicability.historical_incident_id}
                  </div>
                </div>
              </div>

              {investigationData.remediation_applicability.supporting_differences.length > 0 && (
                <div>
                  <h5 className="text-xs font-mono text-emerald-400 uppercase mb-2">Supporting Signals</h5>
                  <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                    {investigationData.remediation_applicability.supporting_differences.map((sd: string, i: number) => (
                      <li key={i}>{sd}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Agent Disagreements */}
          {investigationData.agent_disagreements && investigationData.agent_disagreements.length > 0 && (
            <div className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-3">
              <h4 className="text-sm font-mono font-semibold text-amber-400 uppercase tracking-wider">
                ⚖️ Persisted Agent Disagreements & Resolution
              </h4>
              {investigationData.agent_disagreements.map((disag, idx) => (
                <div key={idx} className="p-4 bg-slate-950/60 border border-amber-500/20 rounded-lg space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono text-slate-400">
                    <span>{disag.agent_a} ↔ {disag.agent_b}</span>
                    <span className="text-cyan-400">Resolved by {disag.resolved_by}</span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                    <div className="p-2 bg-slate-900/60 rounded border border-slate-800 text-slate-300">
                      <span className="font-semibold text-slate-400 font-mono">{disag.agent_a}:</span> {disag.position_a}
                    </div>
                    <div className="p-2 bg-slate-900/60 rounded border border-slate-800 text-slate-300">
                      <span className="font-semibold text-slate-400 font-mono">{disag.agent_b}:</span> {disag.position_b}
                    </div>
                  </div>
                  {disag.resolution && (
                    <div className="text-xs text-emerald-300 bg-emerald-500/10 p-2 rounded border border-emerald-500/20">
                      <span className="font-semibold font-mono">Resolution:</span> {disag.resolution}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Agent Trace Timeline */}
          {traceData && traceData.agent_steps && (
            <div className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4">
              <h4 className="text-sm font-mono font-semibold text-cyan-400 uppercase tracking-wider">
                📜 Agent Execution Trace Timeline
              </h4>
              <div className="space-y-3">
                {traceData.agent_steps.map((st, i) => (
                  <div key={i} className="flex items-start gap-4 p-3 bg-slate-950/60 border border-slate-800 rounded-lg">
                    <div className="w-8 h-8 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 flex items-center justify-center text-xs font-mono font-bold shrink-0">
                      {i + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-slate-200">{st.agent_name}</span>
                        <span className="text-xs font-mono text-slate-400">{st.duration_ms}ms</span>
                      </div>
                      <p className="text-xs text-slate-300 mt-1">{st.output_summary}</p>
                      <div className="mt-2 flex items-center gap-4 text-xs font-mono text-slate-400">
                        <span>Confidence: {(st.confidence * 100).toFixed(0)}%</span>
                        <span>Tool Calls: {st.tool_calls.length}</span>
                      </div>
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
