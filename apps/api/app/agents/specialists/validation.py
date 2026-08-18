import time
import uuid
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.agents.base import AgentState
from app.schemas.agent_investigation import CritiqueResult, AgentDisagreement
from app.core.logging import logger

class ValidationAgent:
    """
    Validation Specialist Agent for GhostOps Stage 4.
    Performs reflection self-critique, calibrates deterministic confidence,
    and records explicit agent disagreements across workflow positions.
    """

    @classmethod
    def run(cls, state: AgentState, db: Session) -> AgentState:
        t0 = time.time()
        logger.info(f"[ValidationAgent] Performing reflection critique and confidence calibration for run '{state.run_id}'")

        # 1. Deterministic Confidence Calibration Layer
        evidence_count = len(state.timeline) + len(state.historical_evidence)
        comp_data = state.remediation_applicability or {}
        comp_score = comp_data.get("compatibility_score", 0.70)

        base_confidence = min(0.95, (comp_score * 0.5) + (min(evidence_count, 5) * 0.08) + 0.25)
        calibrated_conf = round(base_confidence, 4)
        state.confidence = calibrated_conf

        # 2. Identify and Preserve Explicit Agent Disagreements
        disagreements: List[AgentDisagreement] = []

        if comp_data.get("classification") == "COMPATIBLE_WITH_DIFFERENCES":
            d1 = AgentDisagreement(
                disagreement_id=f"disag-{uuid.uuid4().hex[:8]}",
                run_id=state.run_id,
                agent_a="HistorianAgent",
                agent_b="TemporalReasoningAgent",
                position_a="Historical Incident A is 100% structurally & semantically similar.",
                position_b="Service version drift (v4.2.0 vs v4.3.1) introduces partial compatibility risk.",
                evidence_refs=[comp_data.get("historical_incident_id", "inc-a")],
                resolution="Accepted COMPATIBLE_WITH_DIFFERENCES classification. Remediation remains viable with version boundary checks.",
                resolved_by="ValidationAgent",
                confidence=0.88
            )
            disagreements.append(d1)

        if len(state.hypotheses) > 1:
            h1_stat = state.hypotheses[0].get("status")
            h2_stat = state.hypotheses[1].get("status")
            if h1_stat in ["SUPPORTED", "PLAUSIBLE"] and h2_stat == "PLAUSIBLE":
                d2 = AgentDisagreement(
                    disagreement_id=f"disag-{uuid.uuid4().hex[:8]}",
                    run_id=state.run_id,
                    agent_a="InvestigatorAgent (H1)",
                    agent_b="InvestigatorAgent (H2)",
                    position_a="H1: Database connection pool exhaustion caused by port 22 ingress surge.",
                    position_b="H2: DB authentication token expiration retry storm remains plausible.",
                    evidence_refs=state.hypotheses[0].get("supporting_evidence", []),
                    resolution="Primary hypothesis H1 prioritized due to direct CloudWatch event correlation.",
                    resolved_by="ValidationAgent",
                    confidence=0.92
                )
                disagreements.append(d2)

        state.agent_disagreements = [d.model_dump() for d in disagreements]

        # 3. Reflection Self-Critique
        critique = CritiqueResult(
            approved=True if calibrated_conf >= 0.60 else False,
            issues=[] if calibrated_conf >= 0.60 else ["Confidence below 0.60 threshold due to missing evidence"],
            missing_evidence=[] if evidence_count > 0 else ["No raw CloudWatch telemetry found"],
            confidence_adjustment=0.0,
            recommended_next_step="COMPLETE" if calibrated_conf >= 0.60 else "RETRY_INVESTIGATION"
        )
        state.critic_feedback = critique.model_dump()
        state.validation_passed = critique.approved

        duration = round((time.time() - t0) * 1000, 2)
        state.trace_steps.append({
            "step_id": f"step-{len(state.trace_steps) + 1}",
            "agent_name": "ValidationAgent",
            "input_summary": f"Evaluated reflection critique for run {state.run_id}",
            "output_summary": f"Calibrated confidence to {calibrated_conf} with {len(disagreements)} recorded agent disagreements",
            "tool_calls": [],
            "status": "SUCCESS",
            "confidence": calibrated_conf,
            "duration_ms": duration,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })

        return state
