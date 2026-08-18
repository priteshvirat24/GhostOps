import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple, Optional, List
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

from app.schemas.verification import SignalStatus, SignalVerificationResult
from app.core.config import settings
from app.core.logging import logger

class AWSVerificationTelemetryReader:
    """
    Independent AWS Telemetry and Infrastructure State Reader for GhostOps Stage 7.
    Strictly read-only boundary.
    Fetches independent verification signals from:
    1. EC2 Security Group readback (describe_security_groups)
    2. CloudWatch Metric Data (get_metric_data / get_metric_statistics)
    Differentiates between AWS_REAL and MOCK modes.
    """

    ALLOWED_CLOUDWATCH_METRICS = {
        "ErrorRate",
        "HTTPCode_Target_5XX_Count",
        "TargetResponseTime",
        "CPUUtilization",
        "NetworkIn",
        "NetworkOut",
        "ActiveConnectionCount",
        "DatabaseConnections"
    }

    @classmethod
    def extract_security_group_id(cls, target_resource: str) -> str:
        if "security-group/" in target_resource:
            return target_resource.split("security-group/")[-1]
        elif target_resource.startswith("sg-"):
            return target_resource
        return target_resource or "sg-0123456789abcdef0"

    @classmethod
    def verify_security_group_state(
        cls,
        target_resource: str,
        expected_revoked_port: int = 22,
        expected_revoked_cidr: str = "0.0.0.0/0",
        force_real_aws: bool = False,
        simulated_infra_failure: bool = False
    ) -> SignalVerificationResult:
        """
        Independently verifies that the target security group ingress rule has been revoked.
        Does NOT rely on ExecutionAgent's return output.
        """
        use_real_aws = force_real_aws or (not settings.AWS_MOCK_MODE)
        mode = "AWS_REAL" if use_real_aws else "MOCK"
        sg_id = cls.extract_security_group_id(target_resource)

        if simulated_infra_failure:
            return SignalVerificationResult(
                signal_name="ec2_security_group_rule_revocation",
                signal_type="INFRASTRUCTURE_STATE",
                source="EC2.DescribeSecurityGroups",
                observed_value={"port": expected_revoked_port, "cidr_block": expected_revoked_cidr, "rule_present": True},
                expected_condition=f"Ingress port {expected_revoked_port} ({expected_revoked_cidr}) must be absent",
                status=SignalStatus.FAIL,
                verification_mode=mode,
                evidence_ref=f"ec2-sg-read-{sg_id}",
                error_message=f"Independent readback shows port {expected_revoked_port} is still present in {sg_id}."
            )

        if use_real_aws:
            region = settings.AWS_REGION or "us-east-1"
            session_kwargs = {"region_name": region}
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                session_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                session_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

            try:
                ec2_client = boto3.client("ec2", **session_kwargs)
                desc = ec2_client.describe_security_groups(GroupIds=[sg_id])
                if not desc.get("SecurityGroups"):
                    return SignalVerificationResult(
                        signal_name="ec2_security_group_rule_revocation",
                        signal_type="INFRASTRUCTURE_STATE",
                        source="EC2.DescribeSecurityGroups",
                        observed_value=None,
                        expected_condition=f"Security group {sg_id} must exist and port {expected_revoked_port} absent",
                        status=SignalStatus.FAIL,
                        verification_mode="AWS_REAL",
                        error_message=f"Security group '{sg_id}' not found in AWS region '{region}'."
                    )

                sg_data = desc["SecurityGroups"][0]
                ip_permissions = sg_data.get("IpPermissions", [])

                # Check if matching rule is present
                rule_found = False
                for perm in ip_permissions:
                    from_port = perm.get("FromPort")
                    to_port = perm.get("ToPort")
                    if from_port is not None and to_port is not None:
                        if from_port <= expected_revoked_port <= to_port:
                            for ip_range in perm.get("IpRanges", []):
                                if ip_range.get("CidrIp") == expected_revoked_cidr:
                                    rule_found = True
                                    break

                status = SignalStatus.FAIL if rule_found else SignalStatus.PASS
                obs_val = {
                    "security_group_id": sg_id,
                    "rule_present": rule_found,
                    "active_ingress_rules_count": len(ip_permissions)
                }

                return SignalVerificationResult(
                    signal_name="ec2_security_group_rule_revocation",
                    signal_type="INFRASTRUCTURE_STATE",
                    source="EC2.DescribeSecurityGroups",
                    observed_value=obs_val,
                    expected_condition=f"Port {expected_revoked_port} ({expected_revoked_cidr}) absent",
                    status=status,
                    verification_mode="AWS_REAL",
                    evidence_ref=f"ec2-sg-read-{sg_id}",
                    error_message=None if not rule_found else f"Security group {sg_id} still contains unauthorized ingress rule for port {expected_revoked_port}."
                )

            except NoCredentialsError:
                msg = "REAL AWS VERIFICATION BLOCKED: AWS credentials unavailable in environment."
                logger.error(f"[AWSVerificationTelemetryReader] {msg}")
                return SignalVerificationResult(
                    signal_name="ec2_security_group_rule_revocation",
                    signal_type="INFRASTRUCTURE_STATE",
                    source="EC2.DescribeSecurityGroups",
                    observed_value=None,
                    expected_condition=f"Port {expected_revoked_port} ({expected_revoked_cidr}) absent",
                    status=SignalStatus.BLOCKED,
                    verification_mode="AWS_REAL",
                    error_message=msg
                )

            except ClientError as e:
                err_code = e.response.get("Error", {}).get("Code", "UNKNOWN")
                err_msg = e.response.get("Error", {}).get("Message", str(e))
                msg = f"AWS ClientError [{err_code}]: {err_msg}"
                logger.error(f"[AWSVerificationTelemetryReader] {msg}")
                return SignalVerificationResult(
                    signal_name="ec2_security_group_rule_revocation",
                    signal_type="INFRASTRUCTURE_STATE",
                    source="EC2.DescribeSecurityGroups",
                    observed_value=None,
                    expected_condition=f"Port {expected_revoked_port} ({expected_revoked_cidr}) absent",
                    status=SignalStatus.BLOCKED,
                    verification_mode="AWS_REAL",
                    error_message=msg
                )

            except Exception as e:
                msg = f"AWS Verification Exception: {str(e)}"
                logger.error(f"[AWSVerificationTelemetryReader] {msg}")
                return SignalVerificationResult(
                    signal_name="ec2_security_group_rule_revocation",
                    signal_type="INFRASTRUCTURE_STATE",
                    source="EC2.DescribeSecurityGroups",
                    observed_value=None,
                    expected_condition=f"Port {expected_revoked_port} ({expected_revoked_cidr}) absent",
                    status=SignalStatus.BLOCKED,
                    verification_mode="AWS_REAL",
                    error_message=msg
                )

        # MOCK Execution Mode
        from app.services.execution.mock_infrastructure import StatefulMockInfrastructure
        curr_state = StatefulMockInfrastructure.get_resource_state(target_resource)
        rules = curr_state.get("security_group_ingress_rules", [])
        rule_found = any(r.get("port") == expected_revoked_port for r in rules)

        status = SignalStatus.FAIL if rule_found else SignalStatus.PASS
        obs_val = {
            "security_group_id": sg_id,
            "rule_present": rule_found,
            "active_ingress_rules_count": len(rules)
        }

        return SignalVerificationResult(
            signal_name="ec2_security_group_rule_revocation",
            signal_type="INFRASTRUCTURE_STATE",
            source="EC2.DescribeSecurityGroups",
            observed_value=obs_val,
            expected_condition=f"Port {expected_revoked_port} ({expected_revoked_cidr}) absent",
            status=status,
            verification_mode="MOCK",
            evidence_ref=f"mock-sg-read-{sg_id}",
            error_message=None if not rule_found else f"[MOCK] Target security group still contains port {expected_revoked_port}."
        )

    @classmethod
    def read_cloudwatch_metric(
        cls,
        service_name: str,
        metric_name: str = "ErrorRate",
        window_minutes: int = 15,
        threshold: float = 1.0,
        comparison_operator: str = "LessThanThreshold",
        force_real_aws: bool = False,
        mock_metric_value: Optional[float] = None,
        mock_blocked: bool = False
    ) -> SignalVerificationResult:
        """
        Independently reads CloudWatch metric telemetry for application behavior verification.
        Does NOT rely on ExecutionAgent's self-evaluation.
        """
        use_real_aws = force_real_aws or (not settings.AWS_MOCK_MODE)
        mode = "AWS_REAL" if use_real_aws else "MOCK"

        if mock_blocked:
            return SignalVerificationResult(
                signal_name=f"cloudwatch_{metric_name.lower()}",
                signal_type="APPLICATION_TELEMETRY",
                source="CloudWatch.GetMetricData",
                observed_value=None,
                expected_condition=f"{metric_name} {comparison_operator} {threshold}",
                status=SignalStatus.BLOCKED,
                observation_window=f"{window_minutes}m",
                verification_mode=mode,
                error_message="CloudWatch metric telemetry unavailable / blocked."
            )

        if metric_name not in cls.ALLOWED_CLOUDWATCH_METRICS:
            return SignalVerificationResult(
                signal_name=f"cloudwatch_{metric_name.lower()}",
                signal_type="APPLICATION_TELEMETRY",
                source="CloudWatch.GetMetricData",
                observed_value=None,
                expected_condition=f"{metric_name} in allowlist",
                status=SignalStatus.BLOCKED,
                verification_mode=mode,
                error_message=f"Metric '{metric_name}' is not in authorized CloudWatch metrics allowlist."
            )

        if use_real_aws:
            region = settings.AWS_REGION or "us-east-1"
            session_kwargs = {"region_name": region}
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                session_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                session_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

            try:
                cw_client = boto3.client("cloudwatch", **session_kwargs)
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(minutes=window_minutes)

                # Fetch real metric statistics
                res = cw_client.get_metric_statistics(
                    Namespace="AWS/ApplicationELB" if "5XX" in metric_name else "AWS/ECS",
                    MetricName=metric_name,
                    Dimensions=[{"Name": "ServiceName", "Value": service_name}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,
                    Statistics=["Average", "Sum", "Maximum"]
                )

                datapoints = res.get("Datapoints", [])
                if not datapoints:
                    return SignalVerificationResult(
                        signal_name=f"cloudwatch_{metric_name.lower()}",
                        signal_type="APPLICATION_TELEMETRY",
                        source="CloudWatch.GetMetricData",
                        observed_value={"datapoints_count": 0, "value": None},
                        expected_condition=f"{metric_name} {comparison_operator} {threshold}",
                        status=SignalStatus.INCONCLUSIVE,
                        observation_window=f"{window_minutes}m",
                        verification_mode="AWS_REAL",
                        error_message=f"No CloudWatch datapoints returned for service '{service_name}' in observation window."
                    )

                latest_dp = sorted(datapoints, key=lambda x: x["Timestamp"])[-1]
                val = float(latest_dp.get("Average") or latest_dp.get("Sum") or latest_dp.get("Maximum") or 0.0)

                passed = (val < threshold) if comparison_operator == "LessThanThreshold" else (val > threshold)
                status = SignalStatus.PASS if passed else SignalStatus.FAIL

                return SignalVerificationResult(
                    signal_name=f"cloudwatch_{metric_name.lower()}",
                    signal_type="APPLICATION_TELEMETRY",
                    source="CloudWatch.GetMetricData",
                    observed_value={"metric": metric_name, "value": val, "unit": latest_dp.get("Unit", "None")},
                    expected_condition=f"{metric_name} {comparison_operator} {threshold}",
                    status=status,
                    observation_window=f"{window_minutes}m",
                    verification_mode="AWS_REAL",
                    evidence_ref=f"cw-metric-{metric_name}-{service_name}"
                )

            except NoCredentialsError:
                msg = "REAL AWS VERIFICATION BLOCKED: AWS credentials unavailable in environment."
                logger.error(f"[AWSVerificationTelemetryReader] {msg}")
                return SignalVerificationResult(
                    signal_name=f"cloudwatch_{metric_name.lower()}",
                    signal_type="APPLICATION_TELEMETRY",
                    source="CloudWatch.GetMetricData",
                    observed_value=None,
                    expected_condition=f"{metric_name} {comparison_operator} {threshold}",
                    status=SignalStatus.BLOCKED,
                    observation_window=f"{window_minutes}m",
                    verification_mode="AWS_REAL",
                    error_message=msg
                )

            except ClientError as e:
                err_code = e.response.get("Error", {}).get("Code", "UNKNOWN")
                err_msg = e.response.get("Error", {}).get("Message", str(e))
                msg = f"AWS ClientError [{err_code}]: {err_msg}"
                logger.error(f"[AWSVerificationTelemetryReader] {msg}")
                return SignalVerificationResult(
                    signal_name=f"cloudwatch_{metric_name.lower()}",
                    signal_type="APPLICATION_TELEMETRY",
                    source="CloudWatch.GetMetricData",
                    observed_value=None,
                    expected_condition=f"{metric_name} {comparison_operator} {threshold}",
                    status=SignalStatus.BLOCKED,
                    observation_window=f"{window_minutes}m",
                    verification_mode="AWS_REAL",
                    error_message=msg
                )

            except Exception as e:
                msg = f"AWS CloudWatch Exception: {str(e)}"
                logger.error(f"[AWSVerificationTelemetryReader] {msg}")
                return SignalVerificationResult(
                    signal_name=f"cloudwatch_{metric_name.lower()}",
                    signal_type="APPLICATION_TELEMETRY",
                    source="CloudWatch.GetMetricData",
                    observed_value=None,
                    expected_condition=f"{metric_name} {comparison_operator} {threshold}",
                    status=SignalStatus.BLOCKED,
                    observation_window=f"{window_minutes}m",
                    verification_mode="AWS_REAL",
                    error_message=msg
                )

        # MOCK Execution Mode
        # Determine value dynamically based on test override or mock state
        val = mock_metric_value if mock_metric_value is not None else 0.35  # Healthy baseline for mock test
        passed = (val < threshold) if comparison_operator == "LessThanThreshold" else (val > threshold)
        status = SignalStatus.PASS if passed else SignalStatus.FAIL

        return SignalVerificationResult(
            signal_name=f"cloudwatch_{metric_name.lower()}",
            signal_type="APPLICATION_TELEMETRY",
            source="CloudWatch.GetMetricData",
            observed_value={"metric": metric_name, "value": val, "unit": "Percent" if "Rate" in metric_name else "Count"},
            expected_condition=f"{metric_name} {comparison_operator} {threshold}",
            status=status,
            observation_window=f"{window_minutes}m",
            verification_mode="MOCK",
            evidence_ref=f"mock-cw-{metric_name}-{service_name}",
            error_message=None if passed else f"[MOCK] Observed {metric_name} ({val}) violated threshold ({threshold})."
        )
