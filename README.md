# GhostOps 👻⚡

> **"The production memory that survives the engineer."**

GhostOps is an autonomous institutional memory and remediation system for production infrastructure.

---

## Architecture & Implementation Progress

GhostOps is built through 10 sequential implementation stages. **All 10 stages are COMPLETE.** Stage 10 establishes the final production-hardening, reliability, security, observability, and system polish layer, transforming GhostOps into a production-oriented, observable, secure, failure-tolerant, and auditable system.

### Monorepo Structure

```
ghostops/
│
├── apps/
│   ├── api/             # FastAPI backend & multi-agent orchestration engine
│   │   ├── app/
│   │   │   ├── api/     # API v1 routes (health, ready, live, metrics, incidents, memory, plans, execution, learning, replay, sentinel, traces)
│   │   │   ├── core/    # Config, structured logging, errors, RBAC auth, idempotency, circuit breakers, retries, metrics
│   │   │   ├── db/      # SQLAlchemy 2.x CockroachDB models & session
│   │   │   ├── domain/  # Core domain models
│   │   │   ├── agents/  # Model provider interfaces & LangGraph multi-agent orchestrator
│   │   │   ├── tools/   # Base tool registry & execution metadata
│   │   │   ├── services/# Search, governance, saga execution, learning, ghost replay, sentinel & recovery services
│   │   │   ├── integrations/# AWS mock & live adapters
│   │   │   ├── schemas/ # Pydantic v2 schemas
│   │   │   └── main.py
│   │   └── tests/       # Pytest test suite (74 test cases covering Stages 1-10)
│   │
│   └── web/             # Next.js 14 frontend dashboard (TypeScript + Tailwind)
│       ├── app/
│       ├── components/  # Incident detail, investigation trace, governance, saga execution, learning, ghost replay, sentinel & production dashboard components
│       ├── lib/
│       ├── types/
│       └── package.json
│
├── packages/
│   └── shared/          # Shared domain schemas & enums
│
├── infra/
│   ├── docker/          # Dockerfile.api and Dockerfile.web
│   ├── cockroach/       # Init scripts & vector extension config
│   └── aws/             # Mock telemetry & snapshot JSON data
│
├── migrations/          # Alembic database migrations
├── scripts/             # Database initialization & seed scripts
├── docs/                # Architecture, operations, security, recovery, api & production-readiness docs
├── docker-compose.yml   # Multi-container local execution
├── Makefile             # CLI commands
└── README.md
```

---

## Quickstart & Local Execution

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker & Docker Compose (optional for local DB)

### 1. Environment Setup
```bash
cp .env.example .env
```

### 2. Local Backend Run
```bash
# Install shared package & API dependencies
pip install -e packages/shared
pip install -e apps/api

# Initialize database schema & seed mock data
$env:DATABASE_URL="sqlite:///./ghostops_local.db"; python scripts/seed_db.py

# Start FastAPI API Server
make api
```
Access the interactive OpenAPI Swagger documentation at: `http://localhost:8000/docs`

### 3. Local Web Dashboard Run
```bash
cd apps/web
npm install
npm run dev
```
Access the GhostOps Web Dashboard at: `http://localhost:3000`

---

## 10-Stage Implementation Roadmap

1. **Stage 1: Foundation & Architecture** (COMPLETE)
2. **Stage 2: Telemetry Ingestion & Evidence Baseline** (COMPLETE)
3. **Stage 3: Historical Retrieval Engine** (COMPLETE)
4. **Stage 4: Agentic Investigation Engine** (COMPLETE)
5. **Stage 5: Governed Planning & Safety Engine** (COMPLETE)
6. **Stage 6: Saga Execution & Compensation Engine** (COMPLETE)
7. **Stage 7: Learning & Memory Consolidation Engine** (COMPLETE)
8. **Stage 8: Ghost Replay & Simulation Engine** (COMPLETE)
9. **Stage 9: Continuous Autonomous Sentinel** (COMPLETE)
10. **Stage 10: Production Hardening, Reliability, Security & System Polish** (COMPLETE)
