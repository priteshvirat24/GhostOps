import re
import math
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.logging import logger

class ModelProvider(ABC):
    @abstractmethod
    def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tier: str = "reasoning",  # fast | reasoning | execution
        temperature: float = 0.2
    ) -> str:
        """Generate text completion from LLM model with tier routing."""
        pass

    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for text chunk."""
        pass

class MockBedrockProvider(ModelProvider):
    """
    Mock Bedrock provider for offline execution & testing (§9.3, §22).
    Generates deterministic 1536-dimensional float vector embeddings
    using token-weighted seed hashing so semantically overlapping text produces high cosine similarity.
    """

    def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tier: str = "reasoning",
        temperature: float = 0.2
    ) -> str:
        logger.info(f"[MOCK Bedrock] Generating completion on tier '{tier}' for prompt length: {len(prompt)}")
        if tier == "fast":
            return "Classification: High-severity database connection exhaustion. Routed to Reasoning Tier."
        elif tier == "reasoning":
            is_planner = (
                (system_prompt and "PLANNER" in system_prompt.upper()) or
                "### REMEDIATION PLANNING" in prompt or
                "### INVESTIGATION RESULTS" in prompt or
                "### AUTHORIZED ACTION CATALOG" in prompt
            )
            if is_planner:
                return self._generate_mock_planner_response(prompt, system_prompt)

            is_investigator = (
                (system_prompt and "INVESTIGATOR" in system_prompt.upper()) or
                "### INCIDENT" in prompt or
                ("JSON" in (system_prompt or "").upper() and "hypotheses" in prompt.lower())
            )
            if is_investigator:
                return self._generate_mock_investigator_response(prompt, system_prompt)
            return (
                "GhostOps Analysis Summary & Step-by-Step Reasoning:\n"
                "1. Telemetry observed metric spike and unauthorized port ingress on auth-service.\n"
                "2. Retained raw evidence and reconstructed event timeline.\n"
                "3. Historical precedent #1847 retrieved with 0.91 weighted score.\n"
                "4. Action history preserved including failed remediation attempts."
            )
        else:
            return "Execution tool parameters validated against schema."

    def _generate_mock_planner_response(self, prompt: str, system_prompt: Optional[str]) -> str:
        import json
        # Extract evidence IDs from prompt
        ev_ids = re.findall(r'(?:Evidence ID|Event ID|Supporting Evidence IDs|evidence_id|event_id):\s*([a-zA-Z0-9_\-:, ]+)', prompt, re.IGNORECASE)
        found_ev_ids = []
        for match in ev_ids:
            for item in re.split(r'[, ]+', match):
                clean = item.strip(" '\"[]")
                if clean and clean not in found_ev_ids:
                    found_ev_ids.append(clean)
        if not found_ev_ids:
            found_ev_ids = re.findall(r'\b(?:cw-[a-zA-Z0-9_\-]+|ev-[a-zA-Z0-9_\-]+|hash[a-zA-Z0-9_\-]+|inc-[a-zA-Z0-9_\-]+)\b', prompt)

        # Extract historical precedent ID
        hist_ids = re.findall(r'(?:Historical Precedent ID|historical_incident_id|Precedent ID):\s*([a-zA-Z0-9_\-]+)', prompt, re.IGNORECASE)
        hist_id = hist_ids[0] if hist_ids else "hist-01"

        # Check for DO_NOT_EXECUTE / INAPPLICABLE / low compatibility verdict in prompt
        is_do_not_execute = (
            "do_not_execute" in prompt.lower() or
            "inapplicable" in prompt.lower() or
            "low_compatibility" in prompt.lower() or
            "flagship rejected" in prompt.lower()
        )

        # Check for prompt injection
        if "delete_database_cluster" in prompt or "rm -rf" in prompt:
            return json.dumps({
                "plan_title": "Rejected Remediation Proposal",
                "explanation": "Rejected unauthorized or uncatalogued action request embedded in telemetry.",
                "root_cause": {
                    "statement": "Prompt injection attempt detected.",
                    "hypothesis_id": "H1",
                    "evidence_ids": found_ev_ids[:1]
                },
                "recommended_actions": [],
                "confidence": 0.20,
                "temporal_compatibility": 0.0,
                "requires_human_approval": True,
                "validation_requirements": [],
                "rejection_reasons": ["Detected uncatalogued destructive instruction in prompt/telemetry."],
                "status": "REJECTED"
            })

        if is_do_not_execute:
            return json.dumps({
                "plan_title": "Rejected Historical Remediation Reuse",
                "explanation": f"Historical precedent '{hist_id}' is marked DO_NOT_EXECUTE / INAPPLICABLE due to infrastructure version drift.",
                "root_cause": {
                    "statement": "Investigation identified root cause, but historical remediation cannot be applied safely.",
                    "hypothesis_id": "H1",
                    "evidence_ids": found_ev_ids[:1]
                },
                "recommended_actions": [],
                "confidence": 0.88,
                "temporal_compatibility": 0.20,
                "requires_human_approval": True,
                "validation_requirements": [],
                "rejection_reasons": [f"Precedent '{hist_id}' is INAPPLICABLE / DO_NOT_EXECUTE in current infrastructure environment."],
                "status": "REJECTED"
            })

        # Standard compatible proposal
        target_arn = "arn:aws:ec2:us-east-1:123456789012:security-group/sg-012345"
        output = {
            "plan_title": "Remediation Plan for Connection Pool Exhaustion",
            "explanation": f"Grounded in primary root cause hypothesis and compatible historical precedent {hist_id}. Proposes modifying security group ingress rule to revoke unrestricted SSH port 22 access.",
            "root_cause": {
                "statement": "Unrestricted ingress traffic surge caused database connection pool exhaustion.",
                "hypothesis_id": "H1",
                "evidence_ids": found_ev_ids[:2] if found_ev_ids else ["ev-1"]
            },
            "recommended_actions": [
                {
                    "action_id": "act-1",
                    "action_type": "CHANGE_SECURITY_RULE",
                    "target": target_arn,
                    "parameters": {
                        "security_group_id": "sg-012345",
                        "protocol": "tcp",
                        "port": 22,
                        "cidr_block": "0.0.0.0/0",
                        "direction": "ingress"
                    },
                    "reason": "Revoke unrestricted SSH ingress rule to restore database connection pool stability.",
                    "historical_precedent_ids": [hist_id],
                    "evidence_ids": found_ev_ids[:2] if found_ev_ids else ["ev-1"],
                    "risk_level": "HIGH_RISK",
                    "expected_effect": "Database connection pool utilization decreases below 40% within 120 seconds.",
                    "preconditions": [
                        "Target security group sg-012345 exists",
                        "No active concurrent remediation holds execution lock on sg-012345"
                    ],
                    "failure_conditions": [
                        "Security group API returns UnauthorizedOperation error",
                        "Database connection pool metrics remain above 90% after 300 seconds"
                    ],
                    "rollback_action": {
                        "action_type": "CHANGE_SECURITY_RULE",
                        "target_resource_arn": target_arn,
                        "parameters": {
                            "security_group_id": "sg-012345",
                            "protocol": "tcp",
                            "port": 22,
                            "cidr_block": "10.0.0.0/16",
                            "direction": "ingress"
                        },
                        "reason": "Revert security group ingress to restricted VPC internal CIDR block."
                    },
                    "verification_requirements": [
                        {
                            "check_id": "vcheck-01",
                            "type": "CLOUDWATCH_METRIC",
                            "target": "auth-service",
                            "expected_condition": "DatabaseConnectionPoolUtilization < 40%",
                            "timeout_seconds": 300,
                            "evidence_refs": found_ev_ids[:2] if found_ev_ids else ["ev-1"]
                        }
                    ]
                }
            ],
            "confidence": 0.88,
            "temporal_compatibility": 0.90,
            "requires_human_approval": True,
            "validation_requirements": [
                {
                    "check_id": "vcheck-01",
                    "type": "CLOUDWATCH_METRIC",
                    "target": "auth-service",
                    "expected_condition": "DatabaseConnectionPoolUtilization < 40%",
                    "timeout_seconds": 300,
                    "evidence_refs": found_ev_ids[:2] if found_ev_ids else ["ev-1"]
                }
            ],
            "rejection_reasons": [],
            "status": "PROPOSED"
        }
        return json.dumps(output)

    def _generate_mock_investigator_response(self, prompt: str, system_prompt: Optional[str]) -> str:
        import json
        # Extract real evidence IDs present in the prompt
        ev_ids = re.findall(r'(?:Evidence ID|Event ID|Candidate Incident ID|evidence_id|event_id):\s*([a-zA-Z0-9_\-:]+)', prompt, re.IGNORECASE)
        if not ev_ids:
            # Fallback scan for common ID patterns in prompt
            ev_ids = re.findall(r'\b(?:cw-[a-zA-Z0-9_\-]+|ev-[a-zA-Z0-9_\-]+|hash[a-zA-Z0-9_\-]+|inc-[a-zA-Z0-9_\-]+)\b', prompt)

        # Remove duplicates while preserving order
        seen = set()
        unique_ev_ids = [x for x in ev_ids if not (x in seen or seen.add(x))]

        # Check for contradiction / low-confidence scenarios in prompt
        is_contradictory = "contradict" in prompt.lower() or "disagree" in prompt.lower() or "conflict" in prompt.lower()
        is_low_confidence = "low_confidence" in prompt.lower() or len(unique_ev_ids) == 0

        # Construct evidence citations strictly from retrieved IDs
        h1_evidence = []
        h2_evidence = []

        if unique_ev_ids:
            h1_evidence.append({
                "source": "incident_evidence",
                "record_id": unique_ev_ids[0],
                "claim": "Telemetry data confirms abnormal ingress traffic saturation leading to connection pool exhaustion"
            })
            if len(unique_ev_ids) > 1:
                h2_evidence.append({
                    "source": "incident_evidence",
                    "record_id": unique_ev_ids[1],
                    "claim": "Authentication retry frequency elevated during initial incident window"
                })
        else:
            h1_evidence = []

        h1_conf = 0.35 if is_low_confidence else (0.65 if is_contradictory else 0.88)
        h2_conf = 0.30 if is_low_confidence else (0.60 if is_contradictory else 0.45)

        output = {
            "hypotheses": [
                {
                    "id": "H1",
                    "statement": "Unrestricted ingress traffic surge caused database connection pool exhaustion.",
                    "evidence": h1_evidence,
                    "counter_evidence": ["No kernel OOM process termination logs observed."] if is_contradictory else [],
                    "confidence": h1_conf,
                    "status": "SUPPORTED" if h1_evidence and not is_low_confidence else "PLAUSIBLE",
                    "next_question": "Validate whether security group ingress was modified prior to incident start."
                },
                {
                    "id": "H2",
                    "statement": "Database authentication token expiration created connection retry storm.",
                    "evidence": h2_evidence,
                    "counter_evidence": ["No auth token expiration logs observed in CloudTrail audit."],
                    "confidence": h2_conf,
                    "status": "PLAUSIBLE",
                    "next_question": "Check IAM role token duration and rotation policies."
                }
            ],
            "selected_hypothesis": "H1",
            "disagreement_flag": is_contradictory or (abs(h1_conf - h2_conf) < 0.10),
            "confidence": h1_conf,
            "next_retrieval_query": "search_historical_memory: connection pool exhaustion" if is_low_confidence else None,
            "reasoning_summary": f"Primary supported hypothesis H1 is grounded in {len(h1_evidence)} verified evidence record(s). Competing token expiration hypothesis H2 remains secondary."
        }
        return json.dumps(output)

    def generate_embedding(self, text: str) -> List[float]:
        if not text:
            text = "empty"

        tokens = re.findall(r'\w+', text.lower())
        if not tokens:
            tokens = [text.lower()]

        vec = [0.0] * 1536
        for token in tokens:
            seed_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
            for i in range(1536):
                chunk = hashlib.sha256(f"{seed_hash}:{i}".encode("utf-8")).digest()
                val = (int.from_bytes(chunk[:4], byteorder="big") / 4294967295.0) * 2.0 - 1.0
                vec[i] += val

        magnitude = math.sqrt(sum(v * v for v in vec))
        if magnitude > 0:
            return [round(v / magnitude, 6) for v in vec]
        return vec

class BedrockMantleProvider(ModelProvider):
    """
    Live Amazon Bedrock Mantle provider using Bedrock API Key (§9.3, §22).
    Connects to Amazon Bedrock Mantle OpenAI-compatible endpoints with ultra-low-cost models.
    """

    MODEL_TIERS = {
        "fast": settings.BEDROCK_FAST_MODEL_ID,  # zai.glm-4.7-flash ($0.08 / 1M tokens)
        "reasoning": settings.BEDROCK_MODEL_ID,   # deepseek.v3.2 ($0.74 / 1M tokens)
        "execution": settings.BEDROCK_FAST_MODEL_ID,
    }

    def __init__(self):
        import requests
        self.api_key = settings.BEDROCK_API_KEY
        self.base_url = settings.BEDROCK_MANTLE_ENDPOINT.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        self._mock_fallback = MockBedrockProvider()

    def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tier: str = "reasoning",
        temperature: float = 0.2
    ) -> str:
        model_id = self.MODEL_TIERS.get(tier, self.MODEL_TIERS["reasoning"])
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model_id,
            "messages": messages,
            "max_tokens": 2048 if tier == "reasoning" else 512,
            "temperature": temperature
        }

        try:
            logger.info(f"[Bedrock Mantle] Generating live completion with model '{model_id}' (tier: {tier})")
            response = self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                if content:
                    return content.strip()
            logger.warning(f"[Bedrock Mantle] API returned status {response.status_code}: {response.text[:200]}, falling back to mock generator")
        except Exception as e:
            logger.error(f"[Bedrock Mantle] Error invoking model '{model_id}': {e}, using fallback")

        return self._mock_fallback.generate_completion(prompt, system_prompt=system_prompt, tier=tier, temperature=temperature)

    def generate_embedding(self, text: str) -> List[float]:
        # Bedrock Mantle currently serves chat/completions; semantic embeddings route through deterministic 1536-dim vector generator
        return self._mock_fallback.generate_embedding(text)

class BedrockProvider(ModelProvider):
    """Live Amazon Bedrock multi-tier provider using boto3 runtime (§9.3, §22)."""

    MODEL_TIERS = {
        "fast": "anthropic.claude-3-haiku-20240307-v1:0",
        "reasoning": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "execution": "anthropic.claude-3-haiku-20240307-v1:0",
    }

    def __init__(self):
        import boto3
        self.client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
        self.embedding_model_id = settings.BEDROCK_EMBEDDING_MODEL_ID

    def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tier: str = "reasoning",
        temperature: float = 0.2
    ) -> str:
        import json
        model_id = self.MODEL_TIERS.get(tier, self.MODEL_TIERS["reasoning"])
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048 if tier == "reasoning" else 1024,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_prompt:
            payload["system"] = system_prompt

        response = self.client.invoke_model(
            modelId=model_id,
            body=json.dumps(payload)
        )
        response_body = json.loads(response.get("body").read())
        return response_body["content"][0]["text"]

    def generate_embedding(self, text: str) -> List[float]:
        import json
        payload = {"inputText": text}
        response = self.client.invoke_model(
            modelId=self.embedding_model_id,
            body=json.dumps(payload)
        )
        response_body = json.loads(response.get("body").read())
        return response_body["embedding"]

def get_model_provider() -> ModelProvider:
    if settings.BEDROCK_API_KEY:
        return BedrockMantleProvider()
    if settings.AWS_MOCK_MODE:
        return MockBedrockProvider()
    return BedrockProvider()
