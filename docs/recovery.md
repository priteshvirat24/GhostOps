# GhostOps Process Restart & Disaster Recovery Runbook

## Overview

GhostOps is designed to recover cleanly after unexpected API process crashes or server restarts without losing audit history, leaving resource locks acquired, or executing unverified remediations.

---

## 1. Process Restart Recovery Services

At startup or via scheduled reconciliation, GhostOps executes three recovery services:

### `ExecutionRecoveryService`
- Scans `remediation_executions` table for runs stuck in `EXECUTING`, `VERIFYING`, or `COMPENSATING` where `updated_at` exceeds `EXECUTION_TIMEOUT_SECONDS` (600s).
- Marks stale executions as `FAILED` with termination reason `RECONCILED_PROCESS_RESTART`.
- Scans `execution_locks` table for active locks where `expires_at` has passed, setting `status = 'RELEASED'`.

### `ReplayRecoveryService`
- Scans `replay_runs` table for simulation runs stuck in `RECONSTRUCTING`, `SIMULATING`, or `COMPARING`.
- Marks stale replay runs as `FAILED` with termination reason `RECONCILED_PROCESS_RESTART`.

### `SentinelRecoveryService`
- Reconciles `sentinel_instances` state, verifying heartbeat and resuming monitoring cycles cleanly.

---

## 2. Infrastructure Re-Verification Before Retry

If an execution was interrupted by a process restart:
1. The execution is marked `FAILED` (never automatically resumed).
2. A new plan must be generated or re-validated against fresh infrastructure state before execution can be re-triggered.
3. Audit trails remain completely intact.
