import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.integrations.aws.base import (
    CloudWatchAdapter,
    CloudTrailAdapter,
    AWSConfigAdapter,
    EventBridgeAdapter,
    SSMAdapter,
    LambdaAdapter,
    ECSAdapter,
)
from app.core.logging import logger

MOCK_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "..", "infra", "aws", "mock_data.json"
)

def _load_mock_data() -> Dict[str, Any]:
    try:
        if os.path.exists(MOCK_DATA_PATH):
            with open(MOCK_DATA_PATH, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load mock data file: {e}")
    return {
        "cloudwatch_alarms": [
            {
                "AlarmName": "HighCPUUtilization-EC2-prod-web-01",
                "AlarmDescription": "EC2 instance cpu utilization exceeded 90% threshold",
                "StateValue": "ALARM",
                "MetricName": "CPUUtilization",
                "Namespace": "AWS/EC2",
                "Dimensions": [{"Name": "InstanceId", "Value": "i-0a1b2c3d4e5f6g7h8"}],
                "Timestamp": datetime.now(timezone.utc).isoformat()
            }
        ],
        "cloudtrail_events": [
            {
                "eventTime": datetime.now(timezone.utc).isoformat(),
                "eventName": "AuthorizeSecurityGroupIngress",
                "eventSource": "ec2.amazonaws.com",
                "userIdentity": {"arn": "arn:aws:iam::123456789012:user/devops-engineer"},
                "requestParameters": {"groupId": "sg-0123456789abcdef0"}
            }
        ],
        "aws_config_snapshots": [
            {
                "resourceId": "i-0a1b2c3d4e5f6g7h8",
                "resourceType": "AWS::EC2::Instance",
                "arn": "arn:aws:ec2:us-east-1:123456789012:instance/i-0a1b2c3d4e5f6g7h8",
                "configuration": {"instanceType": "t3.medium", "state": {"name": "running"}},
                "tags": {"Environment": "production", "Service": "web-frontend"}
            }
        ]
    }

class MockCloudWatchAdapter(CloudWatchAdapter):
    def __init__(self):
        self.data = _load_mock_data()

    def get_alarms(self, state_value: Optional[str] = None) -> List[Dict[str, Any]]:
        alarms = self.data.get("cloudwatch_alarms", [])
        if state_value:
            return [a for a in alarms if a.get("StateValue") == state_value]
        return alarms

    def get_metric_data(self, namespace: str, metric_name: str, instance_id: str) -> List[Dict[str, Any]]:
        return [
            {"Timestamp": datetime.now(timezone.utc).isoformat(), "Value": 94.5, "Unit": "Percent"}
        ]

class MockCloudTrailAdapter(CloudTrailAdapter):
    def __init__(self):
        self.data = _load_mock_data()

    def lookup_events(self, lookup_attributes: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        return self.data.get("cloudtrail_events", [])

class MockAWSConfigAdapter(AWSConfigAdapter):
    def __init__(self):
        self.data = _load_mock_data()

    def get_resource_config_history(self, resource_id: str) -> List[Dict[str, Any]]:
        snapshots = self.data.get("aws_config_snapshots", [])
        return [s for s in snapshots if s.get("resourceId") == resource_id]

    def list_discovered_resources(self, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        snapshots = self.data.get("aws_config_snapshots", [])
        if resource_type:
            return [s for s in snapshots if s.get("resourceType") == resource_type]
        return snapshots

class MockEventBridgeAdapter(EventBridgeAdapter):
    def publish_event(self, detail_type: str, source: str, detail: Dict[str, Any]) -> str:
        event_id = f"evt-{uuid.uuid4()}"
        logger.info(f"[MOCK EventBridge] Event Published ({event_id}): {detail_type} from {source}")
        return event_id

class MockSSMAdapter(SSMAdapter):
    def send_command(self, instance_id: str, document_name: str, parameters: Dict[str, Any]) -> str:
        cmd_id = f"cmd-{uuid.uuid4()}"
        logger.info(f"[MOCK SSM] Sent {document_name} to {instance_id} (Cmd ID: {cmd_id})")
        return cmd_id

    def get_command_invocation(self, command_id: str, instance_id: str) -> Dict[str, Any]:
        return {
            "CommandId": command_id,
            "InstanceId": instance_id,
            "Status": "Success",
            "Output": "[MOCK SSM Output] Command completed cleanly with exit code 0.",
            "StandardErrorContent": ""
        }

class MockLambdaAdapter(LambdaAdapter):
    def invoke_function(self, function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[MOCK Lambda] Invoked {function_name}")
        return {
            "StatusCode": 200,
            "ExecutedVersion": "$LATEST",
            "Payload": {"status": "SUCCESS", "message": f"Lambda {function_name} executed mock validation."}
        }

class MockECSAdapter(ECSAdapter):
    def restart_service(self, cluster: str, service: str) -> Dict[str, Any]:
        logger.info(f"[MOCK ECS] Restarted service {service} in cluster {cluster}")
        return {
            "service": service,
            "cluster": cluster,
            "desiredCount": 2,
            "runningCount": 2,
            "status": "ACTIVE"
        }

    def describe_services(self, cluster: str, services: List[str]) -> List[Dict[str, Any]]:
        return [
            {
                "serviceName": s,
                "clusterArn": f"arn:aws:ecs:us-east-1:123456789012:cluster/{cluster}",
                "status": "ACTIVE",
                "runningCount": 2,
                "desiredCount": 2
            } for s in services
        ]
