import React from 'react';
import { CheckCircle2, XCircle, Brain, Sparkles, AlertTriangle, ShieldCheck, Database, Server } from 'lucide-react';

interface HistoricalCandidate {
  incident_id: string;
  rank: number;
  title: string;
  service: string;
  region: string;
  severity: string;
  status: string;
  hybrid_score: number;
  structured_score: number;
  semantic_score: number;
  outcome_score: number;
  matched_fields: Record<string, boolean>;
  outcome_summary: string;
  failed_actions: Array<{
    command: string;
    tool: string;
    target: string;
    reason: string;
    error_message?: string;
  }>;
  successful_actions: Array<{
    command: string;
    tool: string;
    target: string;
    reason: string;
  }>;
  infrastructure_snapshot_summary: {
    db_version: string;
    service_version: string;
    region: string;
  };
}

interface HistoricalMemorySectionProps {
  candidates?: HistoricalCandidate[];
  incidentId?: string;
}

export default function HistoricalMemorySection({ candidates: initialCandidates, incidentId }: HistoricalMemorySectionProps) {
  const [candidates, setCandidates] = React.useState<HistoricalCandidate[]>(initialCandidates || []);
  const [loading, setLoading] = React.useState<boolean>(!initialCandidates && Boolean(incidentId));

  React.useEffect(() => {
    if (initialCandidates && initialCandidates.length > 0) {
      setCandidates(initialCandidates);
      return;
    }

    if (incidentId) {
      setLoading(true);
      fetch(`http://localhost:8000/api/v1/memory/similar/${incidentId}`)
        .then(res => res.json())
        .then(data => {
          if (data && data.candidates) {
            setCandidates(data.candidates);
          }
        })
        .catch(err => console.error("Failed to load similar memory:", err))
        .finally(() => setLoading(false));
    }
  }, [initialCandidates, incidentId]);

  if (loading) {
    return (
      <div className="p-8 text-center glass-panel rounded-xl border border-gray-800 text-gray-400 text-xs font-mono">
        Querying CockroachDB Unified Vector + Relational Store...
      </div>
    );
  }

  if (!candidates || candidates.length === 0) {
    return (
      <div className="p-8 text-center glass-panel rounded-xl border border-gray-800 text-gray-400 text-sm">
        No similar historical incidents found in CockroachDB institutional memory store.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="p-4 bg-purple-950/20 border border-purple-800/40 rounded-xl text-xs text-purple-300 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Brain className="w-4 h-4 text-purple-400" />
          <span>
            <strong>HYBRID HISTORICAL RETRIEVAL ENGINE:</strong> Querying CockroachDB SQL structured signals + 1536-dim vector distance.
          </span>
        </div>
        <span className="font-mono text-purple-300 font-bold">Candidates: {candidates.length}</span>
      </div>

      <div className="space-y-4">
        {candidates.map((cand) => {
          const simPct = Math.round(cand.hybrid_score * 100);
          const isSuccess = cand.outcome_score > 0.5;

          return (
            <div
              key={cand.incident_id}
              className="p-5 glass-panel rounded-2xl border border-gray-800 hover:border-purple-500/40 transition space-y-4 bg-gray-900/60"
            >
              {/* Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-purple-500/20 text-purple-300 border border-purple-500/40">
                    Rank #{cand.rank}
                  </span>
                  <h4 className="text-base font-bold text-gray-100">{cand.title}</h4>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono font-bold text-cyan-400 bg-cyan-950/60 border border-cyan-800/60 px-3 py-1 rounded-full">
                    {simPct}% Similarity
                  </span>
                </div>
              </div>

              {/* Explainable Matched Fields Checklist */}
              <div className="p-3 bg-gray-950/80 rounded-xl border border-gray-800 space-y-2">
                <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block">
                  Why Matched (Explainable Signal Breakdown)
                </span>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                  {Object.entries(cand.matched_fields).map(([field, isMatch]) => (
                    <div key={field} className="flex items-center space-x-1.5 font-mono">
                      {isMatch ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      ) : (
                        <XCircle className="w-3.5 h-3.5 text-gray-600 shrink-0" />
                      )}
                      <span className={isMatch ? "text-emerald-300 font-semibold" : "text-gray-500"}>
                        {isMatch ? `same ${field}` : `different ${field}`}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Infrastructure Version Info */}
              <div className="flex items-center space-x-4 text-xs font-mono text-gray-400 bg-gray-900 p-2.5 rounded-lg border border-gray-800">
                <div className="flex items-center space-x-1.5">
                  <Database className="w-3.5 h-3.5 text-cyan-400" />
                  <span>DB: {cand.infrastructure_snapshot_summary.db_version}</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <Server className="w-3.5 h-3.5 text-purple-400" />
                  <span>Service: {cand.infrastructure_snapshot_summary.service_version}</span>
                </div>
              </div>

              {/* Action History (Failed & Successful Attempts) */}
              <div className="space-y-2">
                <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block">
                  Historical Action Attempts & Outcome
                </span>

                {cand.failed_actions.length > 0 && (
                  <div className="space-y-1.5">
                    <span className="text-[11px] text-rose-400 font-mono font-semibold">Previous Failed Attempts (Preserved):</span>
                    {cand.failed_actions.map((act, idx) => (
                      <div key={idx} className="p-2.5 bg-rose-950/20 border border-rose-900/40 rounded-lg text-xs font-mono flex items-start justify-between">
                        <div>
                          <span className="text-rose-400 font-bold">FAILED: {act.command}</span>
                          <span className="text-gray-400 ml-2">({act.reason})</span>
                          {act.error_message && (
                            <p className="text-[11px] text-rose-300 mt-1">{act.error_message}</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {cand.successful_actions.length > 0 && (
                  <div className="space-y-1.5">
                    <span className="text-[11px] text-emerald-400 font-mono font-semibold">Successful Remediation Attempt:</span>
                    {cand.successful_actions.map((act, idx) => (
                      <div key={idx} className="p-2.5 bg-emerald-950/20 border border-emerald-800/40 rounded-lg text-xs font-mono flex items-center justify-between">
                        <div>
                          <span className="text-emerald-400 font-bold">SUCCESS: {act.command}</span>
                          <span className="text-gray-300 ml-2">({act.reason})</span>
                        </div>
                        <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
