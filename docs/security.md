# GhostOps Security & Prompt Injection Defense Architecture

> "Operational data is untrusted data and must never become executable instructions."

## Overview

GhostOps processes raw telemetry, logs, CloudWatch alarms, and CloudTrail events. These inputs are treated as **untrusted user data** and strictly isolated from LLM system prompt instructions.

---

## 1. Prompt Injection Boundary & Untrusted Data Isolation

1. **Separation of Instructions & Context**: System prompts are immutable. Telemetry payloads and log strings are passed strictly within delimited data blocks (`<telemetry_payload>` tags).
2. **No Dynamic Code Generation**: Agents never generate raw Python, Bash, or SQL scripts for direct execution.
3. **Governed Action Catalog**: Agents select only typed action enum types (`CHANGE_SECURITY_RULE`, `ADJUST_CONNECTION_POOL`, `SCALE_RESOURCE`, `RESTART_SERVICE`, `ROTATE_CONFIGURATION`, `ROLLBACK_DEPLOYMENT`, `REVERT_CONFIGURATION`, `DRAIN_RESOURCE`).

---

## 2. Role-Based Access Control (RBAC)

| Role | View Incidents / Memory | Trigger Investigation / Replay | Create Plan Proposals | Approve Plan | Execute Plan | Modify Sentinel Policy |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `READ_ONLY` | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| `OPERATOR` | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| `ADMIN` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `SYSTEM` | ✓ | ✓ | ✓ | **FORBIDDEN** | **FORBIDDEN** | ✗ |

> **CRITICAL**: The `SYSTEM` role is programmatically prohibited from approving or executing remediation plans. Any attempt by `SYSTEM` to invoke approval or execution endpoints fails closed with `HTTP 403 AUTONOMOUS_EXECUTION_FORBIDDEN`.

---

## 3. Secret Redaction & Log Hygiene

The `StructuredJSONFormatter` in `app.core.logging` automatically redacts sensitive headers, access keys, secrets, and authorization tokens:
- `AWS_SECRET_ACCESS_KEY` $\rightarrow$ `[REDACTED_SECRET]`
- `authorization` $\rightarrow$ `[REDACTED_SECRET]`
- `db_password` $\rightarrow$ `[REDACTED_SECRET]`

Private chain-of-thought is never stored or exposed via API.
