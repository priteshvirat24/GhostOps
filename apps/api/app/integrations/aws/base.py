from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class CloudWatchAdapter(ABC):
    @abstractmethod
    def get_alarms(self, state_value: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch CloudWatch alarms."""
        pass

    @abstractmethod
    def get_metric_data(self, namespace: str, metric_name: str, instance_id: str) -> List[Dict[str, Any]]:
        """Fetch CloudWatch metric statistics."""
        pass

class CloudTrailAdapter(ABC):
    @abstractmethod
    def lookup_events(self, lookup_attributes: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Fetch CloudTrail audit log events."""
        pass

class AWSConfigAdapter(ABC):
    @abstractmethod
    def get_resource_config_history(self, resource_id: str) -> List[Dict[str, Any]]:
        """Fetch point-in-time infrastructure configuration history."""
        pass

    @abstractmethod
    def list_discovered_resources(self, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List active resources from AWS Config snapshot."""
        pass

class EventBridgeAdapter(ABC):
    @abstractmethod
    def publish_event(self, detail_type: str, source: str, detail: Dict[str, Any]) -> str:
        """Publish custom telemetry event to EventBridge bus."""
        pass

class SSMAdapter(ABC):
    @abstractmethod
    def send_command(self, instance_id: str, document_name: str, parameters: Dict[str, Any]) -> str:
        """Execute SSM command document on target EC2 instance."""
        pass

    @abstractmethod
    def get_command_invocation(self, command_id: str, instance_id: str) -> Dict[str, Any]:
        """Fetch execution result status of an SSM command."""
        pass

class LambdaAdapter(ABC):
    @abstractmethod
    def invoke_function(self, function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke AWS Lambda function for serverless remediation or validation."""
        pass

class ECSAdapter(ABC):
    @abstractmethod
    def restart_service(self, cluster: str, service: str) -> Dict[str, Any]:
        """Trigger update/restart on an ECS service."""
        pass

    @abstractmethod
    def describe_services(self, cluster: str, services: List[str]) -> List[Dict[str, Any]]:
        """Fetch ECS service status and task health."""
        pass
