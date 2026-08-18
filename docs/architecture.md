# GhostOps System Architecture

> "The production memory that survives the engineer."

## Overview

GhostOps is an autonomous institutional memory and remediation system for production infrastructure. It addresses institutional knowledge decay, transient production outages, un-documented infrastructure state changes, and automated remediation without human cognitive overload.

## The Operational Memory Lifecycle

GhostOps follows a 10-stage operational loop:

```
Production Telemetry → Observe (Sentinel) → Understand (Historian) 
→ Remember & Retrieve (Memory Engine) → Compare (Temporal Reasoning)
→ Validate (Safety & Governance) → Act (Execution Engine) 
→ Verify (Independent Audit) → Learn (Post-Remediation Consolidation)
→ Replay & Simulate (Ghost Engine) → Production Hardening
```

## System Reference Architecture

```
                       ┌─────────────────────────┐
                       │  AWS Infrastructure     │
                       │ (CloudWatch/Trail/Config)│
                       └────────────┬────────────┘
                                    │
                                    ▼
                         ┌────────────────────┐
                         │ Autonomous Sentinel│
                         └──────────┬─────────┘
                                    │
                                    ▼
                         ┌────────────────────┐
                         │ Anomaly & Dedup    │
                         └──────────┬─────────┘
                                    │
                                    ▼
                         ┌────────────────────┐
                         │   CockroachDB      │
                         │ (System of Record) │
                         └──────────┬─────────┘
                                    │
                                    ▼
                         ┌────────────────────┐
                         │  LangGraph Agent   │
                         │    Orchestrator    │
                         └──────────┬─────────┘
                                    │
    ┌──────────────┬────────────────┼────────────────┬──────────────┐
    │              │                │                │              │
    ▼              ▼                ▼                ▼              ▼
┌───────┐   ┌────────────┐   ┌─────────────┐   ┌────────────┐  ┌─────────────┐
│Histo- │   │Investigator│   │  Temporal   │   │ Safety &   │  │ Governed    │
│ rian  │   │   Agent    │   │  Reasoning  │   │ Governance │  │ Saga Exec   │
└───────┘   └────────────┘   └─────────────┘   └────────────┘  └──────┬──────┘
                                                                      │
                                                                      ▼
                                                               ┌─────────────┐
                                                               │ Verification│
                                                               └──────┬──────┘
                                                                      │
                                                                      ▼
                                                               ┌─────────────┐
                                                               │ Ghost Replay│
                                                               │ Simulation  │
                                                               └──────┬──────┘
                                                                      │
                                                                      ▼
                                                               ┌─────────────┐
                                                               │ CockroachDB │
                                                               │ Audit Trace │
                                                               └─────────────┘
```

## 10-Stage Implementation Roadmap

1. **Stage 1: Project Foundation & Architecture** (Completed) - Clean monorepo structure, database schemas, mock AWS adapters, health checks.
2. **Stage 2: Production Incident Ingestion & Evidence Baseline** (Completed) - Raw evidence preservation vs generated interpretation.
3. **Stage 3: Historical Memory Retrieval Engine** (Completed) - Hybrid vector + structured query scoring engine in CockroachDB.
4. **Stage 4: Evidence-Backed Agentic Investigation Engine** (Completed) - LangGraph multi-agent orchestration, temporal reasoning, hypothesis generation.
5. **Stage 5: Governed, Explainable & Human-Approvable Remediation Planning Engine** (Completed) - 9 action catalog types, safety checks, drift detector, human approval gates.
6. **Stage 6: Controlled Saga Execution & Rollback Engine** (Completed) - Idempotency, prechecks, transactional locks, pre/post-state diffs, reverse compensation, verification.
7. **Stage 7: Post-Remediation Learning & Institutional Memory Consolidation Engine** (Completed) - Outcome analysis, effectiveness scoring, positive & negative knowledge, candidate generation, deduplication, non-destructive supersession, bounded confidence calibration (0.0 to 0.95), review queue, provenance APIs, and Next.js frontend UI.
8. **Stage 8: Ghost Replay & Simulation Engine** (Completed) - Historical scenario reconstruction, isolated simulation environment (zero live mutation), 4 replay modes, deterministic ReplayScore formula (0.0 to 1.0), memory regression detector, changefeed monitor, and Next.js UI.
9. **Stage 9: Continuous Autonomous Sentinel** (Completed) - Telemetry normalizer, anomaly engine, sliding-window deduplication, alert storm protection, incident correlator, autonomous orchestrator, sentinel decisions audit trail, policy controls, zero unauthorized execution safeguard, and Next.js UI.
10. **Stage 10: Production Hardening, Reliability, Security & System Polish** (Completed) - Production configuration fail-fast validation, structured JSON logging with correlation IDs, standardized API error responses, RBAC authorization boundary, idempotency manager, process restart recovery services, circuit breakers, classified retries, health/ready/live/metrics Prometheus probes, fail-closed replay simulation safety, Next.js ProductionDashboardSection UI, 74 passed pytest cases, operational runbooks, and production readiness audit checklist.
