from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from enum import Enum

class SignalStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    BLOCKED = "BLOCKED"

class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"

class SignalVerificationResult(BaseModel):
    signal_name: str
    signal_type: str  # INFRASTRUCTURE_STATE | APPLICATION_TELEMETRY | RELIABILITY_OBSERVATION
    source: str       # e.g., EC2.DescribeSecurityGroups, CloudWatch.GetMetricData
    observed_value: Any
    expected_condition: str
    status: SignalStatus
    observation_window: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evidence_ref: Optional[str] = None
    error_message: Optional[str] = None
    verification_mode: str = "MOCK"

class VerificationReport(BaseModel):
    incident_id: str
    plan_id: str
    execution_id: str
    overall_status: VerificationStatus
    verification_mode: str  # AWS_REAL | MOCK
    signals: List[SignalVerificationResult] = Field(default_factory=list)
    infrastructure_verified: bool = False
    telemetry_verified: bool = False
    observation_window_complete: bool = False
    trust_delta: float = 0.0
    summary: str
    blocked_reason: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def signal_results(self) -> Dict[str, Dict[str, Any]]:
        res = {}
        for s in self.signals:
            res[s.signal_name] = {
                "signal": s.source,
                "status": s.status.value if hasattr(s.status, "value") else str(s.status),
                "value": s.observed_value,
                "threshold": s.expected_condition
            }
        if "cloudwatch_errorrate" in res:
            res["application_error_rate"] = res["cloudwatch_errorrate"]
        if "cloudwatch_targetresponsetime" in res:
            res["p99_latency_recovery"] = res["cloudwatch_targetresponsetime"]
        return res
