import uuid
from typing import Dict, Any, Tuple, Optional
from app.services.execution.mock_infrastructure import StatefulMockInfrastructure
from app.services.governance.action_catalog import ActionCatalog

from app.services.execution.aws_executor import AWSActionExecutor

class TypedActionExecutors:
    """
    Controlled Typed Action Executors for GhostOps Stage 6.
    Performs parameter validation, pre-state capture, post-state capture, secret redaction,
    and state reconciliation without allowing arbitrary shell/Python/AWS-CLI execution.
    Supports both live governed AWS execution and deterministic mock execution.
    """

    SECRET_KEYS = {"secret", "password", "token", "access_key", "secret_key", "authorization", "private_key"}

    @classmethod
    def redact_secrets(cls, data: Any) -> Any:
        return AWSActionExecutor.redact_secrets(data)

    @classmethod
    def execute_action(
        cls,
        action_type: str,
        target_resource: str,
        parameters: Dict[str, Any],
        idempotency_key: str,
        simulated_failure: bool = False,
        simulated_timeout: bool = False,
        force_real_aws: bool = False
    ) -> Tuple[bool, Dict[str, Any], Dict[str, Any], str, str, str]:
        return AWSActionExecutor.execute_action(
            action_type=action_type,
            target_resource=target_resource,
            parameters=parameters,
            idempotency_key=idempotency_key,
            simulated_failure=simulated_failure,
            simulated_timeout=simulated_timeout,
            force_real_aws=force_real_aws
        )

    @classmethod
    def compensate_action(
        cls,
        action_type: str,
        target_resource: str,
        rollback_parameters: Dict[str, Any],
        force_real_aws: bool = False
    ) -> Tuple[bool, Dict[str, Any], Dict[str, Any], str, str]:
        return AWSActionExecutor.compensate_action(
            action_type=action_type,
            target_resource=target_resource,
            rollback_parameters=rollback_parameters,
            force_real_aws=force_real_aws
        )

    @classmethod
    def reconcile_timeout_state(
        cls,
        action_type: str,
        target_resource: str,
        expected_params: Dict[str, Any]
    ) -> Tuple[bool, str]:
        curr_state = StatefulMockInfrastructure.get_resource_state(target_resource)

        if action_type == "CHANGE_SECURITY_RULE":
            port = expected_params.get("port", 22)
            rules = curr_state.get("security_group_ingress_rules", [])
            has_port = any(r.get("port") == port for r in rules)
            if not has_port:
                return True, "Reconciliation confirmed action completed despite initial request timeout."
        elif action_type == "ADJUST_CONNECTION_POOL":
            expected_max = expected_params.get("max_connections", 150)
            if curr_state.get("connection_pool_max") == expected_max:
                return True, "Reconciliation confirmed connection pool state matches target capacity."

        return False, "Reconciliation determined action was not applied during timeout."
