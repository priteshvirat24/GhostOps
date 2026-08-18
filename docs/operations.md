# GhostOps Operations Runbook

> "The production memory that survives the engineer."

## Overview

GhostOps is an autonomous institutional memory and remediation system for production infrastructure. This operational runbook documents deployment, sentinel operation, plan approval workflows, saga execution, post-remediation learning, replay simulation, and incident recovery.

---

## 1. Environment & Deployment Modes

GhostOps operates in three distinct environment modes:

| Mode | `APP_ENV` | `AWS_MOCK_MODE` | `BEDROCK_MOCK_MODE` | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Development** | `development` | `True` | `True` | In-memory SQLite DB, mock AWS adapters, mock Bedrock embeddings. |
| **Test** | `test` | `True` | `True` | Pytest suite execution mode. Mocks permitted. |
| **Production** | `production` | `False` | `False` | Real CockroachDB cluster, live AWS SDK adapters, live Bedrock LLM. **Fails fast on missing credentials.** |

---

## 2. Sentinel Monitoring Operations

The Stage 9 Autonomous Sentinel continuously observes telemetry without alert storms or unauthorized execution:

### Sentinel Modes
- `OBSERVE_ONLY`: Normalizes telemetry and records alerts/incidents without auto-triggering agents.
- `DETECT_AND_INVESTIGATE`: Auto-triggers Stage 4 multi-agent investigation and Stage 8 ghost replay.
- `DETECT_INVESTIGATE_AND_PLAN`: Auto-triggers Stage 4 investigation, Stage 8 ghost replay, and Stage 5 plan proposals.

### Sentinel Governance Boundaries
> **CRITICAL**: The Sentinel (`SYSTEM` role) can propose remediation plans (`PENDING_APPROVAL`), but **MUST NEVER** autonomously approve or execute remediation plans.

---

## 3. Human Plan Approval & Governance Workflow

1. **Proposal**: Stage 5 Governed Remediation Planner generates a plan in `PENDING_APPROVAL` status.
2. **Safety Check Validation**: Automated validation checks (drift detection, lock conflict, schema verification, parameter bounds).
3. **Human Approval**: Authorized DevOps Engineer (`ADMIN` role) approves the plan via Web UI or API. High-risk plans require typed confirmation phrases.
4. **Advance to Ready**: Approval advances plan status to `READY_FOR_EXECUTION`.

---

## 4. Saga Execution & Recovery

1. **Transactional Locking**: Execution acquires a resource lock (`ExecutionLockRecord`) preventing concurrent execution on the same resource.
2. **Prechecks**: Fresh state verification, non-expired lock check, and safety check re-evaluation.
3. **Step Execution & Verification**: Sequential execution with pre/post-state diff logging and verification.
4. **Failure & Rollback**: Step failure triggers reverse compensation (LIFO order) to restore baseline infrastructure state.
