from typing import Dict, Any, Tuple

class StatefulMockInfrastructure:
    """
    Stateful Mock Infrastructure Environment for GhostOps Stage 6.
    Maintains simulated infrastructure state (connection pools, security rules, task counts)
    and evaluates pre-state and post-state mutations deterministically.
    """

    _STATE_STORE: Dict[str, Dict[str, Any]] = {
        "default": {
            "connection_pool_max": 50,
            "security_group_ingress_rules": [
                {"protocol": "tcp", "port": 22, "cidr_block": "0.0.0.0/0"},
                {"protocol": "tcp", "port": 443, "cidr_block": "0.0.0.0/0"}
            ],
            "desired_task_count": 2,
            "min_task_count": 1,
            "max_task_count": 10,
            "service_version": "v4.2.0",
            "secret_version": "v1-active",
            "drain_status": "NORMAL"
        }
    }

    @classmethod
    def get_resource_state(cls, target_arn: str) -> Dict[str, Any]:
        return cls._STATE_STORE.get(target_arn, dict(cls._STATE_STORE["default"]))

    @classmethod
    def apply_mutation(cls, target_arn: str, action_type: str, parameters: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        pre_state = cls.get_resource_state(target_arn)
        post_state = dict(pre_state)

        if action_type == "CHANGE_SECURITY_RULE":
            sg_id = parameters.get("security_group_id", "sg-012345")
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
            post_state["last_restart_timestamp"] = "2026-08-18T00:15:00Z"
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

        cls._STATE_STORE[target_arn] = post_state
        return pre_state, post_state
