from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import AgentTrace, AgentStepExecution
from app.schemas.agent_trace import AgentTraceResponse
from app.schemas.agent_investigation import TraceDetailResponse, StepTraceItem, AgentDisagreement

router = APIRouter()

@router.get("", response_model=List[AgentTraceResponse])
def list_agent_traces(db: Session = Depends(get_db)):
    stmt = select(AgentTrace).order_by(AgentTrace.created_at.desc())
    return list(db.scalars(stmt).all())

@router.get("/{run_id}", response_model=TraceDetailResponse)
def get_agent_trace_detail(run_id: str, db: Session = Depends(get_db)):
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
