import { SystemHealth, Incident, IncidentDetail, IncidentEvidence, AgentTrace, RemediationPlan } from '../types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface InvestigationResponse {
  run_id: string;
  incident_id: string;
  status: string;
  selected_hypothesis?: {
    hypothesis_id: string;
    statement: string;
    supporting_evidence: string[];
    contradicting_evidence: string[];
    confidence: number;
    status: string;
  };
  confidence: number;
  historical_candidates: any[];
  temporal_comparisons: any[];
  remediation_applicability?: any;
  agent_disagreements: any[];
  termination_reason: string;
}

export interface TraceDetailResponse {
  run_id: string;
  incident_id: string;
  status: string;
  agent_steps: Array<{
    step_id: string;
    agent_name: string;
    input_summary: string;
    output_summary: string;
    tool_calls: any[];
    status: string;
    confidence: number;
    duration_ms: number;
    timestamp: string;
  }>;
  tool_calls: any[];
  confidence_progression: any[];
  disagreements: any[];
  termination_reason: string;
}

export interface RemediationPlanResponse {
  plan_id: string;
  incident_id: string;
  investigation_run_id: string;
  version: number;
  title: string;
  summary: string;
  status: string;
  root_cause_hypothesis_id: string;
  confidence: number;
  compatibility_score: number;
  compatibility_classification: string;
  risk: {
    risk_level: string;
    risk_score: number;
    blast_radius: string;
    factors: string[];
  };
  steps: Array<{
    step_order: number;
    action_type: string;
    target_resource_arn: string;
    parameters: any;
    reason: string;
    evidence_refs: string[];
    risk_level: string;
    requires_approval: boolean;
    idempotency_key: string;
    preconditions: string[];
    expected_effect: string;
    failure_conditions: string[];
    rollback_action?: any;
    verification_requirements: any[];
    status: string;
  }>;
  approval_gate: {
    approval_id: string;
    plan_id: string;
    required: boolean;
    required_approver_role: string;
    status: string;
    requested_at: string;
    approved_at?: string;
    approved_by?: string;
    rejection_reason?: string;
    confirmation_text?: string;
    expires_at: string;
  };
  safety_checks: Array<{
    passed: boolean;
    check_name: string;
    severity: string;
    message: string;
    blocking: boolean;
  }>;
  rollback_plan: any[];
  verification_plan: any[];
  evidence_refs: string[];
  historical_precedent_refs: string[];
  created_at: string;
  expires_at: string;
}

export interface DryRunResponse {
  dry_run: boolean;
  would_execute: boolean;
  plan_id: string;
  plan_version: number;
  steps: any[];
  expected_pre_state: any;
  expected_post_state: any;
  rollback_plan: any[];
  verification_plan: any[];
  risk: any;
  blocking_conditions: string[];
}

export interface ExecutionDetailResponse {
  execution_id: string;
  plan_id: string;
  plan_version: number;
  incident_id: string;
  status: string;
  started_at: string;
  completed_at?: string;
  failure_reason?: string;
  termination_reason: string;
  current_step: number;
  executed_steps: number;
  compensated_steps: number;
  verification_status: string;
  incident_recovery_status: string;
  lock_id?: string;
  executor: string;
  trace_id: string;
  steps_detail: Array<{
    execution_step_id: string;
    step_order: number;
    action_type: string;
    target_resource: string;
    status: string;
    idempotency_key: string;
    started_at?: string;
    completed_at?: string;
    attempt_count: number;
    request_id?: string;
    result_summary?: string;
    failure_reason?: string;
    pre_state: any;
    post_state: any;
    compensation_status: string;
    verification_status: string;
  }>;
  events: Array<{
    event_id: string;
    execution_id: string;
    step_id?: string;
    event_type: string;
    timestamp: string;
    actor: string;
    request_id?: string;
    summary: string;
    metadata: any;
    severity: string;
  }>;
  created_at: string;
  updated_at: string;
}

