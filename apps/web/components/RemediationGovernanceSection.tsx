'use client';

import React, { useState } from 'react';
import {
  generateRemediationPlan,
  validatePlanSafety,
  approveRemediationPlan,
  rejectRemediationPlan,
  RemediationPlanResponse,
} from '@/lib/api';
import SagaExecutionSection from './SagaExecutionSection';
import LearningConsolidationSection from './LearningConsolidationSection';
import GhostReplaySection from './GhostReplaySection';
import ProductionDashboardSection from './ProductionDashboardSection';

interface RemediationGovernanceSectionProps {
  incidentId: string;
}

export default function RemediationGovernanceSection({ incidentId }: RemediationGovernanceSectionProps) {
  const [loading, setLoading] = useState(false);
  const [planData, setPlanData] = useState<RemediationPlanResponse | null>(null);
  const [confirmationInput, setConfirmationInput] = useState('');
  const [rejectReasonInput, setRejectReasonInput] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const handleGeneratePlan = async () => {
    setLoading(true);
    setError(null);
    setActionSuccess(null);
    try {
      const res = await generateRemediationPlan(incidentId);
      setPlanData(res);
      setConfirmationInput('');
    } catch (err: any) {
      setError(err.message || 'Failed to generate remediation plan proposal');
    } finally {
      setLoading(false);
    }
  };

  const handleApprovePlan = async () => {
    if (!planData) return;
    setLoading(true);
    setError(null);
    setActionSuccess(null);
    try {
      const res = await approveRemediationPlan(planData.plan_id, {
        approved_by: 'DevOpsLead',
        confirmation_text: confirmationInput || undefined,
      });
      setPlanData(res);
      setActionSuccess('Plan successfully approved and advanced to READY_FOR_EXECUTION!');
    } catch (err: any) {
      setError(err.message || 'Approval failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRejectPlan = async () => {
    if (!planData || !rejectReasonInput) return;
    setLoading(true);
    setError(null);
    setActionSuccess(null);
    try {
      const res = await rejectRemediationPlan(planData.plan_id, {
        rejected_by: 'DevOpsLead',
        rejection_reason: rejectReasonInput,
      });
      setPlanData(res);
      setShowRejectModal(false);
      setActionSuccess('Plan successfully rejected and logged to audit trail.');
    } catch (err: any) {
      setError(err.message || 'Rejection failed');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadgeClass = (status?: string) => {
    switch (status) {
      case 'READY_FOR_EXECUTION':
      case 'APPROVED':
      case 'COMPLETED':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
      case 'PENDING_APPROVAL':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
      case 'REJECTED':
      case 'EXPIRED':
      case 'FAILED':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/30';
      default:
        return 'bg-slate-500/20 text-slate-300 border-slate-500/30';
    }
  };

  const getRiskBadgeClass = (riskLevel?: string) => {
    switch (riskLevel) {
      case 'HIGH_RISK':
      case 'CRITICAL':
        return 'bg-rose-500/20 text-rose-400 border-rose-500/40';
      case 'MEDIUM_RISK':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
      default:
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
    }
  };

  return (
    <div className="space-y-6">
      {/* Stage 10 System Overview & Production Dashboard */}
      <ProductionDashboardSection />

      {/* Top Header */}
      <div className="flex items-center justify-between p-4 bg-slate-900/60 rounded-xl border border-slate-800">
        <div>
          <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
            Stage 5-10 Governed Planning, Execution, Learning, Replay & Production Engine
          </h3>
          <p className="text-sm text-slate-400">
            Safety validation, blast radius, saga execution, post-remediation learning & production hardening
          </p>
        </div>
        <button
          onClick={handleGeneratePlan}
          disabled={loading}
          className="px-5 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 disabled:opacity-50 text-white font-medium rounded-lg shadow-lg shadow-emerald-500/20 transition-all flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
              Generating Governed Plan...
            </>
          ) : (
            <>🛡️ Generate Remediation Plan</>
          )}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-sm font-mono">
          ⚠️ {error}
        </div>
      )}

      {actionSuccess && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-300 text-sm font-mono">
          ✓ {actionSuccess}
        </div>
      )}

      {planData && (
        <div className="space-y-6">
          {/* Status & Risk Banner */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
              <div className="text-xs font-mono text-slate-400 uppercase">Plan Status</div>
              <div className={`mt-1 inline-block px-2.5 py-1 rounded text-xs font-bold border uppercase ${getStatusBadgeClass(planData.status)}`}>
                {planData.status}
              </div>
            </div>
            <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
              <div className="text-xs font-mono text-slate-400 uppercase">Risk Assessment</div>
              <div className={`mt-1 inline-block px-2.5 py-1 rounded text-xs font-bold border uppercase ${getRiskBadgeClass(planData.risk?.risk_level)}`}>
                {planData.risk?.risk_level} ({(planData.risk?.risk_score * 100).toFixed(0)}%)
              </div>
            </div>
            <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
              <div className="text-xs font-mono text-slate-400 uppercase">Blast Radius</div>
              <div className="text-lg font-bold text-amber-400 mt-1 uppercase font-mono">
                {planData.risk?.blast_radius}
              </div>
            </div>
            <div className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl">
              <div className="text-xs font-mono text-slate-400 uppercase">Expiration Time</div>
              <div className="text-xs font-mono text-slate-300 mt-2">
                {new Date(planData.expires_at).toUTCString()}
              </div>
            </div>
          </div>

          {/* Root Cause & Investigation Context */}
          <div className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-mono font-semibold text-cyan-400 uppercase tracking-wider">
                🔍 Investigation Evidence & Precedent Grounding
              </h4>
              <span className="text-xs bg-slate-800 text-slate-300 font-mono px-2.5 py-1 rounded border border-slate-700">
                Confidence: {(planData.confidence * 100).toFixed(0)}%
              </span>
            </div>
            <p className="text-sm text-slate-300">{planData.summary}</p>
            <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
              <span>Root Cause: <strong className="text-cyan-300">{planData.root_cause_hypothesis_id}</strong></span>
              <span>Temporal Compatibility: <strong className="text-emerald-400">{(planData.compatibility_score * 100).toFixed(0)}% ({planData.compatibility_classification})</strong></span>
            </div>
          </div>

          {/* Proposed Actions List */}
          <div className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4">
            <h4 className="text-sm font-mono font-semibold text-emerald-400 uppercase tracking-wider">
              📋 Proposed Action Sequence (Governed Catalog)
            </h4>
            <div className="space-y-4">
              {planData.steps?.map((step, idx) => (
                <div key={idx} className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center text-xs font-mono font-bold">
                        {step.step_order}
                      </span>
                      <span className="text-xs font-mono font-bold text-slate-200 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                        {step.action_type}
                      </span>
                    </div>
                    <span className={`text-[10px] px-2 py-0.5 rounded uppercase font-bold border ${getRiskBadgeClass(step.risk_level)}`}>
                      {step.risk_level}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 font-mono">Target: {step.target_resource_arn}</p>
                  <p className="text-xs text-slate-400">{step.reason}</p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <div className="p-3 bg-slate-900/60 rounded border border-slate-800 font-mono">
                      <div className="text-[10px] text-slate-500 uppercase">Parameters</div>
                      <pre className="text-slate-300 text-[11px] mt-1 overflow-x-auto">
                        {JSON.stringify(step.parameters, null, 2)}
                      </pre>
                    </div>
                    {step.rollback_action && (
                      <div className="p-3 bg-slate-900/60 rounded border border-slate-800 font-mono">
                        <div className="text-[10px] text-amber-400 uppercase">Rollback Action</div>
                        <div className="text-slate-300 text-[11px] mt-1">
                          {step.rollback_action.action_type}: {step.rollback_action.reason}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Safety Engine Checks */}
          <div className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-3">
            <h4 className="text-sm font-mono font-semibold text-cyan-400 uppercase tracking-wider">
              🛡️ Safety Engine Check Results
            </h4>
            <div className="space-y-2">
              {planData.safety_checks?.map((chk, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-slate-950/60 border border-slate-800 rounded-lg text-xs">
                  <div className="flex items-center gap-3">
                    <span className={chk.passed ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
                      {chk.passed ? "✓ PASS" : "✗ BLOCK"}
                    </span>
                    <span className="font-mono text-slate-300 capitalize">{chk.check_name.replace(/_/g, ' ')}</span>
                  </div>
                  <span className="text-slate-400">{chk.message}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Approval Gate & Governance Controls */}
          <div className="p-5 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-mono font-semibold text-amber-400 uppercase tracking-wider">
                ⚖️ Human Approval Gate Governance
              </h4>
              <span className={`px-2.5 py-1 rounded text-xs font-bold border uppercase ${getStatusBadgeClass(planData.approval_gate?.status)}`}>
                {planData.approval_gate?.status}
              </span>
            </div>

            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                <span>Required Role: <strong className="text-slate-200">{planData.approval_gate?.required_approver_role}</strong></span>
                <span>Requested At: {new Date(planData.approval_gate?.requested_at).toUTCString()}</span>
              </div>

              {/* High-Risk Confirmation Input */}
              {planData.risk?.risk_level === 'HIGH_RISK' && planData.status === 'PENDING_APPROVAL' && (
                <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg space-y-2">
                  <div className="text-xs text-amber-300 font-semibold font-mono">
                    ⚠️ HIGH-RISK PLAN CONFIRMATION REQUIRED
                  </div>
                  <p className="text-xs text-slate-300">
                    Type exact confirmation phrase to enable approval: <code className="text-cyan-300 font-bold">{planData.approval_gate?.confirmation_text}</code>
                  </p>
                  <input
                    type="text"
                    value={confirmationInput}
                    onChange={(e) => setConfirmationInput(e.target.value)}
                    placeholder={planData.approval_gate?.confirmation_text}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded text-xs text-slate-100 font-mono focus:border-cyan-500 focus:outline-none"
                  />
                </div>
              )}

              {/* Action Buttons */}
              {planData.status === 'PENDING_APPROVAL' && (
                <div className="flex items-center gap-4 pt-2">
                  <button
                    onClick={handleApprovePlan}
                    disabled={loading || (planData.risk?.risk_level === 'HIGH_RISK' && confirmationInput !== planData.approval_gate?.confirmation_text)}
                    className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-lg shadow-emerald-600/20 transition-all"
                  >
                    ✓ Approve Plan (Advance to READY_FOR_EXECUTION)
                  </button>
                  <button
                    onClick={() => setShowRejectModal(true)}
                    disabled={loading}
                    className="px-6 py-2.5 bg-rose-600/80 hover:bg-rose-600 disabled:opacity-50 text-white text-xs font-semibold rounded-lg transition-all"
                  >
                    ✗ Reject Plan
                  </button>
                </div>
              )}

              {planData.status === 'READY_FOR_EXECUTION' && (
                <div className="p-3 bg-emerald-500/20 border border-emerald-500/40 rounded-lg text-emerald-300 text-xs font-mono font-semibold">
                  ✓ Plan approved by {planData.approval_gate?.approved_by} at {new Date(planData.approval_gate?.approved_at || '').toUTCString()}. Status: READY_FOR_EXECUTION.
                </div>
              )}
            </div>
          </div>

          {/* Embedded Stage 6 Saga Execution Section */}
          <SagaExecutionSection planId={planData.plan_id} planStatus={planData.status} />

          {/* Embedded Stage 7 Post-Remediation Learning Section */}
          <LearningConsolidationSection incidentId={incidentId} />

          {/* Embedded Stage 8 Ghost Replay & Simulation Engine Section */}
          <GhostReplaySection incidentId={incidentId} />
        </div>
      )}

      {/* Rejection Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="p-6 bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full space-y-4">
            <h4 className="text-base font-bold text-slate-100">Reject Remediation Plan</h4>
            <p className="text-xs text-slate-400">Provide an auditable rejection reason for log persistence:</p>
            <textarea
              value={rejectReasonInput}
              onChange={(e) => setRejectReasonInput(e.target.value)}
              rows={3}
              placeholder="e.g. Rejecting due to ongoing database maintenance window."
              className="w-full p-3 bg-slate-950 border border-slate-800 rounded text-xs text-slate-100 focus:outline-none"
            />
            <div className="flex items-center justify-end gap-3">
              <button
                onClick={() => setShowRejectModal(false)}
                className="px-4 py-2 bg-slate-800 text-slate-300 text-xs rounded hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={handleRejectPlan}
                disabled={!rejectReasonInput}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs rounded disabled:opacity-50 font-semibold"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
