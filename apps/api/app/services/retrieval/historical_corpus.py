from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import hashlib
import json

class HistoricalMemoryRecord:
    def __init__(
        self,
        incident_id: str,
        title: str,
        description: str,
        service: str,
        region: str,
        severity: str,
        symptoms: List[str],
        root_cause: str,
        action_command: str,
        action_result: str, # SUCCESS | FAILED
        memory_type: str, # remediation | root_cause | negative | superseded | timeline
        trust_level: str, # HIGH | MEDIUM | LOW | VERIFIED_GOLD
        service_version: str = "v4.2.0",
        db_version: str = "CockroachDB v23.2.3",
        topology: Optional[Dict[str, Any]] = None,
        configuration: Optional[Dict[str, Any]] = None,
        superseded_by: Optional[str] = None,
        memory_status: str = "ACTIVE",
        days_ago: int = 30
    ):
        self.incident_id = incident_id
        self.title = title
        self.description = description
        self.service = service
        self.region = region
        self.severity = severity
        self.symptoms = symptoms
        self.root_cause = root_cause
        self.action_command = action_command
        self.action_result = action_result
        self.memory_type = memory_type
        self.trust_level = trust_level
        self.service_version = service_version
        self.db_version = db_version
        self.topology = topology or {"nodes": [f"{service}-1", f"{service}-2"]}
        self.configuration = configuration or {"connection_pool_max": 50}
        self.superseded_by = superseded_by
        self.memory_status = memory_status
        self.days_ago = days_ago

    def to_rich_content(self) -> str:
        symptom_str = ", ".join(self.symptoms)
        topo_str = f"nodes={len(self.topology.get('nodes', []))}"
        if self.topology.get("multi_region"):
            topo_str += ", multi_region=True"
        return (
            f"Historical Operational Incident on {self.service} ({self.region}): {self.title}. "
            f"Observed Symptoms: {symptom_str}. "
            f"Underlying Root Cause: {self.root_cause}. "
            f"Remediation Action Executed: {self.action_command} (Outcome: {self.action_result}). "
            f"Environment Context: Service Version {self.service_version}, Database {self.db_version}, Topology [{topo_str}]."
        )