export interface LearningSummaryResponse {
  incident_id: string;
  outcome: {
    outcome_id: string;
    incident_id: string;
    plan_id: string;
    execution_id: string;
    execution_status: string;
    verification_status: string;
    incident_recovery_status: string;
    outcome_classification: string;
    effectiveness_score: number;
    duration_seconds: number;
    executed_steps_count: number;
    failed_steps_count: number;
    compensated_steps_count: number;
    rollback_performed: boolean;
    rollback_successful: boolean;
    recovery_metrics: any;
    evidence_refs: string[];
    confidence: number;
    created_at: string;
  };
  lessons: Array<{
    lesson_id: string;
    incident_id: string;
    execution_id?: string;
    lesson_type: string;
    title: string;
    statement: string;
    supporting_evidence: string[];
    contradicting_evidence: string[];
    applicability_conditions: string[];
    non_applicability_conditions: string[];
    observed_effect: string;
    confidence: number;
    temporal_scope: string;
    status: string;
  }>;
  candidates: Array<{
    candidate_id: string;
    lesson_id: string;
    candidate_text: string;
    normalized_fingerprint: string;
    source_incident_ids: string[];
    source_execution_ids: string[];
    evidence_refs: string[];
    confidence: number;
    novelty_score: number;
    contradiction_score: number;
    applicability_score: number;
    quality_score: number;
    review_required: boolean;
    rejection_reason?: string;
    status: string;
  }>;
  consolidations: Array<{
    consolidation_id: string;
    candidate_id: string;
    target_memory_id?: string;
    action: string;
    reason: string;
    previous_memory_ids: string[];
    evidence_refs: string[];
    confidence_before: number;
    confidence_after: number;
    actor: string;
    created_at: string;
  }>;
}

export interface ReplayResultResponse {
  replay_id: string;
  source_incident_id: string;
  mode: string;
  status: string;
  score: {
    overall_score: number;
    classification: string;
    diagnosis_accuracy: number;
    evidence_accuracy: number;
    remediation_accuracy: number;
    outcome_accuracy: number;
    temporal_compatibility: number;
    provenance_completeness: number;
  };
  predicted_outcome: string;
  actual_outcome: string;
  termination_reason: string;
  steps_count: number;
  differences_count: number;
  regressions_count: number;
  created_at: string;
}

export interface ReplayProvenanceResponse {
  replay_id: string;
  source_incident_id: string;
  source_execution_id?: string;
  source_snapshot_id?: string;
  memory_version: string;
  mode: string;
  deterministic_seed: number;
  started_at: string;
  completed_at?: string;
  steps: Array<{
    replay_step_id: string;
    replay_id: string;
    step_order: number;
    agent_name: string;
    action_type: string;
    target_resource: string;
    input_summary: string;
    output_summary: string;
    simulated_pre_state: any;
    simulated_post_state: any;
    evidence_refs: string[];
    confidence: number;
    status: string;
    duration_ms: number;
  }>;
  differences: Array<{
    difference_id: string;
    replay_id: string;
    category: string;
    historical_value: any;
    predicted_value: any;
    severity: string;
    explanation: string;
    evidence_refs: string[];
  }>;
  regressions: Array<{
    regression_id: string;
    replay_id: string;
    memory_id: string;
    regression_type: string;
    previous_confidence: number;
    observed_confidence: number;
    score_delta: number;
    explanation: string;
    severity: string;
    status: string;
  }>;
  mutations: Array<{
    mutation_id: string;
    replay_id: string;
    resource_id: string;
    action_type: string;
    pre_state: any;
    post_state: any;
    simulated_only: boolean;
    reversible: boolean;
    mutation_hash: string;
  }>;
}

export interface SentinelHealthResponse {
  sentinel_id: string;
  status: string;
  mode: string;
  enabled: boolean;
  last_heartbeat_at: string;
  poll_interval_seconds: number;
  metrics: {
    events_processed: number;
    alerts_created: number;
    alerts_suppressed: number;
    incidents_correlated: number;
    investigations_triggered: number;
    plans_created: number;
    consecutive_errors: number;
    uptime_seconds: number;
  };
  active_policy: any;
}

export async function fetchSystemHealth(): Promise<SystemHealth | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/health`, { cache: 'no-store' });
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error('Failed to fetch system health:', error);
    return null;
  }
}

export async function fetchIncidents(params?: { severity?: string; service?: string; region?: string; status?: string }): Promise<Incident[]> {
  try {
    const url = new URL(`${API_BASE_URL}/api/v1/incidents`);
    if (params?.severity) url.searchParams.append('severity', params.severity);
    if (params?.service) url.searchParams.append('service', params.service);
    if (params?.region) url.searchParams.append('region', params.region);
    if (params?.status) url.searchParams.append('status', params.status);

    const res = await fetch(url.toString(), { cache: 'no-store' });
    if (!res.ok) return [];
    return await res.json();
  } catch (error) {
    console.error('Failed to fetch incidents:', error);
    return [];
  }
}

export async function fetchIncidentDetail(incidentId: string): Promise<IncidentDetail | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/incidents/${incidentId}`, { cache: 'no-store' });
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error(`Failed to fetch incident detail for ${incidentId}:`, error);
    return null;
  }
}

