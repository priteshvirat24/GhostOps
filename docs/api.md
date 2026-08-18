# GhostOps REST API Reference Specification

## Overview

Base URL: `http://localhost:8000/api/v1`

---

## Endpoint Summary

### Health & Metrics
- `GET /health` - System health probe
- `GET /ready` - System readiness probe
- `GET /live` - Process liveness probe
- `GET /metrics` - Prometheus metrics exposition

### Incident Ingestion & History (Stage 2 & 3)
- `GET /incidents` - List ingested incidents
- `GET /incidents/{id}` - Incident detail
- `GET /incidents/{id}/evidence` - Ingested evidence
- `GET /incidents/{id}/similar` - Hybrid memory retrieval

### Agent Investigation (Stage 4)
- `POST /incidents/{id}/investigate` - Multi-agent investigation run
- `GET /traces/{run_id}` - Agent execution trace

### Governed Remediation Planning (Stage 5)
- `POST /incidents/{id}/plans` - Propose governed remediation plan
- `GET /plans/{plan_id}` - Plan detail
- `POST /plans/{plan_id}/validate` - Safety Engine validation
- `POST /plans/{plan_id}/approve` - Human approval gate (`ADMIN` role required)
- `POST /plans/{plan_id}/reject` - Human rejection gate

### Controlled Saga Execution (Stage 6)
- `POST /plans/{plan_id}/execute` - Controlled saga execution
- `GET /executions/{id}` - Execution status & step details
- `POST /executions/{id}/cancel` - Cancel active execution
- `POST /executions/{id}/rollback` - Manual rollback trigger

### Institutional Learning (Stage 7)
- `POST /incidents/{id}/learn` - Trigger post-remediation learning
- `GET /incidents/{id}/learning` - Learning summary
- `GET /learning/review-queue` - Memory candidates review queue
- `POST /learning/candidates/{id}/approve` - Approve candidate
- `POST /learning/candidates/{id}/reject` - Reject candidate

### Ghost Replay Simulation (Stage 8)
- `POST /replay/incidents/{id}` - Incident historical replay
- `POST /replay/counterfactual` - Counterfactual simulation
- `POST /replay/drift-simulation` - Infrastructure drift simulation
- `GET /replay/{id}` - Replay run summary
- `GET /replay/{id}/provenance` - Step & mutation provenance
- `GET /replay/regressions` - Detected memory regressions

### Continuous Autonomous Sentinel (Stage 9)
- `GET /sentinel/status` - Sentinel health & status
- `POST /sentinel/start` - Start sentinel
- `POST /sentinel/stop` - Stop sentinel
- `POST /sentinel/pause` - Pause sentinel
- `POST /sentinel/resume` - Resume sentinel
- `POST /sentinel/policy` - Update policy settings
- `POST /sentinel/ingest-event` - Ingest telemetry event
- `GET /sentinel/decisions` - Audit decision log
