-- ============================================================================
-- GhostOps v3.0 Database Schema for CockroachDB Cloud
-- Includes native VECTOR types, CSPANN distributed vector indexes,
-- REGIONAL BY ROW locality, and Changefeeds (CDC)
-- ============================================================================

CREATE DATABASE IF NOT EXISTS ghostops;
USE ghostops;

-- 1. INCIDENTS (System of record & operational entrypoint)
CREATE TABLE IF NOT EXISTS incidents (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title            STRING NOT NULL,
    description      STRING NOT NULL,
    severity         STRING NOT NULL,
    status           STRING NOT NULL DEFAULT 'OPEN',
    service          STRING NOT NULL,
    region           STRING NOT NULL,
    start_time       TIMESTAMPTZ NOT NULL,
    end_time         TIMESTAMPTZ,
    target_resource_id STRING,
    root_cause_summary STRING,
    resolution_summary STRING,
    memory_status    STRING NOT NULL DEFAULT 'COMPLETED',
    environment_fingerprint JSONB NOT NULL DEFAULT '{}'::JSONB,
    summary_embedding VECTOR(1536),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    INDEX idx_incidents_service_region (service, region)
);

-- Note: In multi-region CockroachDB clusters, tables can be partitioned by locality:
-- ALTER TABLE incidents ADD COLUMN crdb_region crdb_internal_region AS (CASE WHEN region = 'eu-west-1' THEN 'eu-west-1' ELSE 'us-east-1' END) STORED;
-- ALTER TABLE incidents SET LOCALITY REGIONAL BY ROW AS crdb_region;

-- 2. INFRASTRUCTURE SNAPSHOTS (Immutable temporal state fingerprints)
CREATE TABLE IF NOT EXISTS infrastructure_snapshots (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id        UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    snapshot_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    db_version         STRING NOT NULL DEFAULT 'CockroachDB v24.1.0',
    service_version    STRING NOT NULL DEFAULT 'v4.2.0',
    topology           JSONB NOT NULL DEFAULT '{}'::JSONB,
    configuration      JSONB NOT NULL DEFAULT '{}'::JSONB,
    dependencies       JSONB NOT NULL DEFAULT '{}'::JSONB,
    resource_identifiers JSONB NOT NULL DEFAULT '[]'::JSONB,
    region             STRING NOT NULL DEFAULT 'us-east-1',
    traffic_info       JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    INDEX idx_infra_snapshots_incident (incident_id)
);

-- 3. OPERATIONAL ACTIONS (Governed, idempotent execution audit ledger)
CREATE TABLE IF NOT EXISTS operational_actions (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id        UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    saga_id            STRING,
    actor              STRING NOT NULL DEFAULT 'GhostOps.SagaEngine',
    agent              STRING NOT NULL DEFAULT 'ExecutionAgent',
    command            STRING NOT NULL,
    tool               STRING NOT NULL,
    target             STRING NOT NULL,
    risk_level         STRING NOT NULL DEFAULT 'LOW',
    reason             STRING NOT NULL,
    authorization      STRING NOT NULL DEFAULT 'SystemAutoApproved',
    idempotency_key    STRING NOT NULL UNIQUE,
    result             STRING NOT NULL, -- SUCCESS | FAILED | ROLLED_BACK
    error_message      STRING,
    timestamp          TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    INDEX idx_actions_incident (incident_id),
    INDEX idx_actions_saga (saga_id)
);

-- 4. INSTITUTIONAL MEMORY VECTORS (Semantic knowledge embeddings)
CREATE TABLE IF NOT EXISTS institutional_memory_vectors (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title              STRING NOT NULL,
    content            STRING NOT NULL,
    redacted_content   STRING,
    memory_type        STRING NOT NULL DEFAULT 'remediation', -- symptom | root_cause | remediation | reasoning
    entity_type        STRING,
    entity_id          STRING,
    incident_id        STRING,
    source_execution_id STRING,
    evidence_references JSONB NOT NULL DEFAULT '[]'::JSONB,
    embedding          VECTOR(1536) NOT NULL,
    metadata_json      JSONB NOT NULL DEFAULT '{}'::JSONB,
    trust_level        STRING NOT NULL DEFAULT 'MEDIUM',
    confidence         FLOAT8 NOT NULL DEFAULT 0.75,
    memory_status      STRING NOT NULL DEFAULT 'ACTIVE',
    usage_count        INT8 NOT NULL DEFAULT 0,
    successful_usage_count INT8 NOT NULL DEFAULT 0,
    failed_usage_count INT8 NOT NULL DEFAULT 0,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    INDEX idx_memory_incident (incident_id),
    INDEX idx_memory_type (memory_type)
);

-- 5. REMEDIATION OUTCOMES & TRUST DELTAS
CREATE TABLE IF NOT EXISTS remediation_outcomes (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id        UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    plan_id            STRING NOT NULL,
    execution_id       STRING NOT NULL,
    execution_status   STRING NOT NULL,
    verification_status STRING NOT NULL,
    incident_recovery_status STRING NOT NULL,
    outcome_classification STRING NOT NULL,
    effectiveness_score FLOAT8 NOT NULL DEFAULT 0.0,
    duration_seconds   FLOAT8 NOT NULL DEFAULT 0.0,
    executed_steps_count INT8 NOT NULL DEFAULT 0,
    failed_steps_count INT8 NOT NULL DEFAULT 0,
    compensated_steps_count INT8 NOT NULL DEFAULT 0,
    rollback_performed BOOL NOT NULL DEFAULT false,
    rollback_successful BOOL NOT NULL DEFAULT false,
    confidence         FLOAT8 NOT NULL DEFAULT 0.75,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    INDEX idx_outcomes_incident (incident_id)
);

-- 6. AGENT DECISIONS LEDGER (Append-only ReAct decision traces)
CREATE TABLE IF NOT EXISTS agent_decisions (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id        UUID REFERENCES incidents(id) ON DELETE SET NULL,
    agent              STRING NOT NULL,
    input_summary      STRING NOT NULL,
    output_json        JSONB NOT NULL DEFAULT '{}'::JSONB,
    confidence         FLOAT8 NOT NULL DEFAULT 0.75,
    disagreement_flag  BOOL NOT NULL DEFAULT false,
    timestamp          TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    INDEX idx_decisions_agent (agent),
    INDEX idx_decisions_incident (incident_id)
);

-- 7. CHANGEFEED CONFIGURATION (Real-Time Memory Bus)
-- Emits live events upon remediation completion to recompute trust scores
-- CREATE CHANGEFEED FOR TABLE remediation_outcomes INTO 'kafka://memory-bus/remediation-outcomes' WITH updated, resolved = '10s';