export async function fetchIncidentEvidence(incidentId: string): Promise<IncidentEvidence[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/incidents/${incidentId}/evidence`, { cache: 'no-store' });
    if (!res.ok) return [];
    return await res.json();
  } catch (error) {
    console.error(`Failed to fetch evidence for ${incidentId}:`, error);
    return [];
  }
}

export async function fetchSimilarIncidents(incidentId: string, limit: number = 5): Promise<any> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/incidents/${incidentId}/similar?limit=${limit}`, { cache: 'no-store' });
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error(`Failed to fetch similar incidents for ${incidentId}:`, error);
    return null;
  }
}

export async function runAgentInvestigation(incidentId: string, payload: any = {}): Promise<InvestigationResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/incidents/${incidentId}/investigate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Agent investigation failed');
  }
  return await res.json();
}

export async function fetchTraceDetails(runId: string): Promise<TraceDetailResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/traces/${runId}`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Failed to fetch trace details for ${runId}`);
  }
  return await res.json();
}

export async function generateRemediationPlan(incidentId: string): Promise<RemediationPlanResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/incidents/${incidentId}/plans`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to generate remediation plan');
  }
  return await res.json();
}

export async function validatePlanSafety(planId: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/plans/${planId}/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Plan validation failed');
  }
  return await res.json();
}

export async function approveRemediationPlan(planId: string, payload: { approved_by?: string; confirmation_text?: string }): Promise<RemediationPlanResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/plans/${planId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Plan approval failed');
  }
  return await res.json();
}

export async function rejectRemediationPlan(planId: string, payload: { rejected_by: string; rejection_reason: string }): Promise<RemediationPlanResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/plans/${planId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Plan rejection failed');
  }
  return await res.json();
}

export async function executeRemediationPlan(planId: string, payload: { dry_run?: boolean; requested_by?: string } = {}): Promise<ExecutionDetailResponse | DryRunResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/plans/${planId}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Execution request failed');
  }
  return await res.json();
}

export async function fetchExecutionDetail(executionId: string): Promise<ExecutionDetailResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/executions/${executionId}`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Failed to fetch execution detail for ${executionId}`);
  }
  return await res.json();
}

export async function cancelExecution(executionId: string): Promise<ExecutionDetailResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/executions/${executionId}/cancel`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Execution cancellation failed');
  }
  return await res.json();
}

export async function triggerManualRollback(executionId: string): Promise<ExecutionDetailResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/executions/${executionId}/rollback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Manual rollback failed');
  }
  return await res.json();
}

export async function fetchPlanExecutions(planId: string): Promise<ExecutionDetailResponse[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/plans/${planId}/executions`, { cache: 'no-store' });
    if (!res.ok) return [];
    return await res.json();
  } catch (error) {
    console.error(`Failed to fetch executions for plan ${planId}:`, error);
    return [];
  }
}

export async function triggerPostRemediationLearning(incidentId: string): Promise<LearningSummaryResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/incidents/${incidentId}/learn`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Post-remediation learning failed');
  }
  return await res.json();
}

export async function fetchIncidentLearningSummary(incidentId: string): Promise<LearningSummaryResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/incidents/${incidentId}/learning`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Failed to fetch learning summary for incident ${incidentId}`);
  }
  return await res.json();
}

