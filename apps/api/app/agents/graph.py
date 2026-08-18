import uuid
import time
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from ghostops_shared import AgentStepStatus

from app.agents.base import AgentState
from app.agents.specialists.supervisor import SupervisorAgent
from app.agents.specialists.historian import HistorianAgent
from app.agents.specialists.investigator import InvestigatorAgent
from app.agents.specialists.temporal import TemporalReasoningAgent
from app.agents.specialists.validation import ValidationAgent
from app.db.models.agent_trace import AgentTrace, AgentStepExecution
from app.db.models.agent_decision import AgentDecision
from app.core.logging import logger

class OrchestratorGraph:
    """Stateful orchestrator graph manager for GhostOps multi-agent lifecycle."""

    def __init__(self):
        self.nodes = [
            "supervisor",
            "historian",
            "investigator",
            "temporal_reasoning",
            "validation",
            "completed"
        ]

    def run_investigation_graph(self, state: AgentState, db: Session) -> AgentState:
        """
        Executes Supervisor-controlled stateful investigation loop across specialist agents.
        Persists AgentTrace and AgentStepExecution records into CockroachDB.
        """
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        state.run_id = run_id
        state.thread_id = f"thread-{uuid.uuid4().hex[:8]}"

        logger.info(f"[OrchestratorGraph] Starting Stage 4 agent investigation run '{run_id}' for incident '{state.incident_id}'")

        # Create DB AgentTrace record
        db_trace = AgentTrace(
            id=run_id,
            incident_id=state.incident_id,
            graph_name="stage4_investigation_graph",
            thread_id=state.thread_id,
            status=AgentStepStatus.RUNNING,
            current_node="supervisor",
            state_snapshot=state.model_dump()
        )
        db.add(db_trace)
        db.commit()

        next_node = "supervisor"

        while True:
            # Check loop budget and route next step
            next_node = SupervisorAgent.route_next(state)
            state.current_node = next_node

            if next_node == "completed" or state.termination_reason is not None:
                if not state.termination_reason:
                    state.termination_reason = "COMPLETED_SUFFICIENT_EVIDENCE"
                break

            step_start = time.time()
            input_snapshot = state.model_dump()

            if next_node == "historian":
                state = HistorianAgent.run(state, db)
            elif next_node == "investigator":
                state = InvestigatorAgent.run(state, db)
            elif next_node == "temporal_reasoning":
                state = TemporalReasoningAgent.run(state, db)
            elif next_node == "validation":
                state = ValidationAgent.run(state, db)
            else:
                state.termination_reason = "UNKNOWN_NODE_TERMINATION"
                break

            execution_ms = int((time.time() - step_start) * 1000)
            output_snapshot = state.model_dump()

            # Record DB Step Execution
            step_exec = AgentStepExecution(
                trace_id=run_id,
                node_name=next_node,
                status=AgentStepStatus.SUCCESS,
                input_state={"current_node": input_snapshot.get("current_node"), "step": state.step_count},
                output_state={"current_node": output_snapshot.get("current_node"), "confidence": state.confidence},
                tool_calls={"count": len(state.tool_results)},
                execution_time_ms=execution_ms
            )
            db.add(step_exec)

            # Record into AgentDecision Ledger (§20, §26)
            decision = AgentDecision(
                incident_id=state.incident_id,
                agent=next_node,
                input_summary=f"Executed graph node '{next_node}' on state step {state.step_count}",
                output_json={
                    "current_node": next_node,
                    "confidence": state.confidence,
                    "disagreements": len(state.agent_disagreements),
                    "hypotheses_evaluated": len(state.hypotheses),
                },
                confidence=state.confidence,
                disagreement_flag=bool(state.agent_disagreements)
            )
            db.add(decision)
            db.commit()

        # Update trace final status
        db_trace.status = AgentStepStatus.SUCCESS
        db_trace.current_node = "completed"
        db_trace.state_snapshot = state.model_dump()
        db.commit()

        logger.info(f"[OrchestratorGraph] Completed Stage 4 investigation run '{run_id}'. Reason: {state.termination_reason}, Confidence: {state.confidence}")
        return state