class HistoricalCorpusRegistry:
    """
    Independent Historical Operational Memory Corpus (§9.5, §19.3).
    Corpus Version: ghostops-history-v1
    Contains 46 pre-existing historical operational memories across 7 services, 3 regions,
    4 database engines, successful remediations, failed attempts, negative knowledge,
    and superseded policies.
    """

    CORPUS_VERSION = "ghostops-history-v1"

    @classmethod
    def get_corpus(cls) -> List[HistoricalMemoryRecord]:
        corpus: List[HistoricalMemoryRecord] = []

        # =========================================================================
        # 1. FLAGSHIP HISTORICAL INCIDENT #1847 (Baseline Precedent from 6 months ago)
        # =========================================================================
        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-inc-1847",
            title="Historical Incident #1847: Client Connection Pool Saturation on Single-Region Cluster",
            description="Auth service exhausted client pool maxing out 50 connections during peak login rush in single-region us-east-1.",
            service="auth-service",
            region="us-east-1",
            severity="HIGH",
            symptoms=["connection_pool_exhaustion", "database_connection_saturation", "error_rate_elevation"],
            root_cause="Client connection pool limit set too low (50) for peak auth concurrency on single-region CockroachDB v23.2.3.",
            action_command="ADJUST_CONNECTION_POOL",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            service_version="v4.2.0",
            db_version="CockroachDB v23.2.3",
            topology={"nodes": ["auth-1", "auth-2"], "multi_region": False},
            configuration={"connection_pool_max": 50, "leaseholder_preference": "us-east-1"},
            days_ago=180
        ))

        # =========================================================================
        # 2. SECURITY & NETWORK INGRESS INCIDENTS (8 records)
        # =========================================================================
        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-auth-001",
            title="Unrestricted Security Group SSH Port 22 Exposure",
            description="Automated port scan identified inbound SSH port 22 open to 0.0.0.0/0 creating socket starvation.",
            service="auth-service",
            region="us-east-1",
            severity="HIGH",
            symptoms=["unauthorized_ingress_traffic", "ssh_brute_force_surge", "tcp_socket_starvation"],
            root_cause="Security group ingress rule accidentally allowed 0.0.0.0/0 on port 22 during debug session.",
            action_command="CHANGE_SECURITY_RULE",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="VERIFIED_GOLD",
            days_ago=60
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-auth-002",
            title="Cleartext HTTP Port 80 Ingress Insecure Traffic",
            description="Auth service ALB accepted unencrypted port 80 traffic leading to token interception risk.",
            service="auth-service",
            region="us-east-1",
            severity="MEDIUM",
            symptoms=["cleartext_http_traffic", "unencrypted_token_transmission"],
            root_cause="Missing HTTP to HTTPS listener redirect rule on security group and load balancer.",
            action_command="CHANGE_SECURITY_RULE",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=45
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-gw-001",
            title="Gateway Listener TLS Cipher Suite Degradation",
            description="Gateway service rejected client handshakes due to deprecated TLS 1.0/1.1 negotiation requests.",
            service="gateway-service",
            region="us-east-1",
            severity="MEDIUM",
            symptoms=["tls_handshake_failure", "client_connection_reset", "ssl_protocol_error"],
            root_cause="Outdated ALB security policy allowing obsolete cipher suites.",
            action_command="UPDATE_LISTENER_CERT",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=90
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-gw-002",
            title="API Gateway Rate Limiter Ingress Surge",
            description="Public API gateway experienced token bucket exhaustion from unthrottled partner webhooks.",
            service="gateway-service",
            region="us-east-1",
            severity="HIGH",
            symptoms=["rate_limit_saturation", "http_429_spike", "downstream_queue_backup"],
            root_cause="WAF rate limit rule set above threshold allowing burst traffic.",
            action_command="UPDATE_WAF_RULE",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=35
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-orders-001",
            title="Orders Database Direct Port 26257 Ingress Exposure",
            description="Orders service database port 26257 was exposed to wide subnet rather than application security group.",
            service="orders-service",
            region="us-east-1",
            severity="CRITICAL",
            symptoms=["database_port_exposure", "unauthorized_sql_handshake"],
            root_cause="Overly permissive CIDR block on CockroachDB ingress firewall rule.",
            action_command="CHANGE_SECURITY_RULE",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="VERIFIED_GOLD",
            days_ago=120
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-pay-001",
            title="Payment Processor Outbound Webhook Egress Block",
            description="Payment gateway failed to dispatch capture webhooks due to missing egress rule on port 443.",
            service="payment-service",
            region="us-east-1",
            severity="HIGH",
            symptoms=["webhook_dispatch_timeout", "egress_traffic_drop", "payment_capture_delay"],
            root_cause="Security group outbound egress rule restricted to private CIDR excluding public payment provider.",
            action_command="CHANGE_SECURITY_RULE",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=50
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-inv-001",
            title="Cross-VPC Peering Ingress Configuration Error",
            description="Inventory service lost sync with warehouse microservice across peered VPC.",
            service="inventory-service",
            region="us-east-1",
            severity="MEDIUM",
            symptoms=["cross_vpc_peering_drop", "inter_service_timeout"],
            root_cause="Security group ingress rule lacked secondary VPC CIDR block.",
            action_command="UPDATE_SECURITY_GROUP",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=75
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-notif-001",
            title="Notification SQS Queue Overly Permissive Access Policy",
            description="Notification dispatch queue allowed unauthorized SendMessage calls from untrusted IAM principals.",
            service="notification-service",
            region="us-east-1",
            severity="MEDIUM",
            symptoms=["unauthorized_queue_write", "spam_message_injection"],
            root_cause="Wildcard IAM principal in SQS queue access policy statement.",
            action_command="SET_QUEUE_ATTRIBUTES",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=110
        ))

        # =========================================================================
        # 3. DATABASE CONTENTION & QUERY OPTIMIZATION INCIDENTS (8 records)
        # =========================================================================
        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-bill-002",
            title="Billing Ledger Transaction Lock Deadlock Spike",
            description="Cascading transaction deadlocks on billing invoice ledgers during end-of-month reconciliation.",
            service="billing-service",
            region="us-east-1",
            severity="HIGH",
            symptoms=["transaction_lock_contention", "deadlock_spike", "database_timeout"],
            root_cause="Row-level contention on invoice account table during concurrent batch billing.",
            action_command="RESTART_SERVICE",
            action_result="FAILED",
            memory_type="negative",
            trust_level="HIGH",
            days_ago=40
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-bill-003",
            title="Billing Batch Query Lock Contention Resolution",
            description="Resolved invoice lock contention by migrating batch queries to optimistic lock retry pattern.",
            service="billing-service",
            region="us-east-1",
            severity="HIGH",
            symptoms=["transaction_lock_contention", "invoice_batch_delay"],
            root_cause="Pessimistic locking on invoice updates during multi-threaded batch dispatch.",
            action_command="OPTIMIZE_TRANSACTION_ISOLATION",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="VERIFIED_GOLD",
            days_ago=38
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-orders-002",
            title="CockroachDB Leaseholder Range Overload on Hot Table",
            description="Orders table range leaseholder concentrated on single node causing CPU bottleneck.",
            service="orders-service",
            region="us-east-1",
            severity="HIGH",
            symptoms=["leaseholder_imbalance", "hot_spot_cpu_spike", "p99_latency_elevation"],
            root_cause="Range leaseholder preference misconfigured on orders primary key index.",
            action_command="SET_LEASEHOLDER_PREFERENCE",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=70
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-orders-003",
            title="Checkout Database Connection Leak During Spike",
            description="Idle database connections accumulated on orders pool without returning to pool.",
            service="orders-service",
            region="us-east-1",
            severity="HIGH",
            symptoms=["connection_leak", "pool_exhaustion", "http_500_checkout_error"],
            root_cause="Missing connection close handler on cancelled HTTP checkout requests.",
            action_command="DRAIN_IDLE_CONNECTIONS",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=55
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-inv-002",
            title="Inventory Range Split Contention in Multi-Region Cluster",
            description="Rapid inserts during global catalog update caused concurrent range split delays.",
            service="inventory-service",
            region="us-east-1",
            severity="HIGH",
            symptoms=["range_split_contention", "insert_latency_elevation"],
            root_cause="Sequential UUID key distribution causing monotonic range growth on one node.",
            action_command="SPLIT_TABLE_RANGES",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=80
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-pay-002",
            title="Payment Ledger Idempotency Lock Retry Storm",
            description="Parallel webhook callbacks for same invoice triggered retry storms.",
            service="payment-service",
            region="us-east-1",
            severity="MEDIUM",
            symptoms=["idempotency_lock_retry", "duplicate_callback_surge"],
            root_cause="Zero-jitter retry policy on duplicate payment capture attempts.",
            action_command="RETRY_WITH_EXPONENTIAL_BACKOFF",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=65
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-auth-003",
            title="Auth Session Table Bloat and Vacuum Lag",
            description="Expired user session tokens accumulated without periodic tombstone cleanup.",
            service="auth-service",
            region="us-east-1",
            severity="MEDIUM",
            symptoms=["session_table_bloat", "query_plan_degradation", "vacuum_lag"],
            root_cause="TTL expiry job stopped running due to scheduled task worker crash.",
            action_command="CLEANUP_EXPIRED_SESSIONS",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=95
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-notif-002",
            title="PostgreSQL 14 Notification Database Connection Starvation",
            description="Notification dispatch workers saturated PostgreSQL max_connections setting.",
            service="notification-service",
            region="us-east-1",
            severity="HIGH",
            symptoms=["postgres_connection_exhaustion", "socket_refusal"],
            root_cause="Missing PgBouncer connection pooler in front of raw PostgreSQL instance.",
            action_command="RESTART_SERVICE",
            action_result="FAILED",
            memory_type="negative",
            trust_level="HIGH",
            db_version="PostgreSQL v14.0",
            days_ago=100
        ))

        # =========================================================================
        # 4. TOPOLOGY, SCALING & RESOURCE MANAGEMENT (8 records)
        # =========================================================================
        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-inv-003",
            title="High Host CPU Utilization from Background Storage Compaction",
            description="Telemetry flagged 98% host CPU utilization while microservice latency remained sub-millisecond (12ms).",
            service="inventory-service",
            region="us-east-1",
            severity="LOW",
            symptoms=["high_host_cpu", "normal_latency", "contradictory_metrics"],
            root_cause="Routine scheduled background RocksDB compaction job utilizing spare CPU cores without serving degradation.",
            action_command="SCALE_RESOURCE",
            action_result="FAILED",
            memory_type="negative",
            trust_level="HIGH",
            days_ago=25
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-inv-004",
            title="Inventory Read Replica Replication Delay",
            description="Read traffic on reporting replica returned stale stock counts due to replication lag.",
            service="inventory-service",
            region="us-east-1",
            severity="MEDIUM",
            symptoms=["replica_lag", "stale_inventory_read"],
            root_cause="Network bandwidth throttling on replica sync channel during bulk stock ingest.",
            action_command="REBALANCE_READ_REPLICAS",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=42
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-orders-004",
            title="Orders ECS Task Memory Saturation During Flash Sale",
            description="Container memory reached 92% ceiling leading to container throttling.",
            service="orders-service",
            region="us-east-1",
            severity="HIGH",
            symptoms=["memory_saturation", "task_throttling", "latency_elevation"],
            root_cause="Sudden 10x traffic spike exceeding provisioned ECS task container capacity.",
            action_command="SCALE_ECS_TASKS",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="VERIFIED_GOLD",
            days_ago=30
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-pay-003",
            title="Payment Worker Thread Pool Saturation",
            description="HTTP client worker threads blocked waiting on slow downstream banking gateway.",
            service="payment-service",
            region="us-east-1",
            severity="HIGH",
            symptoms=["thread_pool_exhaustion", "worker_starvation", "http_504_gateway_timeout"],
            root_cause="Default client socket timeout set too high (60s) allowing stalled connections to consume workers.",
            action_command="ADJUST_THREAD_POOL",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=52
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-auth-004",
            title="Auth JVM Heap Space Fragmentation OOM",
            description="Auth service crashed with OutOfMemoryError after 45 days continuous uptime.",
            service="auth-service",
            region="us-east-1",
            severity="HIGH",
            symptoms=["jvm_oom", "container_restart", "heap_fragmentation"],
            root_cause="G1GC garbage collection parameters unoptimized for high object churn auth tokens.",
            action_command="ADJUST_JVM_HEAP",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=85
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-gw-003",
            title="Gateway ALB Target Group Unhealthy Host Drop",
            description="ALB marked 2 of 4 gateway instances unhealthy after health check timeout.",
            service="gateway-service",
            region="us-east-1",
            severity="HIGH",
            symptoms=["unhealthy_host_count", "alb_502_error", "traffic_skew"],
            root_cause="Health check endpoint performing deep database query rather than shallow liveness check.",
            action_command="DEREGISTER_UNHEALTHY_TARGETS",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=48
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-bill-004",
            title="Billing Volume Disk IOPS Throttling",
            description="EBS volume burst balance dropped to zero during monthly financial ledger aggregation.",
            service="billing-service",
            region="us-east-1",
            severity="HIGH",
            symptoms=["iops_throttling", "ebs_burst_depletion", "write_latency_spike"],
            root_cause="gp2 storage volume IOPS baseline insufficient for sustained ledger writes.",
            action_command="MODIFY_VOLUME_IOPS",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=62
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-notif-003",
            title="Notification Consumer Worker Thread Saturation",
            description="Push notification dispatch backlog grew to 150,000 messages.",
            service="notification-service",
            region="us-east-1",
            severity="MEDIUM",
            symptoms=["sqs_queue_backlog", "message_processing_delay"],
            root_cause="Under-provisioned worker pool unable to keep pace with marketing campaign broadcast.",
            action_command="SCALE_CONSUMER_WORKERS",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=72
        ))

        # =========================================================================
        # 5. NEGATIVE OPERATIONAL KNOWLEDGE & HARMFUL ACTIONS (7 records)
        # =========================================================================
        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-neg-001",
            title="Flushing Security Group Ingress Rules During Peak Traffic",
            description="Flushing security group ingress rules in bulk severed active internal microservice communication.",
            service="auth-service",
            region="us-east-1",
            severity="CRITICAL",
            symptoms=["security_rule_flush_cascade", "network_partition", "error_rate_spike_99"],
            root_cause="Negative Knowledge: Mass security group flush drops established TCP sessions immediately.",
            action_command="CHANGE_SECURITY_RULE",
            action_result="FAILED",
            memory_type="negative",
            trust_level="HIGH",
            days_ago=90
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-neg-002",
            title="Forced Kill -9 on Database Primary Node During Lock Wait",
            description="Hard killing database process during deadlock caused 45-minute WAL recovery replay stall.",
            service="billing-service",
            region="us-east-1",
            severity="CRITICAL",
            symptoms=["database_recovery_stall", "wal_replay_delay", "split_brain_risk"],
            root_cause="Negative Knowledge: Hard termination during active transactions induces extended crash recovery.",
            action_command="RESTART_SERVICE",
            action_result="FAILED",
            memory_type="negative",
            trust_level="HIGH",
            days_ago=115
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-neg-003",
            title="Immediate Rollback of Database Schema Migration Without Deprecation",
            description="Rolling back schema migration dropped active column causing active microservices to crash.",
            service="orders-service",
            region="us-east-1",
            severity="HIGH",
            symptoms=["schema_deserialization_error", "instant_crash_loop"],
            root_cause="Negative Knowledge: Reversing schema migrations without backwards-compatible view breaks running services.",
            action_command="ROLLBACK_MIGRATION",
            action_result="FAILED",
            memory_type="negative",
            trust_level="HIGH",
            days_ago=88
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-neg-004",
            title="Resetting Rate Limit Counter Tables During Active DDoS",
            description="Flushing rate limit Redis keys during volumetric attack allowed millions of requests into DB.",
            service="payment-service",
            region="us-east-1",
            severity="CRITICAL",
            symptoms=["rate_limit_bypass", "backend_saturation"],
            root_cause="Negative Knowledge: Resetting rate limits during active traffic surge exposes core database.",
            action_command="FLUSH_RATE_LIMITS",
            action_result="FAILED",
            memory_type="negative",
            trust_level="HIGH",
            days_ago=105
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-neg-005",
            title="Lowering Keep-Alive Timeouts Below 1 Second",
            description="Setting HTTP keep-alive timeout to 500ms forced rapid SSL/TLS connection renegotiation.",
            service="gateway-service",
            region="us-east-1",
            severity="HIGH",
            symptoms=["tls_renegotiation_storm", "gateway_cpu_spike"],
            root_cause="Negative Knowledge: Sub-second keep-alive creates severe TLS CPU handshake overhead.",
            action_command="UPDATE_TIMEOUT_CONFIG",
            action_result="FAILED",
            memory_type="negative",
            trust_level="HIGH",
            days_ago=92
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-neg-006",
            title="Truncating Distributed Cache Cluster on Sync Errors",
            description="Flushing entire Redis cache cluster caused thundering herd query storm on CockroachDB.",
            service="inventory-service",
            region="us-east-1",
            severity="HIGH",
            symptoms=["thundering_herd_storm", "cache_stampede", "database_exhaustion"],
            root_cause="Negative Knowledge: Total cache truncation without warm-up crushes database layer.",
            action_command="FLUSH_CACHE_CLUSTER",
            action_result="FAILED",
            memory_type="negative",
            trust_level="HIGH",
            days_ago=78
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-neg-007",
            title="Broadening IAM Permissions with Wildcard on Auth Failure",
            description="Attempted to bypass S3 access denied error by granting Action: s3:* on all resources.",
            service="auth-service",
            region="us-east-1",
            severity="CRITICAL",
            symptoms=["iam_policy_violation", "unauthorized_resource_access"],
            root_cause="Negative Knowledge: Wildcard IAM escalation violates least privilege and triggers compliance alerts.",
            action_command="IAM_GRANT_WILDCARD",
            action_result="FAILED",
            memory_type="negative",
            trust_level="HIGH",
            days_ago=130
        ))

        # =========================================================================
        # 6. SUPERSEDED POLICIES & IMMUTABLE HISTORICAL VERSIONS (7 records)
        # =========================================================================
        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-sup-001",
            title="Legacy Auth Connection Allocation Formula (Static 20 Connections)",
            description="Old v3.x static pool formula of allocating fixed 20 connections per container.",
            service="auth-service",
            region="us-east-1",
            severity="LOW",
            symptoms=["static_pool_allocation"],
            root_cause="Legacy static configuration superseded by dynamic adaptive pool sizing.",
            action_command="SET_STATIC_CONNECTION_POOL",
            action_result="SUCCESS",
            memory_type="superseded",
            trust_level="LOW",
            service_version="v3.8.0",
            superseded_by="hist-sup-002",
            memory_status="SUPERSEDED",
            days_ago=250
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-sup-002",
            title="Modern Auth Adaptive Dynamic Connection Pool Sizing",
            description="Dynamic connection pool auto-adjusting based on active DB leaseholder capacity.",
            service="auth-service",
            region="us-east-1",
            severity="LOW",
            symptoms=["adaptive_pool_sizing"],
            root_cause="Current modern standard configuration for auth-service.",
            action_command="SET_DYNAMIC_CONNECTION_POOL",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            service_version="v4.2.0",
            memory_status="ACTIVE",
            days_ago=60
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-sup-003",
            title="Orders Single-Region Leaseholder Pinning Policy",
            description="Old pinning policy forcing all leaseholders to us-east-1 node 1.",
            service="orders-service",
            region="us-east-1",
            severity="LOW",
            symptoms=["single_region_pinning"],
            root_cause="Single region pinning policy obsolete after multi-region cluster upgrade.",
            action_command="PIN_LEASEHOLDER_SINGLE_NODE",
            action_result="SUCCESS",
            memory_type="superseded",
            trust_level="LOW",
            service_version="v3.9.0",
            db_version="CockroachDB v22.2.0",
            superseded_by="hist-sup-004",
            memory_status="SUPERSEDED",
            days_ago=300
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-sup-004",
            title="Orders Multi-Region Follower Read and Zone Balancing",
            description="Modern follower read policy distributing query load across multi-region nodes.",
            service="orders-service",
            region="us-east-1",
            severity="LOW",
            symptoms=["follower_read_balancing"],
            root_cause="Current standard multi-region read optimization policy.",
            action_command="ENABLE_FOLLOWER_READS",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            service_version="v4.2.0",
            db_version="CockroachDB v23.2.3",
            memory_status="ACTIVE",
            days_ago=80
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-sup-005",
            title="Billing Synchronous Webhook Dispatch Architecture",
            description="Legacy synchronous HTTP dispatcher calling customer webhook endpoints inline.",
            service="billing-service",
            region="us-east-1",
            severity="LOW",
            symptoms=["synchronous_webhook_dispatch"],
            root_cause="Synchronous webhook delivery superseded by asynchronous SQS queue architecture.",
            action_command="DISPATCH_SYNC_WEBHOOK",
            action_result="SUCCESS",
            memory_type="superseded",
            trust_level="LOW",
            superseded_by="hist-sup-006",
            memory_status="SUPERSEDED",
            days_ago=220
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-sup-006",
            title="Billing Asynchronous SQS Dead-Letter Queue Dispatcher",
            description="Modern decoupled event-driven webhook dispatch with exponential backoff and DLQ.",
            service="billing-service",
            region="us-east-1",
            severity="LOW",
            symptoms=["async_sqs_webhook_dispatch"],
            root_cause="Current standard decoupled webhook delivery pipeline.",
            action_command="DISPATCH_ASYNC_SQS_WEBHOOK",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            memory_status="ACTIVE",
            days_ago=50
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-sup-007",
            title="Gateway HTTP/1.1 Internal Microservice Transport",
            description="Legacy HTTP/1.1 connection pooling for inter-service communication.",
            service="gateway-service",
            region="us-east-1",
            severity="LOW",
            symptoms=["http11_internal_transport"],
            root_cause="Superseded by gRPC HTTP/2 multiplexed streaming channels.",
            action_command="CONFIGURE_HTTP11_POOL",
            action_result="SUCCESS",
            memory_type="superseded",
            trust_level="LOW",
            memory_status="SUPERSEDED",
            days_ago=280
        ))

        # =========================================================================
        # 7. REGION-SPECIFIC & MULTI-REGION KNOWLEDGE (7 records)
        # =========================================================================
        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-reg-001",
            title="Payment GDPR Latency Compliance Routing in EU-West-1",
            description="European payment gateway traffic routed to local CockroachDB leaseholders for GDPR compliance.",
            service="payment-service",
            region="eu-west-1",
            severity="MEDIUM",
            symptoms=["cross_border_latency", "gdpr_compliance_check"],
            root_cause="Cross-region transatlantic roundtrips violating regional latency SLA.",
            action_command="SET_LOCAL_LEASEHOLDER_EU",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=70
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-reg-002",
            title="Auth US-West-2 Secondary Region Replication Lag",
            description="Cross-region consensus quorum delays between us-east-1 and us-west-2 during network fiber flap.",
            service="auth-service",
            region="us-west-2",
            severity="HIGH",
            symptoms=["cross_region_raft_lag", "quorum_latency_spike"],
            root_cause="Inter-region peering transit gateway bandwidth saturation.",
            action_command="ADJUST_REPLICATION_FACTOR",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=65
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-reg-003",
            title="Orders Route53 DNS Health Check Automated Failover",
            description="Route53 failed over traffic from us-east-1 to us-west-2 following regional power outage.",
            service="orders-service",
            region="us-west-2",
            severity="CRITICAL",
            symptoms=["regional_failover", "dns_health_check_switch"],
            root_cause="Regional power outage in primary availability zone.",
            action_command="UPDATE_ROUTE53_HEALTH_CHECK",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="VERIFIED_GOLD",
            days_ago=140
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-reg-004",
            title="Inventory EU-West-1 Multi-AZ Partition Recovery",
            description="Isolated availability zone network split resolved by promoting remaining two AZ leaseholders.",
            service="inventory-service",
            region="eu-west-1",
            severity="HIGH",
            symptoms=["az_partition", "leaseholder_failover"],
            root_cause="AZ-level fiber cut in Dublin datacenter.",
            action_command="REBALANCE_AZ_LEASEHOLDERS",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=95
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-reg-005",
            title="Gateway US-West-2 CloudFront Edge Cache Invalidation",
            description="Corrupted static asset cached at edge popped with targeted distribution invalidation.",
            service="gateway-service",
            region="us-west-2",
            severity="MEDIUM",
            symptoms=["stale_edge_cache", "corrupted_asset_delivery"],
            root_cause="Missing cache-busting asset hash in continuous deployment pipeline.",
            action_command="INVALIDATE_CLOUDFRONT_CACHE",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=55
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-reg-006",
            title="Notification EU-West-1 Local SMS Provider Failover",
            description="Primary European SMS gateway experienced routing outage; traffic diverted to backup aggregator.",
            service="notification-service",
            region="eu-west-1",
            severity="HIGH",
            symptoms=["sms_delivery_failure", "third_party_outage"],
            root_cause="Upstream telecom provider network partition in Frankfurt.",
            action_command="FAILOVER_SMS_PROVIDER",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=45
        ))

        corpus.append(HistoricalMemoryRecord(
            incident_id="hist-reg-007",
            title="Billing US-West-2 Range Consensus Stall",
            description="Range leaseholder lost quorum during node maintenance in us-west-2.",
            service="billing-service",
            region="us-west-2",
            severity="HIGH",
            symptoms=["range_consensus_stall", "leaseholder_transfer_delay"],
            root_cause="Simultaneous maintenance restart of two nodes in same availability zone.",
            action_command="SYNC_COCKROACH_RANGES",
            action_result="SUCCESS",
            memory_type="remediation",
            trust_level="HIGH",
            days_ago=82
        ))

        return corpus