export async function fetchReviewQueue(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/learning/review-queue`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error('Failed to fetch review queue');
  }
  return await res.json();
}

export async function approveCandidate(candidateId: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/learning/candidates/${candidateId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Candidate approval failed');
  }
  return await res.json();
}

export async function rejectCandidate(candidateId: string, rejectionReason?: string): Promise<any> {
  const url = new URL(`${API_BASE_URL}/api/v1/learning/candidates/${candidateId}/reject`);
  if (rejectionReason) url.searchParams.append('rejection_reason', rejectionReason);

  const res = await fetch(url.toString(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Candidate rejection failed');
  }
  return await res.json();
}

export async function fetchMemoryProvenance(memoryId: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/memory/${memoryId}/provenance`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Failed to fetch memory provenance for ${memoryId}`);
  }
  return await res.json();
}

export async function fetchMemoryFeedback(memoryId: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/memory/${memoryId}/feedback`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Failed to fetch memory feedback for ${memoryId}`);
  }
  return await res.json();
}

export async function triggerIncidentReplay(incidentId: string, payload: any = {}): Promise<ReplayResultResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/replay/incidents/${incidentId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Incident replay failed');
  }
  return await res.json();
}

export async function triggerCounterfactualReplay(payload: any = {}): Promise<ReplayResultResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/replay/counterfactual`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Counterfactual simulation failed');
  }
  return await res.json();
}

export async function triggerDriftSimulation(payload: any = {}): Promise<ReplayResultResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/replay/drift-simulation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Drift simulation failed');
  }
  return await res.json();
}

export async function fetchReplayDetail(replayId: string): Promise<ReplayResultResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/replay/${replayId}`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Failed to fetch replay detail for ${replayId}`);
  }
  return await res.json();
}

export async function fetchReplayProvenance(replayId: string): Promise<ReplayProvenanceResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/replay/${replayId}/provenance`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Failed to fetch replay provenance for ${replayId}`);
  }
  return await res.json();
}

export async function fetchMemoryRegressions(): Promise<any[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/replay/regressions`, { cache: 'no-store' });
    if (!res.ok) return [];
    return await res.json();
  } catch (error) {
    console.error('Failed to fetch memory regressions:', error);
    return [];
  }
}

export async function fetchSentinelStatus(): Promise<SentinelHealthResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/sentinel/status`, { cache: 'no-store' });
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error('Failed to fetch sentinel status:', error);
    return null;
  }
}

export async function startSentinel(payload: any = {}): Promise<SentinelHealthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/sentinel/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to start sentinel');
  }
  return await res.json();
}

export async function stopSentinel(payload: any = {}): Promise<SentinelHealthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/sentinel/stop`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to stop sentinel');
  }
  return await res.json();
}

export async function pauseSentinel(payload: any = {}): Promise<SentinelHealthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/sentinel/pause`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to pause sentinel');
  }
  return await res.json();
}

export async function resumeSentinel(payload: any = {}): Promise<SentinelHealthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/sentinel/resume`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to resume sentinel');
  }
  return await res.json();
}

export async function updateSentinelPolicy(policy: any): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/sentinel/policy`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(policy),
    cache: 'no-store',
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to update sentinel policy');
  }
  return await res.json();
}

export async function ingestTelemetryEvent(rawPayload: any): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/sentinel/ingest-event`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(rawPayload),
    cache: 'no-store',
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to ingest telemetry event');
  }
  return await res.json();
}

export async function fetchSentinelDecisions(limit: number = 20): Promise<any[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/sentinel/decisions?limit=${limit}`, { cache: 'no-store' });
    if (!res.ok) return [];
    return await res.json();
  } catch (error) {
    console.error('Failed to fetch sentinel decisions:', error);
    return [];
  }
}

export async function fetchAgentTraces(): Promise<AgentTrace[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/traces`, { cache: 'no-store' });
    if (!res.ok) return [];
    return await res.json();
  } catch (error) {
    console.error('Failed to fetch agent traces:', error);
    return [];
  }
}

export async function fetchRemediationPlans(): Promise<RemediationPlan[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/plans`, { cache: 'no-store' });
    if (!res.ok) return [];
    return await res.json();
  } catch (error) {
    console.error('Failed to fetch remediation plans:', error);
    return [];
  }
}

export async function getHealth(): Promise<SystemHealth | null> {
  return await fetchSystemHealth();
}

export async function runEvaluation(split?: string): Promise<any> {
  try {
    const query = split ? `?split=${encodeURIComponent(split)}` : '';
    const res = await fetch(`${API_BASE_URL}/api/v1/evaluation/run${query}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      cache: 'no-store'
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (error) {
    console.error('Failed to run evaluation:', error);
    throw error;
  }
}

export async function runDemoReplay(): Promise<any> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/demo/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      cache: 'no-store'
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (error) {
    console.error('Failed to run demo replay:', error);
    throw error;
  }
}

export async function runDemoInvestigation(): Promise<any> {
  return await runDemoReplay();
}
