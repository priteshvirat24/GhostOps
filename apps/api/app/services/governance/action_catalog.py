from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ActionDefinition(BaseModel):
    action_type: str
    description: str
    default_safety_level: str  # READ_ONLY | LOW_RISK | MEDIUM_RISK | HIGH_RISK | CRITICAL
    default_blast_radius: str  # LOCAL | SERVICE | CLUSTER | REGION | GLOBAL
    required_parameters: List[str]
    allowed_target_types: List[str]
    rollback_required: bool = True
    verification_required: bool = True
    validation_rules: List[str] = Field(default_factory=list)

class ActionCatalog:
    """
    Controlled catalog of allowed remediation action types in GhostOps Stage 5.
    Prevents LLM agents from inventing arbitrary or ungoverned infrastructure actions.
    """

    CATALOG: Dict[str, ActionDefinition] = {
        "UPDATE_CONFIGURATION": ActionDefinition(
            action_type="UPDATE_CONFIGURATION",
            description="Update service or application environment configuration parameters.",
            default_safety_level="LOW_RISK",
            default_blast_radius="SERVICE",
            required_parameters=["config_key", "config_value"],
            allowed_target_types=["ECS_SERVICE", "LAMBDA_FUNCTION", "EC2_INSTANCE"],
            rollback_required=True,
            verification_required=True,
            validation_rules=["config_key must be non-empty", "config_value must be non-null"]
        ),
        "SCALE_RESOURCE": ActionDefinition(
            action_type="SCALE_RESOURCE",
            description="Adjust target container task count or autoscaling instance capacity.",
            default_safety_level="MEDIUM_RISK",
            default_blast_radius="CLUSTER",
            required_parameters=["desired_count", "min_count", "max_count"],
            allowed_target_types=["ECS_SERVICE", "EC2_INSTANCE"],
            rollback_required=True,
            verification_required=True,
            validation_rules=["desired_count >= min_count", "desired_count <= max_count"]
        ),
        "RESTART_SERVICE": ActionDefinition(
            action_type="RESTART_SERVICE",
            description="Perform a graceful rolling restart of target service tasks or cluster node.",
            default_safety_level="MEDIUM_RISK",
            default_blast_radius="SERVICE",
            required_parameters=["drain_seconds"],
            allowed_target_types=["ECS_SERVICE", "COCKROACH_NODE"],
            rollback_required=False,
            verification_required=True,
            validation_rules=["drain_seconds >= 0"]
        ),
        "ROTATE_CONFIGURATION": ActionDefinition(
            action_type="ROTATE_CONFIGURATION",
            description="Trigger secret or IAM authentication token rotation.",
            default_safety_level="MEDIUM_RISK",
            default_blast_radius="SERVICE",
            required_parameters=["secret_arn"],
            allowed_target_types=["IAM_ROLE", "ECS_SERVICE"],
            rollback_required=True,
            verification_required=True,
            validation_rules=["secret_arn must be valid ARN format"]
        ),
        "CHANGE_SECURITY_RULE": ActionDefinition(
            action_type="CHANGE_SECURITY_RULE",
            description="Modify network ingress/egress security group rules or firewall ACLs.",
            default_safety_level="HIGH_RISK",
            default_blast_radius="REGION",
            required_parameters=["security_group_id", "protocol", "port", "cidr_block"],
            allowed_target_types=["SECURITY_GROUP", "VPC_SUBNET"],
            rollback_required=True,
            verification_required=True,
            validation_rules=["security_group_id format validation", "port range 1-65535"]
        ),
        "ROLLBACK_DEPLOYMENT": ActionDefinition(
            action_type="ROLLBACK_DEPLOYMENT",
            description="Revert target service image digest to previously verified stable deployment version.",
            default_safety_level="HIGH_RISK",
            default_blast_radius="SERVICE",
            required_parameters=["target_revision"],
            allowed_target_types=["ECS_SERVICE", "LAMBDA_FUNCTION"],
            rollback_required=True,
            verification_required=True,
            validation_rules=["target_revision must exist in deployment history"]
        ),
        "REVERT_CONFIGURATION": ActionDefinition(
            action_type="REVERT_CONFIGURATION",
            description="Revert configuration key to baseline historical value.",
            default_safety_level="LOW_RISK",
            default_blast_radius="SERVICE",
            required_parameters=["config_key", "baseline_value"],
            allowed_target_types=["ECS_SERVICE", "LAMBDA_FUNCTION", "EC2_INSTANCE"],
            rollback_required=True,
            verification_required=True,
            validation_rules=["baseline_value must be provided"]
        ),
        "ADJUST_CONNECTION_POOL": ActionDefinition(
            action_type="ADJUST_CONNECTION_POOL",
            description="Adjust maximum database connection pool size or connection timeout limit.",
            default_safety_level="MEDIUM_RISK",
            default_blast_radius="CLUSTER",
            required_parameters=["max_connections", "idle_timeout_seconds"],
            allowed_target_types=["COCKROACH_NODE", "ECS_SERVICE"],
            rollback_required=True,
            verification_required=True,
            validation_rules=["max_connections between 5 and 500"]
        ),
        "DRAIN_RESOURCE": ActionDefinition(
            action_type="DRAIN_RESOURCE",
            description="Gracefully drain connections from target instance or node prior to maintenance.",
            default_safety_level="HIGH_RISK",
            default_blast_radius="CLUSTER",
            required_parameters=["drain_timeout_seconds"],
            allowed_target_types=["COCKROACH_NODE", "EC2_INSTANCE"],
            rollback_required=True,
            verification_required=True,
            validation_rules=["drain_timeout_seconds > 0"]
        ),
    }

    @classmethod
    def get_action_definition(cls, action_type: str) -> Optional[ActionDefinition]:
        return cls.CATALOG.get(action_type)

    @classmethod
    def validate_action(cls, action_type: str, target: str, parameters: Dict[str, Any]) -> List[str]:
        defn = cls.get_action_definition(action_type)
        if not defn:
            return [f"Unknown or unauthorized action type '{action_type}' in action catalog."]

        errors: List[str] = []
        for param in defn.required_parameters:
            if param not in parameters or parameters[param] is None:
                errors.append(f"Missing required parameter '{param}' for action '{action_type}'.")

        return errors
