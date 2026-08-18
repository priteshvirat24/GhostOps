import copy
import hashlib
import json
from typing import Dict, Any, Tuple
from app.core.errors import GhostOpsException

class SimulationEnvironment:
    """
    Isolated Simulation Environment for GhostOps Stage 8 & 10.
    Clones historical infrastructure state into an isolated in-memory sandbox.
    Guarantees ZERO mutation to production or live AWS adapters. Fail closed if a live adapter is supplied.
    """

    def __init__(self, baseline_state: Dict[str, Any] = None, live_adapter: Any = None):
        if live_adapter is not None:
            raise GhostOpsException(
                error_code="SIMULATION_LIVE_ADAPTER_REJECTED",
                message="REPLAY SAFETY VIOLATION: SimulationEnvironment cannot accept live infrastructure adapters. Replay must execute only in isolated memory.",
                status_code=400
            )

        self._simulated_state: Dict[str, Dict[str, Any]] = {}
        if baseline_state:
            for k, v in baseline_state.items():
                self._simulated_state[k] = copy.deepcopy(v)
        else:
            self._simulated_state["default"] = {
                "connection_pool_max": 50,
                "security_group_ingress_rules": [
                    {"protocol": "tcp", "port": 22, "cidr_block": "0.0.0.0/0"},
                    {"protocol": "tcp", "port": 443, "cidr_block": "0.0.0.0/0"}
                ],
                "desired_task_count": 2,
                "service_version": "v4.2.0",
                "secret_version": "v1-active",
                "drain_status": "NORMAL"
            }

    def get_resource_state(self, resource_id: str) -> Dict[str, Any]:
        return copy.deepcopy(self._simulated_state.get(resource_id, self._simulated_state.get("default", {})))

    def apply_simulated_mutation(self, resource_id: str, action_type: str, parameters: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
        pre_state = self.get_resource_state(resource_id)
        post_state = copy.deepcopy(pre_state)

        if action_type == "CHANGE_SECURITY_RULE":
            port = parameters.get("port", 22)
            cidr = parameters.get("cidr_block", "0.0.0.0/0")
            rules = list(post_state.get("security_group_ingress_rules", []))
            if cidr == "0.0.0.0/0":
                rules = [r for r in rules if r.get("port") != port]
            else:
                rules.append({"protocol": "tcp", "port": port, "cidr_block": cidr})
            post_state["security_group_ingress_rules"] = rules

        elif action_type == "ADJUST_CONNECTION_POOL":
            new_max = parameters.get("max_connections", 150)
            post_state["connection_pool_max"] = new_max

        elif action_type == "SCALE_RESOURCE":
            desired = parameters.get("desired_count", 5)
            post_state["desired_task_count"] = desired

        elif action_type == "RESTART_SERVICE":
            post_state["last_restart_timestamp"] = "2026-08-18T00:40:00Z"
            post_state["service_status"] = "HEALTHY"

        elif action_type == "ROTATE_CONFIGURATION":
            post_state["secret_version"] = "v2-rotated"

        elif action_type == "ROLLBACK_DEPLOYMENT":
            target_rev = parameters.get("target_revision", "v4.1.0")
            post_state["service_version"] = target_rev

        elif action_type == "REVERT_CONFIGURATION":
            base_val = parameters.get("baseline_value", 50)
            post_state["connection_pool_max"] = base_val

        elif action_type == "DRAIN_RESOURCE":
            post_state["drain_status"] = "DRAINED"

        self._simulated_state[resource_id] = post_state

        hash_str = hashlib.sha256(json.dumps({
            "resource_id": resource_id,
            "action_type": action_type,
            "post_state": post_state
        }, sort_keys=True).encode()).hexdigest()

        return pre_state, post_state, hash_str
