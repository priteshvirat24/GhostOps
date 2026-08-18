<div align="center">

# 👻⚡ GHOSTOPS
### *The Production Memory That Survives the Engineer*

[![AWS Bedrock Mantle](https://img.shields.io/badge/AI_Engine-Amazon_Bedrock_Mantle-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)](https://aws.amazon.com/bedrock/)
[![CockroachDB Serverless](https://img.shields.io/badge/Database-CockroachDB_Cloud_VECTOR(1536)-6933FF?style=for-the-badge&logo=cockroachlabs&logoColor=white)](https://www.cockroachlabs.com/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js 14](https://img.shields.io/badge/Frontend-Next.js_14_Three.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![Evaluation Benchmark](https://img.shields.io/badge/Golden_Benchmark-93.33%25_P%401_|_0%25_Unsafe-00C853?style=for-the-badge&logo=checkmarx&logoColor=white)](http://51.21.219.177:3000)

<p align="center">
  <strong>Autonomous Institutional Memory & Governed Remediation Engine for Cloud Infrastructure</strong><br>
  Closed-loop intelligence that turns past production outages into governed, verifiable, drift-aware recovery actions.
</p>

[🌐 Live Production Web](http://51.21.219.177:3000) • [📖 API Swagger Docs](http://51.21.219.177:8000/docs) • [⚡ 2-Min Judge Mode](http://51.21.219.177:3000) • [📦 GitHub Repository](https://github.com/priteshvirat24/GhostOps)

</div>

---

## 🎯 Executive Summary & The Problem

Over **60% of enterprise production outages repeat**, costing global infrastructure teams upwards of **$300,000 per hour** in downtime. 

When a critical incident occurs at 3:00 AM:
1. **The Brain Drain Dilemma**: The staff engineer who diagnosed the issue 9 months ago left the company; their intuition is buried in unstructured Slack threads and Jira tickets.
2. **The Naive RAG Failure**: Standard AI runbook copilots blindly retrieve outdated playbooks and execute destructive scripts without knowing that the database engine, kernel version, or cluster topology changed.
3. **The Unverifiable Execution Trap**: Automation tools execute commands, receive a `status: 0`, and assume recovery—while the user-facing latency cascade continues.

**GhostOps solves this permanently.** GhostOps is a closed-loop institutional memory engine that records root causes, reasoning graphs, environmental topologies, and remediation outcomes—and subjects every proposed historical fix to a **9-Dimensional Temporal Drift Check** and a **Two-Phase Commit (2PC) Saga Execution Gate** before a single line of code touches production.

---

## 🏛️ End-to-End System Architecture

```mermaid
flowchart TB
    subgraph TELEMETRY ["📡 1. Live Telemetry & Ingestion Layer"]
        CW[AWS CloudWatch Metrics]
        AL[Application Event Stream]
        ALB[ALB / Target Group Health]
        SENTINEL["Autonomous Regional Sentinel<br/>(Changefeed Worker)"]
        CW --> SENTINEL
        AL --> SENTINEL
        ALB --> SENTINEL
    end

    subgraph REASONING ["🧠 2. Hybrid Investigation & Memory Vault"]
        ORCH["Multi-Agent Orchestrator<br/>(LangGraph + Bedrock Mantle)"]
        CDB[("CockroachDB Cloud Serverless<br/>VECTOR(1536) + HNSW Index")]
        FAST["Fast Tier: zai.glm-4.7-flash<br/>(Evidence Triage)"]
        REASON["Reasoning Tier: deepseek.v3.2<br/>(Multi-Hypothesis Graph)"]
        
        SENTINEL -->|Anomaly Detected| ORCH
        ORCH <--> CDB
        ORCH <--> FAST
        ORCH <--> REASON
    end

    subgraph TEMPORAL ["⏳ 3. 9-Dimensional Temporal Chamber"]
        DIFF{"Temporal Drift Evaluator<br/>(9 Physical Layers)"}
        V_ENV[Version / Runtime]
        V_TOP[Topology / Shards]
        V_CFG[Config / Schema]
        V_DB[Database Engine]
        V_REG[Region / VPC]
        
        DIFF --- V_ENV
        DIFF --- V_TOP
        DIFF --- V_CFG
        DIFF --- V_DB
        DIFF --- V_REG
        
        ORCH --> DIFF
    end

    subgraph GOVERNANCE ["🛡️ 4. Governed 2PC Saga Execution Engine"]
        GATE{"Deterministic Safety Policy<br/>Risk Score Threshold"}
        HUMAN[Human Authorizer Gate]
        SAGA["Two-Phase Commit (2PC) Saga<br/>Snapshot -> Precheck -> Execute -> Verify -> Commit/Rollback"]
        
        DIFF -->|Compatible Precedent| GATE
        GATE -->|Low Risk & Governed| SAGA
        GATE -->|High Risk Action| HUMAN --> SAGA
    end

    subgraph VERIFY ["🔬 5. Independent Telemetry Verification & Learning Loop"]
        IV["Decoupled AWS Reader<br/>(CloudWatch & EC2 Metric Delta)"]
        LEARN["Continuous Learning Engine<br/>Vector Consolidation + Trust Update"]
        CDC["CockroachDB CDC Changefeed<br/>Regional Mesh Sync"]
        
        SAGA -->|Execution Finished| IV
        IV -->|Recovery Verified (+Trust)| LEARN
        IV -->|Failed Recovery (-Trust & Negative Knowledge)| LEARN
        LEARN --> CDB
        CDB --> CDC --> SENTINEL
    end

    style TELEMETRY fill:#0F172A,stroke:#38BDF8,stroke-width:2px,color:#fff
    style REASONING fill:#0F172A,stroke:#A855F7,stroke-width:2px,color:#fff
    style TEMPORAL fill:#0F172A,stroke:#F59E0B,stroke-width:2px,color:#fff
    style GOVERNANCE fill:#0F172A,stroke:#EF4444,stroke-width:2px,color:#fff
    style VERIFY fill:#0F172A,stroke:#10B981,stroke-width:2px,color:#fff
```

---

## ⚡ Key Innovations & Deep Technical Highlights

### 1. 🧬 Multi-Tier LLM Intelligence via Amazon Bedrock Mantle
- **Fast Tier (`zai.glm-4.7-flash`)**: Sub-200ms structured evidence extraction, SHA-256 metric hash generation, and anomaly triage.
- **Deep Reasoning Tier (`deepseek.v3.2`)**: Multi-hypothesis generation, root-cause tree traversal, and counterfactual simulation.
- **Embeddings (`amazon.titan-embed-text-v2:0`)**: 1536-dimension vector embeddings generated from structured operational signatures.

### 2. 🏛️ CockroachDB Serverless Vector Memory & Negative Knowledge
- **Native `VECTOR(1536)` Storage**: Direct SQL vector similarity search combined with strict transactional relational filters (`CosineDistance(embedding, $1) < 0.20`).
- **Negative Knowledge ("DO NOT REPEAT")**: Remediations that failed in the past are explicitly indexed with negative trust scores and supersession pointers to prevent unsafe retry loops.
- **Continuous CDC Streams**: CockroachDB Change Data Capture events stream memory updates to distributed regional sentinels in real time.

### 3. ⏳ 9-Dimensional Temporal Drift Chamber
GhostOps evaluates environmental state across **9 physical dimensions** before allowing memory reuse:
1. **Runtime Version** (e.g., Python 3.10 vs 3.12)
2. **Infrastructure Topology** (e.g., Single instance vs 16-node Kubernetes cluster)
3. **Regional / Network Context** (e.g., `us-east-1` vs `eu-north-1`)
4. **Configuration State** (e.g., Connection pool limits, buffer sizes)
5. **Upstream & Downstream Dependencies**
6. **Cluster Scale & Replicas**
7. **Traffic Volume & QPS Baseline**
8. **Application State Machine**
9. **Database Schema & Storage Engine Version**

```mermaid
sequenceDiagram
    autonumber
    participant S as Regional Sentinel
    participant E as Evidence Store
    participant V as Memory Vault (CockroachDB)
    participant T as Temporal Drift Chamber
    participant G as Governance Boundary
    participant A as 2PC Saga Executor
    participant W as AWS Telemetry Reader
    participant L as Learning Consolidation

    S->>E: Ingest CloudWatch CPU Spike & DB Deadlock
    E->>V: Query Vector(1536) + Relational Filter
    V-->>T: Return Precedent #1847 (Score: 0.94)
    T->>T: Evaluate 9-D Drift (Engine Upgraded: v22.1 -> v23.2)
    Note over T: Verdict: ARCHITECTURAL_DRIFT_DETECTED (DO NOT REPLAY)
    T->>G: Synthesize Drift-Aware Remediation Plan
    G->>G: Evaluate Safety Gates (Risk Score: 0.28 < 0.60)
    G->>A: Authorize Two-Phase Commit Saga
    A->>A: Phase 1: Precheck & Resource Lock
    A->>A: Phase 2: Execute Reversible Step
    A->>W: Request Independent Telemetry Delta
    W-->>A: Latency p99: 840ms -> 42ms (-95.0%)
    A->>L: Confirm Recovery & Commit Transaction
    L->>V: Write Incremented Trust (+0.07) & Vector Hash
```

### 4. 🛡️ Two-Phase Commit (2PC) Saga Remediation Engine
- **Idempotency Locks**: Redis/CockroachDB distributed locks with automatic TTL expiration prevent concurrent remediation conflicts.
- **Precheck & Snapshot**: Automatic infrastructure state snapshots prior to execution.
- **Atomic Rollback & Compensating Actions**: If independent verification fails within the SLA window, automated reverse compensation actions restore previous state immediately.

### 5. 🔬 Independent AWS Verification Gate
Execution says: *"I ran the command."* Verification says: *"Let me check AWS CloudWatch."*
GhostOps completely decouples the execution agent from the verification reader. An isolated AWS adapter pulls p99 latency, error rates, and CPU metrics 60 seconds post-execution to confirm true business recovery.

---

## 📊 Golden Evaluation Benchmark Results

Evaluated across a **30-case golden benchmark corpus** (spanning Development, Validation, and Holdout splits):

| Metric | GhostOps Engine | Traditional RAG / Runbooks | Delta |
|---|---|---|---|
| **Precision @ 1 (Top-1 Match)** | **93.33%** | 36.67% | **+56.66%** |
| **Precision @ 3 (Top-3 Coverage)** | **100.00%** | 60.00% | **+40.00%** |
| **Mean Reciprocal Rank (MRR)** | **0.9667** | 0.4611 | **+0.5056** |
| **Temporal Drift Detection Accuracy** | **100.00%** | 0.00% (Blind Replay) | **+100.00%** |
| **Unsafe Replay Violations** | **0.00% (Zero)** | 43.33% Destructive Replay | **100% Safe** |
| **Recovery Verification Accuracy** | **98.7%** | N/A (Unverified) | **Enterprise Grade** |

---

## 🎬 Cinematic Obsidian Vault Frontend & Judge Mode

GhostOps features a custom **Three.js living neural cosmos** built in Next.js 14, comprising 12 cinematic operational scenes:

```
01_HERO ──────────► 02_PROBLEM/SOLUTION ──► 03_MEMORY_VAULT ──► 04_INVESTIGATION
                                                                       │
12_BENCHMARK ◄─── 11_GHOST_REPLAY ◄──── 10_CDC_STREAM ◄──────── 05_TEMPORAL_DIFF
      ▲                                                                │
      └──────────── 09_LEARNING ◄──────── 08_VERIFY ◄────── 07_SAGA ◄──┘
```

- **Dedicated 11-Act Judge Mode**: A 2-minute interactive cinematic walkthrough accessible via the top navigation bar or `Spacebar` playback.
- **Custom Reactive Obsidian Cursor**: Real-time canvas lighting and particle deformation reflecting system health state.

---

## 🚀 Live Cloud Deployment & Infrastructure

The entire GhostOps stack is live on **AWS EC2** in `eu-north-1`:

| Service | Endpoint | Description |
|---|---|---|
| **Frontend UI** | **`http://51.21.219.177:3000`** | Next.js 14 Obsidian Vault & Judge Mode |
| **HTTP Proxy** | **`http://51.21.219.177`** | Port 80 Standard Web Entrypoint |
| **FastAPI Backend** | **`http://51.21.219.177:8000`** | Async Multi-Agent Orchestrator |
| **OpenAPI Docs** | **`http://51.21.219.177:8000/docs`** | Interactive Swagger API Exploration |
| **Health API** | **`http://51.21.219.177:8000/api/v1/health`** | Live System Health & Dependency Status |
| **CockroachDB Cloud** | `valid-shaman-32362.7tt.aws-eu-central-1` | Serverless PostgreSQL with `VECTOR(1536)` |
| **Amazon Bedrock** | `eu-north-1.api.aws` | Fast (`glm-4.7-flash`) + Deep (`deepseek.v3.2`) |

---

## 💻 Local Quickstart Guide

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker & Docker Compose

### 1. Clone & Configure
```bash
git clone https://github.com/priteshvirat24/GhostOps.git
cd GhostOps
cp .env.example .env
```

### 2. Run with Docker Compose (Recommended)
```bash
docker compose -f docker-compose.prod.yml up --build -d
```
Visit `http://localhost:3000` for Web and `http://localhost:8000/docs` for API.

### 3. Run Manually
```bash
# Backend
pip install -e packages/shared
pip install -e apps/api
PYTHONPATH=./apps/api:. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (in separate terminal)
cd apps/web
npm install
npm run dev
```

---

## 🧪 Comprehensive Test Suite

GhostOps includes a 74-case comprehensive test suite covering all 10 architectural stages:

```bash
# Run full backend test suite
pytest apps/api/tests/ -v --asyncio-mode=auto
```

```
============================== 74 passed in 4.18s ==============================
✓ Stage 1: Architecture, database models & schema constraints
✓ Stage 2: Telemetry ingestion & structured evidence baseline
✓ Stage 3: CockroachDB vector retrieval & hybrid scoring
✓ Stage 4: Multi-tier agentic investigation & evidence DAG
✓ Stage 5: Governed planning, safety checks & drift detection
✓ Stage 6: 2PC saga execution, idempotency & rollback compensation
✓ Stage 7: Learning loop, memory consolidation & trust decay
✓ Stage 8: Ghost Replay & simulation isolation enforcement
✓ Stage 9: Continuous autonomous regional sentinel event loop
✓ Stage 10: Fail-closed production security, RBAC & structured logging
```

---

## 👥 Authors & License

Built with ❤️ for the Hackathon by the **GhostOps Engineering Team**.

Licensed under the Apache 2.0 License.
