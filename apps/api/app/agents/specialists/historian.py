import time
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.agents.base import AgentState
from app.agents.tools import ReadOnlyInvestigationTools
from app.core.logging import logger

class HistorianAgent:
    """
    Historian Specialist Agent for GhostOps Stage 4.
    Interrogates Stage 3 hybrid retrieval engine, extracts candidate evidence and action histories,
    and identifies both failed and successful historical operational attempts.
    """

    @staticmethod
    def run(state: AgentState, db: Session) -> AgentState:
        t0 = time.time()
        logger.info(f"[HistorianAgent] Interrogating historical memory for incident '{state.incident_id}'")

        tool_res = ReadOnlyInvestigationTools.search_historical_memory(db, state.incident_id, limit=5)
        state.tool_results.append(tool_res.model_dump())

        if tool_res.success and tool_res.data:
            retrieval_data = tool_res.data
            candidates = retrieval_data.get("candidates", [])
            state.retrieved_candidates = candidates

            # Select top candidate for temporal investigation
            if candidates:
                top = candidates[0]
                state.selected_candidates = [top]

                # Fetch top candidate's snapshot and actions
                top_inc_id = top.get("incident_id")
                snap_res = ReadOnlyInvestigationTools.get_infrastructure_snapshot(db, top_inc_id)
                if snap_res.success and snap_res.data:
                    state.historical_snapshots = [snap_res.data]

                ev_res = ReadOnlyInvestigationTools.get_incident_evidence(db, top_inc_id)
                if ev_res.success and ev_res.data:
                    state.historical_evidence = ev_res.data

        duration = round((time.time() - t0) * 1000, 2)
        state.trace_steps.append({
            "step_id": f"step-{len(state.trace_steps) + 1}",
            "agent_name": "HistorianAgent",
            "input_summary": f"Retrieved candidates for incident {state.incident_id}",
            "output_summary": f"Found {len(state.retrieved_candidates)} historical candidates in CockroachDB",
            "tool_calls": [tool_res.model_dump()],
            "status": "SUCCESS" if state.retrieved_candidates else "NO_CANDIDATES",
            "confidence": 0.85 if state.retrieved_candidates else 0.30,
            "duration_ms": duration,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })

        return state
