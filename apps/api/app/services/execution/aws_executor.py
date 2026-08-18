import uuid
import re
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError, BotoCoreError, NoCredentialsError

from app.core.config import settings
from app.services.governance.action_catalog import ActionCatalog
from app.services.execution.mock_infrastructure import StatefulMockInfrastructure
from app.core.logging import logger

class AWSActionExecutor:
    """
    Governed AWS Real & Mock Execution Boundary for GhostOps Stage 6.
    Enforces narrow, controlled execution of governed AWS actions (specifically EC2 security group mutations).
    Prevents unrestricted boto3 access, captures real pre/post state, and strictly segregates MOCK vs AWS_REAL modes.
    """

    SECRET_KEYS = {"secret", "password", "token", "access_key", "secret_key", "authorization", "private_key"}

    @classmethod
    def redact_secrets(cls, data: Any) -> Any:
        if isinstance(data, dict):
            redacted = {}
            for k, v in data.items():
                if any(sk in k.lower() for sk in cls.SECRET_KEYS):
                    redacted[k] = "[REDACTED_SECRET]"
                else:
                    redacted[k] = cls.redact_secrets(v)
            return redacted
        elif isinstance(data, list):
            return [cls.redact_secrets(item) for item in data]
        return data

    @classmethod
    def extract_security_group_id(cls, target_resource: str, parameters: Dict[str, Any]) -> str:
        """Extracts security group ID (e.g., 'sg-012345') from target ARN or parameters."""
        if parameters.get("security_group_id"):
            return parameters["security_group_id"]
        # Check ARN pattern
        match = re.search(r'security-group/(sg-[a-zA-Z0-9]+)', target_resource)
        if match:
            return match.group(1)
        if target_resource.startswith("sg-"):
            return target_resource
        return parameters.get("security_group_id", target_resource)

    @classmethod
    def execute_action(
        cls,
        action_type: str,
        target_resource: str,
        parameters: Dict[str, Any],
        idempotency_key: str,
        is_compensation: bool = False,
        simulated_failure: bool = False,
        simulated_timeout: bool = False,
        force_real_aws: bool = False
    ) -> Tuple[bool, Dict[str, Any], Dict[str, Any], str, str, str]:
        """
        Executes a typed action through the governed AWS boundary.
        Returns:
            Tuple[success (bool), pre_state (dict), post_state (dict), request_id (str), summary (str), execution_mode (str)]
        """
        req_id = f"req-{uuid.uuid4().hex[:10]}"
        use_real_aws = force_real_aws or (not settings.AWS_MOCK_MODE)

        # 1. Action Catalog Parameter & Target Validation
        errs = ActionCatalog.validate_action(action_type, target_resource, parameters)
        if errs:
            pre_st = cls.redact_secrets(StatefulMockInfrastructure.get_resource_state(target_resource))
            return False, pre_st, pre_st, req_id, f"Action catalog validation failed: {'; '.join(errs)}", "VALIDATION_FAILED"

        # 2. Simulated Timeout or Failure Testing (for mock testing)
        if simulated_timeout:
            pre_st = cls.redact_secrets(StatefulMockInfrastructure.get_resource_state(target_resource))
            return False, pre_st, pre_st, req_id, "ACTION_TIMEOUT: Request to AWS API timed out after 300 seconds.", "MOCK"

        if simulated_failure:
            pre_st = cls.redact_secrets(StatefulMockInfrastructure.get_resource_state(target_resource))
            return False, pre_st, pre_st, req_id, "AWS API returned UnauthorizedOperation / ResourceInUseException failure.", "MOCK"

        # 3. Real AWS Execution Path (when AWS_MOCK_MODE=False or force_real_aws=True)
        if use_real_aws:
            return cls._execute_real_aws(
                action_type=action_type,
                target_resource=target_resource,
                parameters=parameters,
                idempotency_key=idempotency_key,
                is_compensation=is_compensation,
                req_id=req_id
            )

        # 4. Mock Execution Path (when AWS_MOCK_MODE=True)
        raw_pre, raw_post = StatefulMockInfrastructure.apply_mutation(target_resource, action_type, parameters)
        pre_state = cls.redact_secrets(raw_pre)
        post_state = cls.redact_secrets(raw_post)
        summary = f"[MOCK] Successfully executed typed action '{action_type}' on target '{target_resource}'."
        return True, pre_state, post_state, req_id, summary, "MOCK"

    @classmethod
    def _execute_real_aws(
        cls,
        action_type: str,
        target_resource: str,
        parameters: Dict[str, Any],
        idempotency_key: str,
        is_compensation: bool,
        req_id: str
    ) -> Tuple[bool, Dict[str, Any], Dict[str, Any], str, str, str]:
        """
        Executes real AWS API call using configured AWS credentials.
        Never falls back to SIMULATED_SUCCESS on real AWS failure.
        """
        region = settings.AWS_REGION or "us-east-1"
        sg_id = cls.extract_security_group_id(target_resource, parameters)
        protocol = str(parameters.get("protocol", "tcp")).lower()
        port = int(parameters.get("port", 22))
        cidr_block = str(parameters.get("cidr_block", "0.0.0.0/0"))
        direction = str(parameters.get("direction", "ingress")).lower()

        logger.info(f"[AWSActionExecutor] REAL AWS MUTATION: {action_type} on SG '{sg_id}' in region '{region}' (is_compensation={is_compensation})")

        try:
            session_kwargs = {"region_name": region}
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                session_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                session_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

            ec2_client = boto3.client("ec2", **session_kwargs)

            # Step A: Capture Pre-State
            pre_state = {}
            try:
                desc = ec2_client.describe_security_groups(GroupIds=[sg_id])
                if desc.get("SecurityGroups"):
                    sg_data = desc["SecurityGroups"][0]
                    pre_state = {
                        "security_group_id": sg_data.get("GroupId"),
                        "group_name": sg_data.get("GroupName"),
                        "vpc_id": sg_data.get("VpcId"),
                        "ip_permissions": sg_data.get("IpPermissions", []),
                        "ip_permissions_egress": sg_data.get("IpPermissionsEgress", [])
                    }
            except ClientError as e:
                logger.error(f"[AWSActionExecutor] Failed to capture pre-state for SG '{sg_id}': {e}")
                err_code = e.response.get("Error", {}).get("Code", "UNKNOWN")
                err_msg = e.response.get("Error", {}).get("Message", str(e))
                return False, {}, {}, req_id, f"AWS Pre-state capture failed [{err_code}]: {err_msg}", "AWS_REAL"

            # Step B: Perform Mutation
            ip_permissions = [{
                "IpProtocol": protocol,
                "FromPort": port,
                "ToPort": port,
                "IpRanges": [{"CidrIp": cidr_block}]
            }]

            if is_compensation or direction == "ingress_add" or parameters.get("authorize", False):
                # Authorize rule (compensation / add)
                try:
                    ec2_client.authorize_security_group_ingress(
                        GroupId=sg_id,
                        IpPermissions=ip_permissions
                    )
                except ClientError as e:
                    err_code = e.response.get("Error", {}).get("Code", "")
                    if err_code == "InvalidPermission.Duplicate":
                        logger.info(f"[AWSActionExecutor] Rule already exists on SG '{sg_id}' (Idempotent authorization).")
                    else:
                        raise e
            else:
                # Revoke rule (remediation / remove)
                try:
                    ec2_client.revoke_security_group_ingress(
                        GroupId=sg_id,
                        IpPermissions=ip_permissions
                    )
                except ClientError as e:
                    err_code = e.response.get("Error", {}).get("Code", "")
                    if err_code == "InvalidPermission.NotFound":
                        logger.info(f"[AWSActionExecutor] Rule not found on SG '{sg_id}' (Idempotent revocation).")
                    else:
                        raise e

            # Step C: Capture Post-State
            post_state = {}
            desc_post = ec2_client.describe_security_groups(GroupIds=[sg_id])
            if desc_post.get("SecurityGroups"):
                sg_post = desc_post["SecurityGroups"][0]
                post_state = {
                    "security_group_id": sg_post.get("GroupId"),
                    "group_name": sg_post.get("GroupName"),
                    "vpc_id": sg_post.get("VpcId"),
                    "ip_permissions": sg_post.get("IpPermissions", []),
                    "ip_permissions_egress": sg_post.get("IpPermissionsEgress", [])
                }

            summary = f"[AWS_REAL] Successfully executed real AWS mutation '{action_type}' on '{sg_id}' (protocol={protocol}, port={port}, cidr={cidr_block})."
            return True, cls.redact_secrets(pre_state), cls.redact_secrets(post_state), req_id, summary, "AWS_REAL"

        except NoCredentialsError as e:
            msg = "REAL AWS INTEGRATION BLOCKED: AWS credentials unavailable in environment."
            logger.error(f"[AWSActionExecutor] {msg}")
            return False, {}, {}, req_id, msg, "AWS_REAL"

        except ClientError as e:
            err_code = e.response.get("Error", {}).get("Code", "UNKNOWN")
            err_msg = e.response.get("Error", {}).get("Message", str(e))
            msg = f"AWS ClientError [{err_code}]: {err_msg}"
            logger.error(f"[AWSActionExecutor] Real AWS call failed: {msg}")
            return False, {}, {}, req_id, msg, "AWS_REAL"

        except Exception as e:
            msg = f"AWS Execution Exception: {str(e)}"
            logger.error(f"[AWSActionExecutor] Real AWS execution failed: {msg}")
            return False, {}, {}, req_id, msg, "AWS_REAL"

    @classmethod
    def compensate_action(
        cls,
        action_type: str,
        target_resource: str,
        rollback_parameters: Dict[str, Any],
        force_real_aws: bool = False
    ) -> Tuple[bool, Dict[str, Any], Dict[str, Any], str, str]:
        """
        Executes reverse compensation for an action.
        """
        req_id = f"req-comp-{uuid.uuid4().hex[:8]}"
        rb_action_type = rollback_parameters.get("action_type", action_type)
        params = rollback_parameters.get("parameters", rollback_parameters)

        success, pre_st, post_st, _, summary, mode = cls.execute_action(
            action_type=rb_action_type,
            target_resource=target_resource,
            parameters=params,
            idempotency_key=f"comp-{uuid.uuid4().hex[:8]}",
            is_compensation=True,
            force_real_aws=force_real_aws
        )
        return success, pre_st, post_st, summary, mode
