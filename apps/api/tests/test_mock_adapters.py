from app.integrations.aws import (
    MockCloudWatchAdapter,
    MockCloudTrailAdapter,
    MockAWSConfigAdapter,
    MockEventBridgeAdapter,
    MockSSMAdapter,
    MockLambdaAdapter,
    MockECSAdapter,
)
from app.agents import MockBedrockProvider

def test_mock_cloudwatch():
    cw = MockCloudWatchAdapter()
    alarms = cw.get_alarms()
    assert isinstance(alarms, list)
    assert len(alarms) > 0
    alarm = alarms[0]
    assert "AlarmName" in alarm

def test_mock_cloudtrail():
    ct = MockCloudTrailAdapter()
    events = ct.lookup_events()
    assert isinstance(events, list)
    assert len(events) > 0

def test_mock_aws_config():
    config = MockAWSConfigAdapter()
    resources = config.list_discovered_resources()
    assert isinstance(resources, list)
    assert len(resources) > 0

def test_mock_eventbridge():
    eb = MockEventBridgeAdapter()
    event_id = eb.publish_event("TestAlarmTriggered", "GhostOps.Sentinel", {"alarm": "CPU"})
    assert event_id.startswith("evt-")

def test_mock_ssm():
    ssm = MockSSMAdapter()
    cmd_id = ssm.send_command("i-12345", "AWS-RunShellScript", {"commands": ["ls -la"]})
    assert cmd_id.startswith("cmd-")
    result = ssm.get_command_invocation(cmd_id, "i-12345")
    assert result["Status"] == "Success"

def test_mock_bedrock_provider():
    provider = MockBedrockProvider()
    completion = provider.generate_completion("Analyze telemetry logs")
    assert "GhostOps Analysis Summary" in completion
    embedding = provider.generate_embedding("EC2 CPU metric payload")
    assert len(embedding) == 1536
    assert isinstance(embedding[0], float)
