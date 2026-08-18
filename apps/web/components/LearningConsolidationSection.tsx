'use client';

import React, { useState } from 'react';
import {
  triggerPostRemediationLearning,
  approveCandidate,
  rejectCandidate,
  LearningSummaryResponse,
} from '@/lib/api';

interface LearningConsolidationSectionProps {
  incidentId?: string;
}

export default function LearningConsolidationSection({ incidentId = 'inc-sample-01' }: LearningConsolidationSectionProps) {
  const [loading, setLoading] = useState(false);
  const [learningData, setLearningData] = useState<LearningSummaryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const handleRunLearning = async () => {
    setLoading(true);
    setError(null);
    setActionSuccess(null);
    try {
      const res = await triggerPostRemediationLearning(incidentId);
      setLearningData(res);
      setActionSuccess('Post-remediation outcome analysis, lesson extraction, and memory consolidation completed!');
    } catch (err: any) {
      setError(err.message || 'Post-remediation learning failed. Ensure an execution outcome exists.');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (candidateId: string) => {
    setLoading(true);
    setError(null);
    try {
      await approveCandidate(candidateId);
      setActionSuccess(`Candidate '${candidateId}' approved and consolidated into active institutional memory.`);
      // Refresh learning summary
      const res = await triggerPostRemediationLearning(incidentId);
      setLearningData(res);
    } catch (err: any) {
      setError(err.message || 'Approval failed');
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async (candidateId: string) => {
    setLoading(true);
    setError(null);
    try {
      await rejectCandidate(candidateId, 'Rejected during operator review.');
      setActionSuccess(`Candidate '${candidateId}' rejected.`);
      const res = await triggerPostRemediationLearning(incidentId);
      setLearningData(res);
    } catch (err: any) {
      setError(err.message || 'Rejection failed');
    } finally {
      setLoading(false);
    }
  };

  const getOutcomeBadgeClass = (classification?: string) => {
    switch (classification) {
      case 'COMPLETED_AND_RECOVERED':
      case 'ROLLED_BACK_AND_RECOVERED':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
      case 'COMPLETED_BUT_INCIDENT_PERSISTS':
      case 'ROLLED_BACK_BUT_INCIDENT_PERSISTS':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
      case 'ROLLBACK_FAILED':
      case 'EXECUTION_FAILED':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/30';
      default:
        return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30';
    }
  };

  const getActionBadgeClass = (action?: string) => {
    switch (action) {
      case 'CREATED':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
      case 'REINFORCED':
        return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30';
      case 'SUPERSEDED':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/30';
      case 'FLAGGED_FOR_REVIEW':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
      case 'REJECTED':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/30';
      default:
        return 'bg-slate-500/20 text-slate-300 border-slate-500/30';
    }
  };

  return (
    <div className="space-y-6 pt-4 border-t border-slate-800">
      {/* Top Header & Trigger Action */}
      <div className="flex items-center justify-between p-4 bg-slate-900/60 rounded-xl border border-slate-800">
        <div>
          <h4 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-400 animate-pulse"></span>
            Stage 7 Post-Remediation Learning & Institutional Memory Consolidation Engine
          </h4>
          <p className="text-xs text-slate-400">
            Evidence-backed lesson extraction, first-class negative knowledge, non-destructive supersession, bounded confidence & feedback loops
          </p>
        </div>
        <button
          onClick={handleRunLearning}
          disabled={loading}
          className="px-5 py-2 bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-400 hover:to-indigo-500 disabled:opacity-50 text-white font-semibold text-xs rounded-lg shadow-lg shadow-purple-500/20 transition-all flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
              Consolidating Memory...
            </>
          ) : (
            <>🧠 Consolidate Operational Memory</>
          )}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs font-mono">
          ⚠️ {error}
        </div>
      )}

      {actionSuccess && (
        <div className="p-4 bg-purple-500/10 border border-purple-500/30 rounded-xl text-purple-300 text-xs font-mono">
          ✓ {actionSuccess}
        </div>
      )}

      {learningData && (
        <div className="space-y-6">
          {/* Outcome & Effectiveness Score Banner */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs font-mono">
            <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
              <div className="text-slate-500 uppercase text-[10px]">Outcome Classification</div>
              <div className={`mt-1 inline-block px-2.5 py-1 rounded font-bold border uppercase ${getOutcomeBadgeClass(learningData.outcome.outcome_classification)}`}>
                {learningData.outcome.outcome_classification}
              </div>
            </div>
            <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
              <div className="text-slate-500 uppercase text-[10px]">Effectiveness Score</div>
              <div className="text-xl font-bold text-emerald-400 mt-1">
                {(learningData.outcome.effectiveness_score * 100).toFixed(1)}%
              </div>
            </div>
            <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
              <div className="text-slate-500 uppercase text-[10px]">Rollback Status</div>
              <div className="text-slate-200 mt-1 font-bold">
                {learningData.outcome.rollback_performed ? (learningData.outcome.rollback_successful ? '✓ ROLLBACK SUCCEEDED' : '✗ ROLLBACK FAILED') : 'NONE REQUIRED'}
              </div>
            </div>
            <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
              <div className="text-slate-500 uppercase text-[10px]">Recovery Metrics</div>
              <div className="text-slate-300 mt-1 font-bold">
                {learningData.outcome.incident_recovery_status} ({learningData.outcome.duration_seconds.toFixed(0)}s)
              </div>
            </div>
          </div>

          {/* Extracted Operational Lessons */}
          <div className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4">
            <h5 className="text-xs font-mono font-semibold text-purple-400 uppercase tracking-wider">
              📘 Extracted Operational Lessons (Positive & Negative Knowledge)
            </h5>
            <div className="space-y-4">
              {learningData.lessons?.map((lesn, idx) => (
                <div
                  key={idx}
                  className={`p-4 bg-slate-950/60 border rounded-lg space-y-3 font-mono text-xs ${
                    lesn.lesson_type === 'NEGATIVE_KNOWLEDGE' ? 'border-amber-500/40' : 'border-emerald-500/40'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${
                        lesn.lesson_type === 'NEGATIVE_KNOWLEDGE' ? 'bg-amber-500/20 text-amber-300 border-amber-500/30' : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                      }`}>
                        {lesn.lesson_type}
                      </span>
                      <span className="font-bold text-slate-100">{lesn.title}</span>
                    </div>
                    <span className="text-slate-400 text-[10px]">Confidence: {(lesn.confidence * 100).toFixed(0)}%</span>
                  </div>

                  <p className="text-slate-300 text-[11px]">{lesn.statement}</p>
                  <p className="text-slate-400 text-[10px]">Observed Effect: {lesn.observed_effect}</p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[10px] text-slate-400">
                    <div>
                      <span className="text-slate-500 uppercase block mb-1">Applicability Conditions</span>
                      <div className="flex flex-wrap gap-1">
                        {lesn.applicability_conditions?.map((c, i) => (
                          <span key={i} className="bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded border border-slate-700">{c}</span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <span className="text-slate-500 uppercase block mb-1">Evidence Lineage</span>
                      <div className="flex flex-wrap gap-1">
                        {lesn.supporting_evidence?.map((e, i) => (
                          <span key={i} className="bg-slate-800 text-purple-300 px-1.5 py-0.5 rounded border border-slate-700">{e}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Memory Candidates & Review Queue */}
          <div className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4">
            <h5 className="text-xs font-mono font-semibold text-cyan-400 uppercase tracking-wider">
              🧪 Memory Candidates & Quality Scoring
            </h5>
            <div className="space-y-3 font-mono text-xs">
              {learningData.candidates?.map((cand, idx) => (
                <div key={idx} className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-200 font-bold">{cand.candidate_text}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${getActionBadgeClass(cand.status)}`}>
                      {cand.status}
                    </span>
                  </div>

                  <div className="flex items-center gap-4 text-[10px] text-slate-400">
                    <span>Quality Score: <strong className="text-emerald-400">{(cand.quality_score * 100).toFixed(0)}%</strong></span>
                    <span>Novelty: <strong>{(cand.novelty_score * 100).toFixed(0)}%</strong></span>
                    <span>Contradiction: <strong>{(cand.contradiction_score * 100).toFixed(0)}%</strong></span>
                  </div>

                  {cand.review_required && cand.status === 'FLAGGED_FOR_REVIEW' && (
                    <div className="flex items-center gap-3 pt-2">
                      <button
                        onClick={() => handleApprove(cand.candidate_id)}
                        disabled={loading}
                        className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-semibold rounded"
                      >
                        ✓ Approve Candidate
                      </button>
                      <button
                        onClick={() => handleReject(cand.candidate_id)}
                        disabled={loading}
                        className="px-3 py-1 bg-rose-600/80 hover:bg-rose-600 text-white text-[11px] font-semibold rounded"
                      >
                        ✗ Reject Candidate
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Consolidation Decisions & Supersession Provenance */}
          <div className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-3">
            <h5 className="text-xs font-mono font-semibold text-purple-300 uppercase tracking-wider">
              📜 Consolidation Decisions & Supersession Provenance Trace
            </h5>
            <div className="space-y-2 font-mono text-[11px]">
              {learningData.consolidations?.map((cons, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-slate-950/60 border border-slate-800 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-0.5 rounded uppercase font-bold border ${getActionBadgeClass(cons.action)}`}>
                      {cons.action}
                    </span>
                    <span className="text-slate-300">{cons.reason}</span>
                  </div>
                  <div className="text-slate-500 text-[10px] flex items-center gap-2">
                    <span>Target Memory: <code className="text-cyan-400">{cons.target_memory_id || 'N/A'}</code></span>
                    <span>Confidence: {cons.confidence_before.toFixed(2)} → {cons.confidence_after.toFixed(2)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
