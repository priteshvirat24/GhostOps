'use client';

import React, { useState } from 'react';
import {
  executeRemediationPlan,
  cancelExecution,
  triggerManualRollback,
  ExecutionDetailResponse,
  DryRunResponse,
} from '@/lib/api';

interface SagaExecutionSectionProps {
  planId?: string;
  planStatus?: string;
  incidentId?: string;
}

export default function SagaExecutionSection({
  planId = 'plan-default-01',
  planStatus = 'APPROVED',
  incidentId = 'inc-sample-01'
}: SagaExecutionSectionProps) {
  const [loading, setLoading] = useState(false);
  const [executionData, setExecutionData] = useState<ExecutionDetailResponse | null>(null);
  const [dryRunData, setDryRunData] = useState<DryRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const handleDryRun = async () => {
    setLoading(true);
    setError(null);
    setActionSuccess(null);
    setDryRunData(null);
    try {
      const res = (await executeRemediationPlan(planId, { dry_run: true })) as DryRunResponse;
      setDryRunData(res);
      setActionSuccess('Dry-run simulation completed. Zero state mutations executed.');
    } catch (err: any) {
      setError(err.message || 'Dry run simulation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteSaga = async () => {
    setLoading(true);
    setError(null);
    setActionSuccess(null);
    setDryRunData(null);
    try {
      const res = (await executeRemediationPlan(planId, { dry_run: false })) as ExecutionDetailResponse;
      setExecutionData(res);
      setActionSuccess(`Saga execution started (Execution ID: ${res.execution_id}). Status: ${res.status}`);
    } catch (err: any) {
      setError(err.message || 'Saga execution failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!executionData) return;
    setLoading(true);
    setError(null);
    try {
      const res = await cancelExecution(executionData.execution_id);
      setExecutionData(res);
      setActionSuccess('Execution cancelled safely by user.');
    } catch (err: any) {
      setError(err.message || 'Cancellation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRollback = async () => {
    if (!executionData) return;
    setLoading(true);
    setError(null);
    try {
      const res = await triggerManualRollback(executionData.execution_id);
      setExecutionData(res);
      setActionSuccess('Manual rollback saga initiated and completed.');
    } catch (err: any) {
      setError(err.message || 'Rollback failed');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadgeClass = (status?: string) => {
    switch (status) {
      case 'COMPLETED':
      case 'SUCCEEDED':
      case 'VERIFIED':
      case 'RECOVERED':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
      case 'ROLLED_BACK':
      case 'COMPENSATED':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
      case 'FAILED':
      case 'ROLLBACK_FAILED':
      case 'BLOCKED':
      case 'CANCELLED':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/30';
      default:
        return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30';
    }
  };

  return (
    <div className="space-y-6 pt-4 border-t border-slate-800">
      {/* Top Header & Actions */}
      <div className="flex items-center justify-between p-4 bg-slate-900/60 rounded-xl border border-slate-800">
        <div>
          <h4 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse"></span>
            Stage 6 Governed Saga Execution & Rollback Engine
          </h4>
          <p className="text-xs text-slate-400">
            Idempotency, precheck validation, transactional locks, pre/post-state diffs, reverse compensation & audit events
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleDryRun}
            disabled={loading}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 font-medium text-xs rounded-lg border border-slate-700 transition"
          >
            🧪 Dry-Run Simulator
          </button>
          <button
            onClick={handleExecuteSaga}
            disabled={loading || planStatus !== 'READY_FOR_EXECUTION'}
            className="px-5 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 text-white font-semibold text-xs rounded-lg shadow-lg shadow-cyan-500/20 transition-all flex items-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                </svg>
                Executing Saga...
              </>
            ) : (
              <>🚀 Execute Governed Saga</>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs font-mono">
          ⚠️ {error}
        </div>
      )}

      {actionSuccess && (
        <div className="p-4 bg-cyan-500/10 border border-cyan-500/30 rounded-xl text-cyan-300 text-xs font-mono">
          ✓ {actionSuccess}
        </div>
      )}

      {/* Dry Run Simulation Output */}
      {dryRunData && (
        <div className="p-5 bg-slate-900/60 border border-cyan-500/30 rounded-xl space-y-4 font-mono text-xs">
          <div className="flex items-center justify-between">
            <span className="text-cyan-300 font-bold uppercase">🧪 Dry-Run Execution Simulation</span>
            <span className={dryRunData.would_execute ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
              {dryRunData.would_execute ? "✓ WOULD EXECUTE SAFELY" : "✗ BLOCKED BY PRECHECKS"}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-3 bg-slate-950 rounded border border-slate-800">
              <div className="text-[10px] text-slate-500 uppercase mb-1">Expected Pre-State Baseline</div>
              <pre className="text-slate-300 overflow-x-auto">{JSON.stringify(dryRunData.expected_pre_state, null, 2)}</pre>
            </div>
            <div className="p-3 bg-slate-950 rounded border border-slate-800">
              <div className="text-[10px] text-cyan-400 uppercase mb-1">Expected Post-State Result</div>
              <pre className="text-slate-300 overflow-x-auto">{JSON.stringify(dryRunData.expected_post_state, null, 2)}</pre>
            </div>
          </div>
        </div>
      )}

      {/* Execution Details & Step Trace */}
      {executionData && (
        <div className="space-y-6">
          {/* Execution Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs font-mono">
            <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
              <div className="text-slate-500 uppercase text-[10px]">Execution Status</div>
              <div className={`mt-1 inline-block px-2.5 py-1 rounded font-bold border uppercase ${getStatusBadgeClass(executionData.status)}`}>
                {executionData.status}
              </div>
            </div>
            <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
              <div className="text-slate-500 uppercase text-[10px]">Incident Recovery Status</div>
              <div className={`mt-1 inline-block px-2.5 py-1 rounded font-bold border uppercase ${getStatusBadgeClass(executionData.incident_recovery_status)}`}>
                {executionData.incident_recovery_status}
              </div>
            </div>
            <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
              <div className="text-slate-500 uppercase text-[10px]">Executed / Compensated</div>
              <div className="text-slate-200 mt-1 font-bold">
                Executed: {executionData.executed_steps} | Compensated: {executionData.compensated_steps}
              </div>
            </div>
            <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
              <div className="text-slate-500 uppercase text-[10px]">Execution Lock ID</div>
              <div className="text-cyan-400 mt-1 font-bold truncate">
                {executionData.lock_id || 'RELEASED'}
              </div>
            </div>
          </div>

          {/* Action Step Execution Progress */}
          <div className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4">
            <div className="flex items-center justify-between">
              <h5 className="text-xs font-mono font-semibold text-cyan-400 uppercase tracking-wider">
                ⚙️ Step Execution Timeline & State Diffs
              </h5>
              <div className="flex items-center gap-2">
                {executionData.status === 'EXECUTING' && (
                  <button onClick={handleCancel} disabled={loading} className="px-3 py-1 bg-rose-600/80 hover:bg-rose-600 text-white text-xs rounded">
                    Cancel Execution
                  </button>
                )}
                {(executionData.status === 'FAILED' || executionData.status === 'COMPLETED_WITH_WARNINGS') && (
                  <button onClick={handleRollback} disabled={loading} className="px-3 py-1 bg-amber-600/80 hover:bg-amber-600 text-white text-xs rounded">
                    ↺ Manual Rollback
                  </button>
                )}
              </div>
            </div>

            <div className="space-y-4">
              {executionData.steps_detail?.map((step, idx) => (
                <div key={idx} className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg space-y-3 font-mono text-xs">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 flex items-center justify-center text-[10px] font-bold">
                        {step.step_order}
                      </span>
                      <span className="font-bold text-slate-200 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                        {step.action_type}
                      </span>
                      <span className="text-slate-400 text-[11px]">{step.target_resource}</span>
                    </div>
                    <span className={`px-2 py-0.5 rounded uppercase font-bold border ${getStatusBadgeClass(step.status)}`}>
                      {step.status}
                    </span>
                  </div>

                  <p className="text-slate-300 text-[11px]">{step.result_summary}</p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px]">
                    <div className="p-3 bg-slate-900/60 rounded border border-slate-800">
                      <div className="text-[10px] text-slate-500 uppercase">Pre-Mutation State</div>
                      <pre className="text-slate-300 mt-1 overflow-x-auto">{JSON.stringify(step.pre_state, null, 2)}</pre>
                    </div>
                    <div className="p-3 bg-slate-900/60 rounded border border-slate-800">
                      <div className="text-[10px] text-emerald-400 uppercase">Post-Mutation State</div>
                      <pre className="text-slate-300 mt-1 overflow-x-auto">{JSON.stringify(step.post_state, null, 2)}</pre>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Audit Event Timeline */}
          <div className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-3">
            <h5 className="text-xs font-mono font-semibold text-slate-300 uppercase tracking-wider">
              📜 Audit Event Trace Log (Immutable)
            </h5>
            <div className="space-y-2 font-mono text-[11px]">
              {executionData.events?.map((evt, i) => (
                <div key={i} className="flex items-center justify-between p-2.5 bg-slate-950/60 border border-slate-800 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className="text-cyan-400 font-bold uppercase">{evt.event_type}</span>
                    <span className="text-slate-300">{evt.summary}</span>
                  </div>
                  <span className="text-slate-500 text-[10px]">{new Date(evt.timestamp).toUTCString()}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
