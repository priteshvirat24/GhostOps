from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import Incident, AgentTrace, AgentStepExecution
from app.agents.base import AgentState
from app.agents.graph import OrchestratorGraph
from app.schemas.agent_investigation import (
    InvestigationRequestPayload,
    InvestigationResponse,
    TraceDetailResponse,
    StepTraceItem,
    Hypothesis,
    TemporalComparisonDimension,
    RemediationApplicability,
    AgentDisagreement
)
from app.core.logging import logger

router = APIRouter()

@router.post("/incidents/{incident_id}/investigate", response_model=InvestigationResponse, status_code=status.HTTP_200_OK)
def investigate_incident(
    incident_id: str,
    payload: InvestigationRequestPayload = InvestigationRequestPayload(),
    db: Session = Depends(get_db)
):
    """
    Triggers evidence-backed multi-agent investigation run for target incident.
    Executes Supervisor, Historian, Investigator, Temporal Reasoning, and Validation agents.
    """
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID '{incident_id}' not found."
        )

    # Initialize AgentState with payload budget limits
    state = AgentState(
        incident_id=incident.id,
        severity=incident.severity,
        target_resource_id=incident.target_resource_id,
        max_steps=payload.max_steps,
        max_retrieval_rounds=payload.max_retrieval_rounds,
        max_reflection_rounds=payload.max_reflection_rounds
    )

    # Add raw incident info
    state.raw_events.append({
        "service": incident.service or "auth-service",
        "region": incident.region or "us-east-1",
        "title": incident.title
    })

    # Execute stateful investigation graph
    graph = OrchestratorGraph()
    final_state = graph.run_investigation_graph(state, db)

    # Parse output structures
    hypotheses_list = [Hypothesis(**h) for h in final_state.hypotheses]
    top_hypothesis = hypotheses_list[0] if hypotheses_list else None

    temp_dims = [TemporalComparisonDimension(**d) for d in final_state.temporal_comparisons]
    applicability = RemediationApplicability(**final_state.remediation_applicability) if final_state.remediation_applicability else None
    disagreements = [AgentDisagreement(**d) for d in final_state.agent_disagreements]

    return InvestigationResponse(
        run_id=final_state.run_id,
        incident_id=incident.id,
        status="COMPLETED" if final_state.validation_passed else "FINISHED_WITH_WARNINGS",
        selected_hypothesis=top_hypothesis,
        confidence=final_state.confidence,
        historical_candidates=final_state.retrieved_candidates,
        temporal_comparisons=temp_dims,
        remediation_applicability=applicability,
        agent_disagreements=disagreements,
        termination_reason=final_state.termination_reason or "COMPLETED_SUFFICIENT_EVIDENCE"
    )

@router.get("/traces/{run_id}", response_model=TraceDetailResponse, status_code=status.HTTP_200_OK)
def get_trace_detail(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves complete execution trace details, tool calls, and confidence progression for a run ID.
    Exposes no private hidden chain-of-thought.
    """
    trace = db.get(AgentTrace, run_id)
    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent trace for run ID '{run_id}' not found."
        )

    snapshot = trace.state_snapshot or {}
    steps = db.scalars(
        select(AgentStepExecution)
        .where(AgentStepExecution.trace_id == run_id)
        .order_by(AgentStepExecution.created_at.asc())
    ).all()

    agent_step_items: List[StepTraceItem] = []
    raw_trace_steps = snapshot.get("trace_steps", [])

    for idx, s in enumerate(steps):
        matching_meta = raw_trace_steps[idx] if idx < len(raw_trace_steps) else {}
        item = StepTraceItem(
            step_id=f"step-{idx + 1}",
            agent_name=matching_meta.get("agent_name", s.node_name.capitalize() + "Agent"),
            input_summary=matching_meta.get("input_summary", f"Step {idx + 1} input for node {s.node_name}"),
            output_summary=matching_meta.get("output_summary", f"Completed step {s.node_name}"),
            tool_calls=matching_meta.get("tool_calls", []),
            status=s.status.value if hasattr(s.status, "value") else str(s.status),
            confidence=matching_meta.get("confidence", 0.5),
            duration_ms=float(matching_meta.get("duration_ms", s.execution_time_ms or 0)),
            timestamp=matching_meta.get("timestamp", s.created_at.isoformat() if s.created_at else "")
        )
        agent_step_items.append(item)

    confidence_progression = [
        {"step": idx + 1, "agent": st.agent_name, "confidence": st.confidence}
        for idx, st in enumerate(agent_step_items)
    ]

    disagreements = [AgentDisagreement(**d) for d in snapshot.get("agent_disagreements", [])]

    return TraceDetailResponse(
        run_id=trace.id,
        incident_id=trace.incident_id or "unknown",
        status=trace.status.value if hasattr(trace.status, "value") else str(trace.status),
        agent_steps=agent_step_items,
        tool_calls=snapshot.get("tool_results", []),
        confidence_progression=confidence_progression,
        disagreements=disagreements,
        termination_reason=snapshot.get("termination_reason", "COMPLETED_SUFFICIENT_EVIDENCE")
    )
