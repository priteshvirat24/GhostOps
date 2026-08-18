from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class SentinelStatus(str):
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"

class SentinelMode(str):
    OBSERVE_ONLY = "OBSERVE_ONLY"
    DETECT_AND_INVESTIGATE = "DETECT_AND_INVESTIGATE"
    DETECT_INVESTIGATE_AND_PLAN = "DETECT_INVESTIGATE_AND_PLAN"

class SentinelEvent(BaseModel):
    event_id: str
    sentinel_id: str = "sentinel-primary"
    source: str
    event_type: str
    resource_id: str
    resource_type: str = "EC2"
    timestamp: str
    severity: str = "MEDIUM"
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    baseline_value: Optional[float] = None
    deviation: Optional[float] = None
    region: str = "us-east-1"
    fingerprint: str
    payload_hash: str
    correlation_key: str
    deduplication_key: str
    suppressed: bool = False
    suppression_reason: Optional[str] = None
    processed: bool = False
    incident_id: Optional[str] = None

class SentinelAlert(BaseModel):
    alert_id: str
    sentinel_id: str
    event_id: str
    fingerprint: str
    resource_id: str
    severity: str
    anomaly_score: float
    confidence: float
    status: str  # OPEN | CORRELATED | SUPPRESSED | RESOLVED | ESCALATED
    deduplication_key: str
    correlation_key: str
    first_seen_at: str
    last_seen_at: str
    occurrence_count: int = 1
    suppressed_count: int = 0
    incident_id: Optional[str] = None

class SentinelDecision(BaseModel):
    decision_id: str
    sentinel_id: str
    event_id: Optional[str] = None
    incident_id: Optional[str] = None
    decision_type: str  # IGNORE | SUPPRESS | CREATE_INCIDENT | CORRELATE | TRIGGER_INVESTIGATION | TRIGGER_REPLAY | CREATE_PLAN | ESCALATE | PAUSE_SENTINEL
    decision: str
    reason: str
    confidence: float
    evidence_refs: List[str] = Field(default_factory=list)
    policy_refs: List[str] = Field(default_factory=list)
    created_at: str

class SentinelRun(BaseModel):
    run_id: str
    sentinel_id: str
    started_at: str
    completed_at: Optional[str] = None
    events_seen: int = 0
    events_normalized: int = 0
    alerts_created: int = 0
    alerts_suppressed: int = 0
    incidents_created: int = 0
    investigations_triggered: int = 0
    replays_triggered: int = 0
    plans_created: int = 0
    errors: List[str] = Field(default_factory=list)
    termination_reason: str = "COMPLETED_CLEANLY"

class SentinelPolicy(BaseModel):
    policy_id: str = "pol-default"
    name: str = "Default Sentinel Policy"
    enabled: bool = True
    severity_threshold: str = "MEDIUM"
    anomaly_threshold: float = 0.65
    confidence_threshold: float = 0.70
    dedup_window_seconds: int = 300
    correlation_window_seconds: int = 600
    cooldown_seconds: int = 60
    max_incidents_per_window: int = 5
    max_investigations_per_window: int = 5
    max_replays_per_window: int = 5
    auto_plan_enabled: bool = True

class SentinelMetrics(BaseModel):
    events_processed: int
    alerts_created: int
    alerts_suppressed: int
    incidents_correlated: int
    investigations_triggered: int
    plans_created: int
    consecutive_errors: int
    uptime_seconds: float

class IncidentCorrelation(BaseModel):
    correlation_key: str
    incident_id: str
    alerts_count: int
    primary_alert_id: str
    relationship: str

class SentinelHealth(BaseModel):
    sentinel_id: str
    status: str
    mode: str
    enabled: bool
    last_heartbeat_at: str
    poll_interval_seconds: int
    metrics: SentinelMetrics
    active_policy: SentinelPolicy

class SentinelStartRequest(BaseModel):
    mode: str = SentinelMode.DETECT_INVESTIGATE_AND_PLAN
    poll_interval_seconds: int = 30

class SentinelStopRequest(BaseModel):
    reason: str = "User requested sentinel stop"

class SentinelPauseRequest(BaseModel):
    duration_seconds: int = 300
    reason: str = "User requested sentinel pause"

class SentinelResumeRequest(BaseModel):
    reason: str = "User requested sentinel resume"

class SentinelConfigurationRequest(BaseModel):
    mode: Optional[str] = None
    poll_interval_seconds: Optional[int] = None
    policy: Optional[SentinelPolicy] = None

class SentinelEventResponse(BaseModel):
    accepted: bool
    event_id: str
    fingerprint: str
    alert_created: bool
    incident_id: Optional[str] = None
    decision: str
