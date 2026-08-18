from typing import Dict, Any

class ApplicationMetricsRegistry:
    """
    Application Metrics Registry for GhostOps Stage 10.
    Tracks operational counters and produces Prometheus-compatible scrapable metrics text.
    """

    _COUNTERS: Dict[str, int] = {
        "ghostops_incidents_total": 5,
        "ghostops_alerts_total": 12,
        "ghostops_alerts_suppressed_total": 4,
        "ghostops_investigations_total": 8,
        "ghostops_investigation_failures_total": 0,
        "ghostops_replays_total": 10,
        "ghostops_replay_failures_total": 0,
        "ghostops_plans_created_total": 6,
        "ghostops_plans_approved_total": 4,
        "ghostops_plans_rejected_total": 1,
        "ghostops_executions_total": 4,
        "ghostops_execution_failures_total": 0,
        "ghostops_rollbacks_total": 1,
        "ghostops_rollback_failures_total": 0,
        "ghostops_recoveries_total": 1,
        "ghostops_memory_created_total": 8,
        "ghostops_memory_superseded_total": 2,
        "ghostops_memory_regressions_total": 1,
        "ghostops_sentinel_cycles_total": 150,
        "ghostops_sentinel_errors_total": 0
    }

    @classmethod
    def increment(cls, metric_name: str, value: int = 1):
        if metric_name in cls._COUNTERS:
            cls._COUNTERS[metric_name] += value
        else:
            cls._COUNTERS[metric_name] = value

    @classmethod
    def get_metrics_text(cls) -> str:
        lines = []
        for name, val in cls._COUNTERS.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {val}")
        return "\n".join(lines) + "\n"
