export type IncidentSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type IncidentStatus = 'OPEN' | 'INVESTIGATING' | 'REMEDIATION_PROPOSED' | 'REMEDIATION_IN_PROGRESS' | 'VERIFYING' | 'RESOLVED' | 'CLOSED';
export type RemediationStatus = 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'EXECUTING' | 'EXECUTED' | 'VERIFIED_SUCCESS' | 'VERIFIED_FAILURE' | 'ROLLED_BACK';
export type AgentStepStatus = 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'SKIPPED';

export interface SystemHealth {
  status: string;
  environment: string;
  database_connected: boolean;
  aws_mock_mode: boolean;
  system_time: string;
  details: {
    project: string;
    bedrock_model: string;
    mock_cloudwatch_alarms_count: number;
  };
}

export interface Incident {
  id: string;
  title: string;
  description: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  service: string;
  region: string;
  start_time: string;
  end_time?: string;
  target_resource_id?: string;
  memory_status: string;
  created_at: string;
}

export interface IncidentEvidence {
  evidence_id: string;
  incident_id: string;
  source: string;
  source_event_id: string;
  captured_at: string;
  event_type: string;
  raw_payload: Record<string, any>;
  content_hash: string;
  trust_level: string;
}

export interface InfrastructureSnapshot {
  id: string;
  db_version: string;
  service_version: string;
  topology: Record<string, any>;
  configuration: Record<string, any>;
  dependencies: Record<string, any>;
  region: string;
  snapshot_timestamp: string;
}

export interface OperationalAction {
  id: string;
  actor: string;
  agent: string;
  command: string;
  tool: string;
  target: string;
  risk_level: string;
  reason: string;
  idempotency_key: string;
  result: 'SUCCESS' | 'FAILED';
  error_message?: string;
  timestamp: string;
}

export interface MemoryRecord {
  id: string;
  title: string;
  memory_type: string;
  content: string;
  trust_level: string;
  created_at: string;
}

export interface IncidentDetail extends Incident {
  environment_fingerprint: Record<string, any>;
  root_cause_summary?: string;
  snapshots: InfrastructureSnapshot[];
  actions: OperationalAction[];
  memories: MemoryRecord[];
}

export interface AgentTrace {
  id: string;
  incident_id?: string;
  graph_name: string;
  thread_id: string;
  status: AgentStepStatus;
  current_node: string;
  created_at: string;
}

export interface RemediationPlan {
  id: string;
  incident_id: string;
  title: string;
  explanation: string;
  status: RemediationStatus;
  idempotency_key: string;
  estimated_risk: string;
  requires_human_approval: boolean;
  created_at: string;
}
