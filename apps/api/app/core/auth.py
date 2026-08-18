from typing import Optional, List
from pydantic import BaseModel
from fastapi import Request, HTTPException, status
from app.core.errors import GhostOpsException

class Role(str):
    SYSTEM = "SYSTEM"
    OPERATOR = "OPERATOR"
    ADMIN = "ADMIN"
    READ_ONLY = "READ_ONLY"

class ActorContext(BaseModel):
    actor_id: str
    role: str
    token: Optional[str] = None

class AuthorizationService:
    """
    Authorization Boundary Service for GhostOps Stage 10.
    Enforces deterministic Role-Based Access Control (RBAC).
    CRITICAL: SYSTEM role is prohibited from approving or executing remediation plans.
    """

    PERMISSIONS = {
        Role.READ_ONLY: ["view_incidents", "view_memory", "view_traces", "view_replay", "view_sentinel"],
        Role.OPERATOR: [
            "view_incidents", "view_memory", "view_traces", "view_replay", "view_sentinel",
            "trigger_investigation", "trigger_replay", "create_plan", "validate_plan", "reject_plan"
        ],
        Role.ADMIN: [
            "view_incidents", "view_memory", "view_traces", "view_replay", "view_sentinel",
            "trigger_investigation", "trigger_replay", "create_plan", "validate_plan", "reject_plan",
            "approve_plan", "execute_plan", "rollback_execution", "modify_sentinel_policy"
        ],
        Role.SYSTEM: [
            "view_incidents", "view_memory", "view_traces", "view_replay", "view_sentinel",
            "trigger_investigation", "trigger_replay", "create_plan"
        ]
    }

    @classmethod
    def check_permission(cls, actor: ActorContext, permission: str) -> bool:
        role_perms = cls.PERMISSIONS.get(actor.role, [])
        return permission in role_perms

    @classmethod
    def enforce_permission(cls, actor: ActorContext, permission: str):
        if not cls.check_permission(actor, permission):
            # Special message for SYSTEM attempting restricted actions
            if actor.role == Role.SYSTEM and permission in ["approve_plan", "execute_plan"]:
                raise GhostOpsException(
                    error_code="AUTONOMOUS_EXECUTION_FORBIDDEN",
                    message=f"CRITICAL SAFETY VIOLATION: Role 'SYSTEM' is strictly prohibited from executing '{permission}'. Stage 5 human approval required.",
                    status_code=status.HTTP_403_FORBIDDEN
                )
            raise GhostOpsException(
                error_code="UNAUTHORIZED_ACTION",
                message=f"Role '{actor.role}' lacks permission '{permission}'.",
                status_code=status.HTTP_403_FORBIDDEN
            )

def get_current_actor(request: Request) -> ActorContext:
    role_hdr = request.headers.get("X-GhostOps-Role", Role.ADMIN)  # Defaults to ADMIN in development/test
    actor_id = request.headers.get("X-GhostOps-Actor", "DevOpsLead")
    return ActorContext(actor_id=actor_id, role=role_hdr)
