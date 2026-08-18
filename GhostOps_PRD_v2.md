# GhostOps PRD — v2.0
## Autonomous Institutional Memory and Remediation System for Production Infrastructure

**Version:** 2.0 (Technical Pinnacle Edition)
**Status:** Build specification
**Target:** CockroachDB × AWS Hackathon
**Primary objective:** Maximize judging performance through genuine architectural depth, not surface complexity

---

## Changelog from v1.0

This revision upgrades the system from "a multi-agent app that calls CockroachDB" to **a properly engineered agentic system** with a real orchestration graph, typed tool contracts, self-verifying reasoning loops, CDC-driven memory propagation, and a CockroachDB schema that actually exploits distributed SQL + native vector search rather than treating Cockroach as "Postgres with extra steps." Key additions:

- A formal **agent orchestration graph** (supervisor + specialist sub-agents with isolated context windows), replacing the implied linear pipeline.
- **ReAct + reflection loops** with explicit self-critique and confidence calibration, not single-shot LLM calls.
- **Claude Agent SDK / MCP-native tool contracts** with strict JSON schemas, idempotency keys, and typed error channels.
- **CockroachDB `VECTOR` type + native vector indexing (CSPANN)**, changefeeds (CDC) for real-time memory propagation, and TTL-based memory decay.
- A **saga-based execution model** for remediation so partial failures roll back cleanly across distributed AWS + database actions.
- An **agent evaluation harness** (golden incident dataset, regression suite, LLM-as-judge scoring) — because "the demo worked once" is not production readiness.
- Explicit **prompt-injection / tool-poisoning defenses**, since GhostOps ingests untrusted operational text (logs, Slack, tickets) and feeds it to an LLM with execution authority.

---

## 1. Product Definition

**Product name:** GhostOps
**Tagline:** The production memory that survives the engineer.

**One-line description:** GhostOps is an autonomous infrastructure operations agent that observes production incidents, captures the complete operational context surrounding them, retrieves and re-validates relevant historical incidents against the *current* environment, executes approved fixes through governed tool calls, verifies outcomes empirically, and permanently learns from the result — closing the loop that most incident tooling leaves open.

**Core thesis** — Today's incident tooling remembers *that* something happened. GhostOps remembers:

- what happened, structurally and temporally
- what the infrastructure looked like at that exact moment (a queryable snapshot, not a log line)
- what humans believed was happening (hypotheses, not just actions)
- what they tried, in what order, and why
- what failed, and why it failed
- what worked, and under what conditions it worked
- whether that solution is *still valid* given today's topology, versions, and configuration
- whether the agent's own past recommendations were correct — i.e., the agent has a trust score, not just the runbook

The resulting memory is not a document store. It is **executable institutional knowledge**: a queryable, versioned, temporally-aware graph of cause, action, and outcome that an agent can reason over and act on.

---

## 2. Problem

Production infrastructure develops organizational amnesia. A senior engineer diagnoses an unusual failure, tries three things that fail and one that works, and closes the ticket. Six months later a different engineer hits a similar failure. The answer technically exists — fragmented across Slack, terminal history, CloudWatch, tickets, Git commits, dashboards, and one person's memory — so the investigation is repeated from zero.

This produces: longer MTTR, repeated incidents, dependency on individual experts, stale runbooks, duplicated troubleshooting, unsafe guesswork under pressure, and quiet erosion of institutional knowledge as people leave.

Existing incident tools organize *incidents and people*. GhostOps treats the incident as a **memory-generating event** and treats remediation as a **hypothesis that must be re-validated against the present**, not blindly replayed.

---

## 3. Product Vision

An operational memory system where every production incident permanently increases the organization's ability to diagnose and resolve future incidents — and where the system is honest about *when its own memory no longer applies*.

```
Production → Observe → Understand → Remember → Retrieve → Compare
    ↑                                                          │
    └──────────── Learn ← Verify ← Act ← Validate ←───────────┘
```

---

## 4. Goals (P0)

