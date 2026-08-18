from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models.evaluation import EvaluationRun, EvaluationCaseResult
from app.services.evaluation.harness import AgentEvaluationHarness
from app.integrations.cockroach.ccloud_sandbox import CockroachCloudSandboxManager
from app.services.cdc.memory_bus import CDCMemoryBus

router = APIRouter(tags=["Evaluation, Sandbox & Memory Bus"])

class DryRunRequest(BaseModel):
    command: str
    target_schema_version: str = "v24.1.0"

class CDCEventRequest(BaseModel):
    event_id: Optional[str] = None
    table: str = "remediation_outcomes"
    op: str = "INSERT"
    row: Dict[str, Any]
    mode: str = "TEST_EVENT_MODE"

class EvaluationRunRequest(BaseModel):
    dataset_version: str = "ghostops-golden-v1"

@router.post("/evaluation/benchmark")
@router.post("/evaluation/run")
def run_evaluation_benchmark(
    request: Optional[EvaluationRunRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Executes the Agent Evaluation Harness (§9.5) against the versioned golden incident dataset.
    Evaluates real hybrid retrieval, investigator evidence grounding, temporal reasoning, and safety regression gates.
    Persists evaluation results in CockroachDB.
    """
    dataset_ver = request.dataset_version if request else "ghostops-golden-v1"
    result = AgentEvaluationHarness.run_benchmark(db, dataset_version=dataset_ver)
    return result

@router.get("/evaluation/runs")
def list_evaluation_runs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Returns historical persisted evaluation runs sorted by started_at descending.
    """
    runs = db.scalars(
        select(EvaluationRun).order_by(desc(EvaluationRun.started_at)).limit(limit)
    ).all()
    return [
        {
            "id": r.id,
            "dataset_version": r.dataset_version,
            "status": r.status,
            "total_cases": r.total_cases,
            "precision_at_1": r.precision_at_1,
            "precision_at_3": r.precision_at_3,
            "mrr": r.mrr,
            "temporal_verdict_accuracy": r.temporal_verdict_accuracy,
            "evidence_grounding_score": r.evidence_grounding_score,
            "unsafe_replay_rate": r.unsafe_replay_rate,
            "false_execution_rate": r.false_execution_rate,
            "regression_gate_passed": r.regression_gate_passed,
            "summary": r.summary,
            "duration_ms": r.duration_ms,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None
        }
        for r in runs
    ]

@router.get("/evaluation/runs/{run_id}")
def get_evaluation_run(run_id: str, db: Session = Depends(get_db)):
    """
    Returns full details and case-by-case trace breakdowns for a specific evaluation run.
    """
    run = db.get(EvaluationRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Evaluation run '{run_id}' not found")

    cases = db.scalars(
        select(EvaluationCaseResult).where(EvaluationCaseResult.evaluation_run_id == run_id)
    ).all()

    return {
        "id": run.id,
        "dataset_version": run.dataset_version,
        "status": run.status,
        "total_cases": run.total_cases,
        "precision_at_1": run.precision_at_1,
        "precision_at_3": run.precision_at_3,
        "mrr": run.mrr,
        "temporal_verdict_accuracy": run.temporal_verdict_accuracy,
        "evidence_grounding_score": run.evidence_grounding_score,
        "unsafe_replay_rate": run.unsafe_replay_rate,
        "false_execution_rate": run.false_execution_rate,
        "regression_gate_passed": run.regression_gate_passed,
        "gate_details": run.gate_details,
        "summary": run.summary,
        "duration_ms": run.duration_ms,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "cases": [
            {
                "id": c.id,
                "benchmark_id": c.benchmark_id,
                "incident_id": c.incident_id,
                "case_category": c.case_category,
                "expected_root_cause": c.expected_root_cause,
                "actual_hypothesis": c.actual_hypothesis,
                "expected_precedent_id": c.expected_precedent_id,
                "retrieved_precedent_id": c.retrieved_precedent_id,
                "retrieval_rank": c.retrieval_rank,
                "retrieval_score": c.retrieval_score,
                "expected_temporal_verdict": c.expected_temporal_verdict,
                "actual_temporal_verdict": c.actual_temporal_verdict,
                "expected_safety_outcome": c.expected_safety_outcome,
                "actual_safety_outcome": c.actual_safety_outcome,
                "decision_match": c.decision_match,
                "safety_match": c.safety_match,
                "would_execute": c.would_execute,
                "unsafe_execution": c.unsafe_execution,
                "evidence_grounding_score": c.evidence_grounding_score,
                "trace_details": c.trace_details
            }
            for c in cases
        ]
    }

@router.get("/evaluation/cases/{case_id}")
def get_evaluation_case(case_id: str, db: Session = Depends(get_db)):
    """
    Returns trace details for a single evaluation case.
    """
    case = db.get(EvaluationCaseResult, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Evaluation case '{case_id}' not found")
    return {
        "id": case.id,
        "evaluation_run_id": case.evaluation_run_id,
        "benchmark_id": case.benchmark_id,
        "incident_id": case.incident_id,
        "case_category": case.case_category,
        "expected_root_cause": case.expected_root_cause,
        "actual_hypothesis": case.actual_hypothesis,
        "expected_precedent_id": case.expected_precedent_id,
        "retrieved_precedent_id": case.retrieved_precedent_id,
        "retrieval_rank": case.retrieval_rank,
        "retrieval_score": case.retrieval_score,
        "expected_temporal_verdict": case.expected_temporal_verdict,
        "actual_temporal_verdict": case.actual_temporal_verdict,
        "expected_safety_outcome": case.expected_safety_outcome,
        "actual_safety_outcome": case.actual_safety_outcome,
        "decision_match": case.decision_match,
        "safety_match": case.safety_match,
        "would_execute": case.would_execute,
        "unsafe_execution": case.unsafe_execution,
        "evidence_grounding_score": case.evidence_grounding_score,
        "trace_details": case.trace_details
    }

@router.post("/sandbox/dry-run")
def execute_sandbox_dry_run(request: DryRunRequest):
    """
    Spins up an ephemeral CockroachDB Cloud sandbox via ccloud CLI (§13, §19.4),
    tests command safety/range-split behavior under specified schema version, and tears down.
    """
    sandbox_ctx = CockroachCloudSandboxManager.provision_ephemeral_sandbox()
    try:
        result = CockroachCloudSandboxManager.execute_dry_run(
            sandbox_ctx,
            command=request.command,
            target_schema_version=request.target_schema_version
        )
        return result
    finally:
        CockroachCloudSandboxManager.teardown_sandbox(sandbox_ctx)

@router.post("/cdc/event")
def process_changefeed_event(request: CDCEventRequest, db: Session = Depends(get_db)):
    """
    Processes an incoming CockroachDB CHANGEFEED event to propagate trust scores and operational memory (§19.2).
    """
    result = CDCMemoryBus.handle_changefeed_event(request.model_dump(), db)
    return result

@router.get("/cdc/status")
def get_cdc_status():
    """
    Returns CockroachDB Changefeed consumer real-time connection status and metrics.
    """
    from app.services.cdc.consumer import CockroachCDCConsumer
    return CockroachCDCConsumer.get_status().model_dump()
