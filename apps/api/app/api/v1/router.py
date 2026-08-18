from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    incidents,
    memory,
    plans_governance,
    execution_governance,
    traces,
    investigation,
    learning,
    replay,
    sentinel,
    mcp,
    evaluation,
    demo
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(demo.router, tags=["End-to-End Demo Workflow"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
api_router.include_router(memory.router, prefix="/memory", tags=["Institutional Memory"])
api_router.include_router(plans_governance.router, tags=["Remediation Plans & Governance"])
api_router.include_router(execution_governance.router, tags=["Remediation Saga Execution"])
api_router.include_router(learning.router, tags=["Post-Remediation Learning & Memory Consolidation"])
api_router.include_router(replay.router, tags=["Ghost Replay & Simulation Engine"])
api_router.include_router(sentinel.router, tags=["Continuous Autonomous Sentinel"])
api_router.include_router(traces.router, prefix="/traces", tags=["Agent Traces"])
api_router.include_router(investigation.router, tags=["Agent Investigation"])
api_router.include_router(mcp.router, tags=["Model Context Protocol (MCP)"])
api_router.include_router(evaluation.router, tags=["Evaluation, Sandbox & Memory Bus"])