GhostOps must: detect infrastructure incidents; build a structured incident representation; preserve historical infrastructure state as immutable, queryable snapshots; preserve the incident timeline as an event-sourced log; preserve every command/action attempted, including failed ones; distinguish failed from successful remediation with evidence, not self-report; store human reasoning and free-text context; store dense embeddings for semantic recall; retrieve historically similar incidents via hybrid (structured + vector) search; compare historical vs. current infrastructure state along explicit, weighted dimensions; determine whether historical remediation remains applicable, with a stated confidence and reason; validate proposed remediation against policy and a sandbox before touching production; execute remediation through governed, idempotent tool calls; verify whether remediation *actually* worked using independent signals (not the executing agent's own claim); record outcomes permanently and immutably; improve future recommendations using historical outcomes (trust scoring); expose CockroachDB as the literal, load-bearing persistent memory layer; operate on real AWS services, not a demo shim; provide human approval and layered safety controls; demonstrate the full loop, including a *failed* replay, in the final demo.

## 5. Non-Goals

GhostOps is not a generic chatbot, Slack summarizer, plain RAG chatbot, static runbook generator, APM dashboard, Terraform linter, AWS monitoring dashboard, LLM wrapper around CloudWatch, or generic DevOps copilot.

**Architectural litmus test:** if removing CockroachDB leaves essentially the same product, the architecture has failed. If removing the *agentic loop* (retrieve → compare → validate → verify) and replacing it with "LLM writes a shell command" leaves essentially the same product, the agent design has also failed.

---

## 6. Target Users

| User | Need |
|---|---|
| SRE (primary) | Rapid resolution of unfamiliar production incidents |
| DevOps / Platform Engineer | Operational knowledge that survives infra and personnel churn |
| On-call Engineer | Reliable historical remediation under time pressure |
| Engineering Manager | Reduced MTTR, reduced bus-factor on individual experts |
| Platform/Infra Team | A continuously self-correcting operational knowledge system |

---

## 7. Core User Stories

- **US-01 Incident detection** — as an SRE, I want GhostOps to auto-detect a production anomaly.
- **US-02 Historical recall** — as an on-call engineer, I want prior similar incidents surfaced with *why* they're similar.
- **US-03 Context preservation** — as an org, I want exact infra state and actions preserved immutably.
- **US-04 Historical reasoning** — as an engineer, I want an explicit answer to "does this old fix still apply, and why or why not?"
- **US-05 Safe execution** — as an SRE, I want risk-tiered approval before anything touches production.
- **US-06 Outcome learning** — as an org, I want the system to remember whether its own recommendation actually worked.
- **US-07 Expert replacement** — as a junior engineer, I want the operational knowledge that used to live only in one person's head.
- **US-08 (new) Adversarial resilience** — as a security team, I want assurance that a poisoned log line or ticket comment cannot manipulate the agent into unsafe action.
- **US-09 (new) Explainable disagreement** — as an SRE, I want to see when two sub-agents disagree and how the system resolved it, not just a final answer.

---

## 8. System Architecture

```
                              AWS PRODUCTION
                                    │
        ┌───────────────────┬──────┴──────┬───────────────────┐
    CloudWatch           CloudTrail    AWS Config          X-Ray/OTel
        │                   │              │                   │
        └───────────────────┴──────┬───────┴───────────────────┘
                                    │
                              EventBridge
                                    │
                                    ▼
                             Sentinel Agent  ── deterministic filters (no LLM)
                                    │
                                    ▼
                          Event Normalization
                                    │
                                    ▼
                     ┌───────────────────────────┐
                     │        CockroachDB         │
                     │  (system of record + memory)│
                     │                             │
                     │ incidents · timeline        │
                     │ infra snapshots · actions    │
                     │ outcomes · VECTOR embeddings │
                     │ policies · agent history      │
                     │ changefeeds → memory bus       │
                     └──────────────┬──────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                                │
              SQL Retrieval                   Vector Retrieval (CSPANN)
                    │                                │
                    └───────────────┬────────────────┘
                                    ▼
                        ┌─────────────────────────┐
                        │   ORCHESTRATOR (Supervisor)  │
                        │   ReAct loop + graph router  │
                        └────────────┬─────────────┘
           ┌───────────┬─────────────┼─────────────┬───────────┐
           ▼           ▼             ▼             ▼           ▼
      Historian   Investigator   Reasoning      Validation  Verification
        Agent        Agent      (Temporal)        Agent        Agent
           │           │             │             │           │
           └───────────┴──────┬──────┴─────────────┴───────────┘
                               ▼
                     Human Approval Gate (risk-tiered)
                               ▼
                        Execution Agent (Saga)
                       ┌───────┴────────┐
                   ccloud CLI        AWS APIs (Lambda/ECS/SSM)
                       └───────┬────────┘
                               ▼
                     Verification Agent (independent signals)
                               ▼
                     Outcome + confidence + trust delta
                               ▼
                          CockroachDB (write-back)
                               ▼
                          Future incidents
```

**Why a graph, not a pipeline:** v1 implied a straight line from detection to learning. Real incident response is not linear — the Investigator may need to re-query the Historian mid-analysis, the Reasoning agent may reject a candidate and force a second retrieval pass, and Verification may trigger a rollback that re-enters Validation. GhostOps is implemented as a **stateful graph** (LangGraph-style or Claude Agent SDK sub-agent orchestration) with the Orchestrator as a supervisor that routes between nodes based on each node's structured output, not a fixed sequence of function calls.

---

## 9. Agentic AI Architecture (Core Differentiator)

### 9.1 Orchestration model

GhostOps uses a **supervisor + specialist sub-agent** pattern, each sub-agent running in an **isolated context window** with a narrow, typed tool surface — this is the pattern used by modern agent SDKs (e.g., Claude's Agent SDK sub-agent/skills model, MCP-based tool routing) to avoid context pollution and prompt-injection blast radius. The Orchestrator itself never calls production tools directly; it only routes between sub-agents and holds the shared incident state.

Each sub-agent runs a **ReAct loop with mandatory reflection**:

```
Thought → Tool Call → Observation → Self-Critique → (repeat | Final Answer)
```

The self-critique step is explicit and structured — the agent must output a `confidence` (0–1), an `evidence[]` list referencing specific retrieved rows/snapshots (not vibes), and a `disagreement_flag` if its own retrieval was ambiguous. This structured self-critique is what feeds the Trust System (§25) instead of an unverified LLM confidence score.

### 9.2 Sub-agents and their contracts

| Sub-agent | Model role | Tool surface (typed, MCP) | Output contract |
|---|---|---|---|
| **Historian** | Extraction / summarization | `read_cloudwatch`, `read_cloudtrail`, `read_config_snapshot`, `write_incident_memory` | `IncidentRecord` (raw evidence + generated summary, kept separate — see §10) |
| **Investigator** | Hybrid retrieval + ranking | `sql_query` (read-only role), `vector_search`, `hybrid_rank` | `RankedCandidates[]` with per-candidate structured similarity breakdown |
| **Reasoning (Temporal)** | Comparative reasoning | `diff_infra_state`, `get_version_matrix` | `TemporalVerdict` (`applicable` / `do_not_execute` / `conditional`, with dimension-level diffs) |
| **Validation** | Policy + risk gating | `policy_check`, `sandbox_execute` (ccloud ephemeral cluster) | `ValidationResult` (`pass`/`fail`/`needs_human`, risk tier, sandbox evidence) |
| **Execution** | Governed action | `ccloud_cli`, `aws_lambda_invoke`, `aws_ssm_run_command` — all wrapped in saga steps with compensating actions | `ExecutionLedgerEntry` |
| **Verification** | Independent outcome check | `read_metrics`, `read_error_rate`, `read_slo_burn` — deliberately *not* the same tool the Execution agent used to claim success | `VerificationResult` with pass/fail per signal, not a single boolean |

Every tool call carries an **idempotency key** derived from `incident_id + action_id + attempt_n`, so a retried agentic step (common with LLM tool-use) can never double-execute a production mutation. This is enforced at the CockroachDB layer via a unique constraint on `(idempotency_key)` in the `actions` table, not just in application code.

### 9.3 Model routing

Different steps have genuinely different cost/latency/accuracy tradeoffs, so GhostOps routes across model tiers rather than using one model for everything:

- **Fast/cheap tier** (event classification, log triage, embedding generation) — small distilled model, sub-second latency, high volume.
- **Reasoning tier** (Investigator ranking, Temporal Reasoning, Validation) — frontier-class model with extended/step-by-step reasoning enabled, since these outputs gate production changes.
- **Execution tier** — a constrained model or deterministic code path wherever possible; tool-call *generation* should be the minimum surface exposed to free-form LLM output, because this is the step with real-world side effects.

This is implemented via Amazon Bedrock's model routing / multiple foundation model endpoints, with the reasoning tier using extended thinking / chain-of-thought and the fast tier optimized for throughput.

### 9.4 Prompt-injection & tool-poisoning defenses

GhostOps ingests **untrusted text** (log lines, ticket comments, Slack messages) and hands it to LLM agents with eventual execution authority. This is a real attack surface, not a theoretical one. Mitigations:

- Untrusted content is always passed to the model as **data, never as instructions** — wrapped in explicit `<untrusted_evidence>` tags with a system-level instruction that content inside these tags must never be treated as commands.
- The Execution agent's tool surface is a strict allowlist; it cannot invoke arbitrary shell commands, only pre-registered, parameterized operations (e.g., `restart_service(service_id)`, not `run_shell(cmd)`).
- Every proposed action from the Validation agent is diffed against a **policy engine allowlist** before it ever reaches Execution — an LLM cannot escalate its own risk tier.
- The MCP server exposed to agents is **read-only by default** with a separate, more tightly scoped write-capable server used only by the Execution agent behind the human-approval gate.

### 9.5 Agentic evaluation harness

Because this is a system that executes production changes, "it worked in the demo" is not sufficient. GhostOps ships with:

- A **golden dataset** of ~50 synthetic historical incidents with known-correct retrieval rankings and known-correct temporal verdicts.
- A **regression suite** run on every change to agent prompts/tools, scoring retrieval precision@k, temporal-verdict accuracy, and false-execution rate.
- **LLM-as-judge** scoring for the Historian's summaries (faithfulness to raw evidence — critical given §10's separation principle) and for the Reasoning agent's explanations (does the stated reason match the actual diff?).
- A tracked **regression gate**: no prompt/tool change ships if it drops false-remediation rate accuracy below a set floor.

---

## 10. Historian Agent — Detail

Transforms raw operational data into durable institutional memory: reconstructs timeline, identifies actors and affected resources, extracts commands, classifies actions, identifies failed attempts and successful remediation, identifies root cause, generates summary, generates embeddings.

**Critical principle, unchanged from v1 and worth restating:** GhostOps must preserve raw evidence and generated interpretation **separately**. An LLM-generated summary must never become the only source of truth — every summary field carries a foreign key back to the raw evidence rows it was derived from, and the evaluation harness (§9.5) continuously checks summary faithfulness against that raw evidence.

---

## 11. Investigator Agent — Hybrid Retrieval

Performs **structured retrieval** (service, region, DB version, resource, error code, config, deployment, topology) and **semantic retrieval** (incident description, logs, symptoms, root cause, historical remediation text), then ranks with a combined score — not raw vector similarity alone.

```
score = w1·vector_similarity
      + w2·structural_match_fraction   (service/region/version/topology exact-match count)
      + w3·historical_success_rate     (from Trust System, §25)
      − w4·staleness_penalty           (time since last verified use)
```

Example: a candidate at 0.91 vector similarity with identical service/region/DB-version/topology and a 3/3 historical success rate should outrank a candidate at 0.94 raw similarity with none of those structural matches and a 1/1 record. Pure vector similarity is not sufficient for operational reasoning — this weighted, explainable scoring function is what the demo needs to visibly justify.

Retrieval is implemented as a single CockroachDB query combining a `VECTOR` distance operator with standard `WHERE`/`JOIN` predicates in one round trip (see §20), rather than a separate vector database plus a separate SQL database that must be kept in sync — this is the concrete technical reason CockroachDB's unified vector + relational support matters here.

---

## 12. Temporal Reasoning Engine

Answers: *"Was this fix valid then, and is it valid now?"* Compares historical state vs. current state across software versions, database versions, topology, infra configuration, permissions, dependencies, traffic profile, deployment architecture, resource identifiers, region, and configuration values.

```json
{
  "historical_fix": "reset_leaseholder",
  "historical_validity": true,
  "current_environment_match": 0.63,
  "dimension_diffs": [
    {"dimension": "topology", "match": false, "detail": "3-region → 5-region since 2026-02-11"},
    {"dimension": "db_version", "match": false, "detail": "v24.1 → v26.0"},
    {"dimension": "service_version", "match": true}
  ],
  "risk": "high",
  "recommendation": "do_not_execute",
  "reason": "Leaseholder rebalancing behavior changed materially between v24.1 and v26.0; historical command is not guaranteed safe under the new range-split defaults."
}
```

Each dimension diff is independently computed against structured snapshot data (§17), not inferred from free text — the LLM's job is to *synthesize the recommendation and explanation* from a deterministic diff, not to eyeball whether two JSON blobs look similar. This keeps the highest-stakes decision in the loop grounded in verifiable data rather than model intuition.

---

## 13. Validation Agent — Hierarchy

```
Historical evidence
     ↓
Current-state compatibility (Temporal Reasoning output)
     ↓
Policy check (deterministic rules engine, not LLM)
     ↓
Risk assessment → tier L0–L5 (§15)
     ↓
Sandbox validation (ephemeral ccloud cluster, real command dry-run)
     ↓
Human approval if tier requires it
     ↓
Production execution
```

The system never treats an LLM's stated confidence as sufficient authorization on its own — the policy check step is a deterministic rules engine over structured fields (`risk_tier`, `blast_radius`, `resource_class`), and an LLM cannot talk its way past it.

---

## 14. Execution Agent — Saga Pattern

Remediation often spans multiple systems (e.g., "drain traffic in ALB, then restart ECS task, then rebalance CockroachDB leaseholders"). GhostOps models multi-step remediation as a **saga**: each step has a defined **compensating action**, and the Execution agent persists saga state to CockroachDB *before* each step so a crash mid-remediation is recoverable rather than leaving infrastructure half-changed.

```
Step 1: drain_alb_target(target)       compensate: undrain_alb_target(target)
Step 2: restart_ecs_task(task_id)      compensate: none (idempotent, safe to leave)
Step 3: rebalance_leaseholders(range)  compensate: revert_lease_preferences(range)
```

If Verification (§16) fails after Step 3, the Execution agent walks the compensating actions in reverse order and marks the remediation `rolled_back`, not `failed` — this distinction matters for the Trust System, since a clean rollback is a different signal than an unrecoverable failure.

Tools available: CockroachDB (`ccloud CLI`, Managed MCP Server, Agent Skills), AWS (Lambda, ECS/EKS, SSM Run Command, CloudWatch, Config, CloudTrail, EventBridge), and optionally Kubernetes, Terraform, and CI providers behind the same saga/idempotency wrapper.

---

## 15. Safety Model

| Risk | Example | Policy |
|---|---|---|
| L0 | Read logs | Automatic |
| L1 | Query state | Automatic |
| L2 | Restart service | Policy-based (auto if trust score > threshold, else human) |
| L3 | Change configuration | Human approval required |
| L4 | Production database modification | Mandatory approval + second reviewer if blast radius > N services |
| L5 | Destructive action | Mandatory approval + explicit typed confirmation + sandbox proof required |

Every action carries: `action_id`, `actor`, `agent`, `timestamp`, `target`, `risk_level`, `reason`, `authorization`, `idempotency_key`, `saga_id`, `result`, `verification_id`. This ledger is append-only (§26) and is itself part of the memory the Investigator can retrieve against — "has this agent been reliable before" is a first-class retrieval signal.

---

## 16. Verification Agent

Execution success is not resolution. GhostOps independently verifies across **infrastructure** (did the intended state change, checked via a fresh Config/CloudTrail read, not the Execution agent's own claim), **application** (did errors decrease, via CloudWatch metrics), **performance** (did latency recover, via CloudWatch/X-Ray), **reliability** (did the incident recur within an observation window), **side effects** (did another service degrade — cross-service SLO check via a dependency graph), and **persistence** (did the fix hold for a defined window, e.g. 30 minutes, before being marked `verified` vs. `provisionally_successful`).

Using a *separate* signal source than the one Execution used to report success is deliberate — it prevents the system from grading its own homework.

---

## 17. Ghost Replay (Flagship Feature)

User selects `Replay Incident #1847`. GhostOps reconstructs the original incident, infra state, diagnosis, actions, and successful remediation, then asks: **would this work today?**

```
Historical remediation succeeded under CockroachDB v24.x with a 3-region
topology. Current environment runs v26.x with different leaseholder
defaults. 8 of 9 relevant dimensions match; the leaseholder-behavior
dimension does not. Sandbox validation on an ephemeral ccloud cluster
running the current schema/version confirms the original command produces
a different (unsafe) range-split pattern. The original command is
therefore rejected.
```

This is the clearest demonstration that GhostOps has *temporal* operational memory, not just search. **The demo should deliberately include one replay that is rejected**, not just successful ones — a system that always says "yes, replay it" hasn't actually demonstrated temporal reasoning.

---

## 18. Learning System

Every action becomes training data for future ranking, not future fine-tuning (no model weights are updated — this is retrieval-and-policy learning, which is faster, auditable, and doesn't require a training pipeline for a hackathon timeline).

```json
{
  "recommendation": "restart_service",
  "confidence": 0.82,
  "human_decision": "approved",
  "result": "failed",
  "root_cause": "database_connection_exhaustion",
  "outcome": "negative",
  "trust_delta": -0.04
}
```

Future recommendation ranking incorporates `trust_delta` directly (§11, §25) — this is a closed-loop system, and the write path (Verification → CockroachDB) and the read path (Investigator's ranking query) touch the *same* table, so the loop closes within a single database rather than requiring an ETL step.

---

## 19. CockroachDB Design — Why It's Load-Bearing, Not Bolted On

GhostOps has transactional memory, vector memory, temporal memory, operational history, agent state, and execution state. CockroachDB lets these coexist as **one consistent system of record**, and this PRD leans on four specific, concrete Cockroach capabilities rather than treating it as "Postgres with a vector column":

1. **Native `VECTOR` type + distributed vector indexing (CSPANN)** — incident, log, and remediation embeddings live in the same row as their structured metadata, so retrieval is a single query, not an application-layer join between a vector DB and a relational DB that can drift out of sync.
2. **Changefeeds (CDC)** — every write to `incidents`, `actions`, and `verification_results` emits a change event consumed by a lightweight memory-propagation service that updates trust scores and cached rankings in near-real-time, without polling.
3. **Managed MCP Server** — read-only by default, audit-logged, scoped per-agent — this is the actual tool interface the Investigator and Historian use, not a hand-rolled DB client.
4. **ccloud CLI + Agent Skills** — used both for cluster inspection/diagnostics *of GhostOps's own database* and, critically, for provisioning the **ephemeral sandbox cluster** used in Validation (§13) — a distinctive use of the product that a generic Postgres deployment could not replicate as cleanly.
5. **Multi-region survivability** — the `incidents` and `actions` tables are configured with `REGIONAL BY ROW` survival goals, so GhostOps's own memory survives the same class of regional failure it's designed to help *other* systems recover from — a nice, honest bit of dogfooding for the demo narrative.

**The key architectural claim, stated explicitly for judges:** the agent should not have one database for state, another vector store for memory, another system for history, and another for transactional outcomes. Its operational memory should remain a single consistent system of record — because a memory system that is itself fragmented across four data stores has recreated the exact problem (fragmented institutional knowledge) that GhostOps exists to solve.

---

## 20. Database Schema (Representative DDL)

```sql
CREATE TABLE incidents (
    incident_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    severity         STRING NOT NULL,
    service          STRING NOT NULL,
    region           STRING NOT NULL,
    start_time       TIMESTAMPTZ NOT NULL,
    end_time         TIMESTAMPTZ,
    root_cause       STRING,
    status           STRING NOT NULL DEFAULT 'open',
    environment      JSONB NOT NULL,        -- structured infra fingerprint
    summary_embedding VECTOR(1536),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    INDEX idx_incidents_service_region (service, region),
    VECTOR INDEX idx_incidents_embedding (summary_embedding)
) LOCALITY REGIONAL BY ROW;

CREATE TABLE infrastructure_snapshots (
    snapshot_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id   UUID REFERENCES incidents(incident_id),
    captured_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    db_version    STRING,
    topology      JSONB,
    config        JSONB,
    dependency_graph JSONB
);

CREATE TABLE actions (
    action_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id       UUID REFERENCES incidents(incident_id),
    saga_id            UUID,
    actor              STRING,             -- 'human' | agent name
    command            STRING,
    tool               STRING,
    target             STRING,
    risk_level         STRING NOT NULL,
    idempotency_key     STRING NOT NULL UNIQUE,
    result              STRING,             -- success | failed | rolled_back
    timestamp           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE remediations (
    remediation_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id          UUID REFERENCES incidents(incident_id),
    action_id            UUID REFERENCES actions(action_id),
    root_cause            STRING,
    success                BOOL,
    confidence             FLOAT,
    verification_status     STRING,
    trust_delta              FLOAT
);

CREATE TABLE memory_embeddings (
    memory_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id    UUID REFERENCES incidents(incident_id),
    memory_type     STRING,     -- 'symptom' | 'root_cause' | 'remediation' | 'reasoning'
    content          STRING,
    embedding         VECTOR(1536),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    VECTOR INDEX idx_memory_embedding (embedding)
);

CREATE TABLE agent_decisions (
    decision_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id      UUID REFERENCES incidents(incident_id),
    agent             STRING NOT NULL,
    input_summary      STRING,
    output_json          JSONB,
    confidence            FLOAT,
    disagreement_flag      BOOL DEFAULT false,
    timestamp               TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Changefeed powering near-real-time trust-score propagation
CREATE CHANGEFEED FOR TABLE remediations
  INTO 'kafka://memory-bus/remediation-outcomes'
  WITH updated, resolved = '10s';
```

Core entities beyond the above: `services`, `resources`, `root_causes`, `validation_runs`, `execution_runs`, `verification_results`, `policies`, `agent_trust_scores`, `human_feedback` — each following the same immutable-ledger pattern (append rows, never mutate history; corrections are new rows with a `supersedes` pointer).

---

## 21. AWS Architecture

| AWS Service | Purpose |
|---|---|
| Amazon Bedrock | Multi-tier model inference (fast classification tier + reasoning tier) |
| AWS Lambda | Event processing, agent step functions, tool-call handlers |
| Amazon EventBridge | Event routing from CloudWatch/CloudTrail/Config to Sentinel |
| CloudWatch | Telemetry, incident detection, verification signal source |
| CloudTrail | Infra/API activity, independent verification signal |
| AWS Config | Configuration state, temporal-diff source of truth |
| S3 | Long-term raw incident artifacts (immutable, versioned bucket) |
| ECS/EKS | Persistent GhostOps agent services |
| Step Functions | Saga orchestration for multi-step remediation |
| IAM | Least-privilege, per-agent scoped roles (read-only vs. execution roles are physically separate roles, not a flag) |
| Secrets Manager | Credential isolation — never embedded in prompts or memory |
| X-Ray / OpenTelemetry | Distributed tracing across the agent graph itself |

This gives AWS a genuine architectural role — Step Functions specifically implements the saga pattern from §14, and Config/CloudTrail are the actual data sources for the Temporal Reasoning diff, not decorative integrations.

---

## 22. Bedrock / Model Architecture

```
LLM (reasoning tier)
   ↓ structured tool_use request
Policy engine (deterministic)
   ↓
Permission validation (per-agent IAM role)
   ↓
Tool execution (idempotent, saga-wrapped)
   ↓
Result (structured, typed)
   ↓
LLM (next reasoning step)
```

The model never directly holds unrestricted infrastructure credentials — every tool call is proxied through the MCP server / Lambda handler, which enforces the actual IAM boundary. Extended/step-by-step reasoning is enabled specifically for the Reasoning and Validation agents, since those are the steps where an unexamined leap in logic has production consequences; the fast-tier classification model does not use extended reasoning, since latency matters more than depth for triage.

---

## 23. Agent Memory vs. Bedrock Session Memory

Do not confuse the two. Bedrock's own agent memory mechanisms are for **conversational/session continuity** — remembering what was said three turns ago in a single investigation session. GhostOps's **operational memory** — incident history, infra state, actions, outcomes, embeddings, policies, agent trust — lives entirely in CockroachDB and persists across sessions, users, and even model changes. This separation is a genuine design decision, not an afterthought, because it means swapping the underlying LLM (or model provider) does not lose a single byte of institutional memory — the memory layer and the reasoning layer are decoupled by design.

---

## 24. Frontend

Five primary screens: **Dashboard** (active incidents, agent status), **Incident Investigation** (live view of the retrieval/reasoning graph as it runs, including a visible disagreement indicator when sub-agents don't converge), **Memory Graph** (current incident → similar past incidents → root cause / failed action / successful fix / infra state, rendered as an actual graph, not a list), **Remediation** (recommended action, confidence, historical use/success/fail counts, current-environment match %, risk tier, validation status, approve/execute), **Ghost Replay** (original vs. current environment diff, compatibility %, replay verdict — including the deliberately-rejected example from §17).

A sixth screen is added in this revision: **Agent Trace** — a real-time view of the ReAct loop (Thought → Tool → Observation → Self-Critique) for the currently active sub-agent, because for a hackathon judged partly on "agentic memory design," *showing the reasoning process itself*, not just its output, is the single highest-leverage UI addition.

---

## 25. Trust System

```
Remediation: restart_auth_service
Historical executions: 42   Success: 39   Failure: 3
Success rate: 92.8%          Human override rate: 4%
Current confidence: 89%  (weighted by recency + environment match)
```

This distinguishes *"the LLM thinks this is correct"* from *"this procedure has empirically worked 39 of 42 times, weighted toward the more recent and more environmentally-similar successes."* Trust scores decay over time (via CockroachDB row-level TTL-adjacent scheduled recompute) so a remediation that hasn't been validated against a current environment in 12 months is flagged `stale` even if its historical record is perfect.

---

## 26. Agent Decision Ledger

```
DECISION #9842
Agent: Investigator
Input: P1 latency incident
Historical matches: 7   Selected precedent: #1847
Reason: same service, same database, same topology, same failure signature
Confidence: 0.91
Disagreement flag: false
Timestamp: ...
```

Append-only, queryable, and itself part of retrieval — "how has the Investigator performed historically" is a legitimate query against this table, closing the loop between agent behavior and agent trust (§9.1, §25).

---

## 27. Failure Handling

Historical memory unavailable → fall back to live diagnosis. Vector search unavailable → structured retrieval only, flagged as degraded-mode in the UI. Agent disagreement (confidence spread > threshold, or explicit `disagreement_flag`) → escalate to human, do not silently pick one. Validation fails → do not execute, full stop. Execution fails mid-saga → walk compensating actions (§14). Verification fails → mark remediation `unsuccessful`, feed negative trust delta. Historical fix becomes obsolete (per Temporal Reasoning) → downgrade its trust score and mark `requires_revalidation`, don't delete it — a fix that stopped working is itself useful memory. Infrastructure changes after validation but before execution → mandatory revalidation, enforced by comparing a fresh Config snapshot hash against the one Validation ran against.

---

## 28. Observability

`incident_detection_latency`, `memory_retrieval_latency`, `historical_match_accuracy`, `recommendation_accuracy`, `validation_success_rate`, `execution_success_rate`, `verification_success_rate`, `human_override_rate`, `false_positive_rate`, `false_remediation_rate`, `agent_disagreement_rate` (new), `saga_rollback_rate` (new), `MTTR_before`, `MTTR_after`.

**Headline metric:** reduction in MTTR from historical-memory-assisted remediation, measured against the golden dataset (§9.5) as well as the live demo scenario.

---

## 29. Security

Least-privilege IAM with **physically separate read and write roles** (not a permission flag on one role); action-level authorization; append-only audit logs; human approval for L3+ operations; secrets stored in Secrets Manager, never in prompts or memory embeddings; sanitized incident logs before embedding generation (PII/secret scrubbing pass); command allowlists/denylists enforced at the tool-schema level, not just the prompt level; environment isolation between the sandbox (ephemeral ccloud cluster) and production; sandbox validation required before any L3+ action; **prompt-injection defenses** (§9.4) as a first-class security control, not an afterthought, since this system's threat model explicitly includes adversarial log/ticket content reaching an execution-capable agent.

---

## 30. Demo Scenario (3 minutes)

**0:00–0:30** — Inject a real failure (auth service → DB connection exhaustion → latency spike → P1). Sentinel detects it deterministically (no LLM in the detection path — faster and more reliable).

**0:30–1:10** — Investigator surfaces 3 historical incidents with the weighted-score breakdown visible on screen (not just a similarity %), showing why Incident #1847 outranks a higher-raw-similarity but structurally-mismatched candidate.

**1:10–1:40** — Historian reconstructs #1847: 2 failed attempts, 1 successful — shown with the raw evidence, not just the LLM summary, to visibly demonstrate the §10 separation principle.

**1:40–2:10** — Temporal Reasoning compares historical vs. current environment, dimension by dimension, and Validation runs the sandbox check. Show the confidence number moving as each dimension resolves.

**2:10–2:35** — Execution runs the saga; show the Agent Trace screen live (§24) so judges see the actual ReAct loop, not a black box. Metrics visibly recover (latency 2.8s → 120ms, error rate 17% → 0.4%).

**2:35–3:00** — CockroachDB write-back, trust score updates live via the changefeed (§19.2) — this is the moment to show the changefeed-driven dashboard update happening with no polling. Close with a **Ghost Replay that returns `DO NOT REPLAY`** on a *different* historical incident — proving the system says no when it should, which is more convincing than another success.

---

## 31. Competitive Differentiation

| Typical tool | GhostOps |
|---|---|
| Stores incidents | Stores operational experience |
| Summarizes incidents | Reconstructs them from separated raw evidence |
| Searches runbooks | Searches actual historical actions, weighted by structural + empirical fit |
| Retrieves documents | Retrieves state + actions + outcomes in one query |
| Gives recommendations | Validates recommendations against a live sandbox |
| Executes commands | Executes governed, saga-wrapped, idempotent actions |
| Logs execution | Learns from execution via closed-loop trust scoring |
| Static runbook | Evolving executable memory that can say "no longer valid" |
| Current-state monitoring | Temporal reasoning across infra generations |
| Human knowledge | Machine-preserved, continuously re-validated institutional knowledge |
| Single LLM call | Multi-agent graph with self-critique and disagreement escalation |

---

## 32. Hackathon Criteria Mapping

| Judging criterion | GhostOps implementation |
|---|---|
| Agentic Memory Design | Incident + state + timeline + commands + outcomes + embeddings + temporal reasoning + trust-weighted retrieval |
| Technical Implementation | Native VECTOR type + CSPANN indexing, changefeed-driven propagation, MCP + ccloud sandbox + Agent Skills, saga-based execution, multi-tier Bedrock routing |
| Real-World Impact | MTTR reduction, institutional knowledge preservation, honest "no longer applicable" verdicts (reduces bad-replay risk) |
| Production Readiness | RBAC with physically separate roles, idempotency, saga rollback, independent verification, regression-gated agent evaluation |
| Creativity | Ghost Replay with a deliberately-rejected case; live Agent Trace UI; trust score as a first-class, decaying, retrievable signal |

---

## 33. MVP Scope

**P0:** CockroachDB memory + native vector search, incident ingestion, historical retrieval (hybrid scoring), Bedrock multi-tier reasoning, infra snapshots, remediation extraction, validation, saga-based execution, independent verification, agent decision ledger, human approval, dashboard + Agent Trace.

**P1 (treated as in-scope, not optional):** Ghost Replay, trust scores, full multi-agent graph with disagreement escalation, ccloud sandbox validation, Agent Skills, MCP, temporal compatibility engine, changefeed-driven propagation.

**P2:** autonomous remediation policies (auto-execute below a trust threshold without human gate), multi-region deployment, predictive incident detection, remediation generalization across services, automated runbook synthesis, cross-service causal reasoning, prompt/agent regression CI pipeline as a standing service.

---

## 34. The Product's Killer Insight

A production incident is not merely an event — it is an expensive experiment conducted by an organization. An engineer tried something; it failed; they tried something else; it worked. That sequence contains operational knowledge. Most systems throw most of that knowledge away. GhostOps captures it, keeps the raw evidence separate from the interpretation, validates the interpretation against a live sandbox before trusting it, re-validates it against the *current* infrastructure every time it's about to be reused, and is honest — visibly, in the demo — about the times it should say no.

**Submission positioning — avoid:** "An AI-powered DevOps assistant."

**Use instead:** *GhostOps is an autonomous institutional memory system for production infrastructure. It observes how engineers solve incidents, preserves the exact state, reasoning, actions, and outcomes in CockroachDB, and uses that memory — continuously re-validated against the present — to decide when to act and when to refuse.*

**Short pitch:** Your best SRE already solved the problem. GhostOps remembers exactly how — and knows when that answer has expired.
