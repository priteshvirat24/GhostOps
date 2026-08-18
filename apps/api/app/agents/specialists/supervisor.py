from typing import Dict, Any, Optional
from app.agents.base import AgentState
from app.core.logging import logger

class SupervisorAgent:
    """
    Supervisor Agent for GhostOps Stage 4.
    Manages workflow routing between specialist nodes, checks evidence sufficiency,
    and strictly enforces loop budgets (max_steps, max_retrieval_rounds, max_reflection_rounds).
    """

    @staticmethod
    def route_next(state: AgentState) -> str:
        state.step_count += 1
        logger.info(f"[Supervisor] Evaluating graph state for run '{state.run_id}'. Step {state.step_count}/{state.max_steps}")

        # Check loop budget limits
        if state.step_count > state.max_steps:
            state.termination_reason = "BUDGET_EXCEEDED"
            logger.warning(f"[Supervisor] Max step budget ({state.max_steps}) exceeded for run '{state.run_id}'. Terminating.")
            return "completed"

        if state.retrieval_rounds > state.max_retrieval_rounds:
            state.termination_reason = "RETRIEVAL_BUDGET_EXCEEDED"
            logger.warning(f"[Supervisor] Max retrieval budget ({state.max_retrieval_rounds}) exceeded. Proceeding to validation.")
            return "validation"

        if state.reflection_rounds > state.max_reflection_rounds:
            state.termination_reason = "REFLECTION_BUDGET_EXCEEDED"
            logger.warning(f"[Supervisor] Max reflection budget ({state.max_reflection_rounds}) exceeded. Completing.")
            return "completed"

        current = state.current_node

        if current == "supervisor" or current == "sentinel":
            return "historian"

        if current == "historian":
            return "investigator"

        if current == "investigator":
            # If investigator had low confidence (< 0.40) and retrieval budget allows, route to Historian
            if state.confidence < 0.40 and state.retrieval_rounds < state.max_retrieval_rounds:
                state.retrieval_rounds += 1
                logger.info(f"[Supervisor] Investigator reported low confidence ({state.confidence:.2f}). Routing to Historian for additional historical memory retrieval.")
                return "historian"
            return "temporal_reasoning"

        if current == "temporal_reasoning":
            return "validation"

        if current == "validation":
            if state.critic_feedback and not state.critic_feedback.get("approved", True):
                state.reflection_rounds += 1
                if state.confidence < 0.4 and state.retrieval_rounds < state.max_retrieval_rounds:
                    state.retrieval_rounds += 1
                    logger.info("[Supervisor] Critic rejected with low confidence. Routing back to Historian for more evidence.")
                    return "historian"
                elif state.reflection_rounds <= state.max_reflection_rounds:
                    logger.info("[Supervisor] Critic requested reflection. Routing back to Investigator.")
                    return "investigator"

            state.termination_reason = "COMPLETED_SUFFICIENT_EVIDENCE"
            return "completed"

        return "completed"
