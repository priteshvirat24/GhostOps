import os
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    GhostOps Stage 10 Environment-Driven Production Configuration.
    Validates mandatory settings at startup and prevents silent mock fallbacks in production mode.
    """
    PROJECT_NAME: str = "GhostOps System of Record & Autonomous Memory Engine"
    APP_NAME: str = "GhostOps System of Record & Autonomous Memory Engine"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", description="development | test | production")
    APP_ENV: str = Field(default="development", description="development | test | production")

    # DB Configuration
    DATABASE_URL: str = Field(default="sqlite:///./ghostops_local.db", description="CockroachDB PostgreSQL or SQLite URL")

    # Execution Modes
    AWS_MOCK_MODE: bool = Field(default=True, description="True for isolated mock mode, False for live AWS execution")
    BEDROCK_MOCK_MODE: bool = Field(default=True, description="True for mock embeddings/LLM, False for live AWS Bedrock")

    # AWS Credentials
    AWS_REGION: str = Field(default="us-east-1", description="AWS Target Region")
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    # CORS
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://127.0.0.1:3000"])

    # Vector & Retrieval Settings
    MINIMUM_PLAN_CONFIDENCE: float = 0.60
    VECTOR_WEIGHT: float = 0.40
    STRUCTURED_WEIGHT: float = 0.30
    OUTCOME_WEIGHT: float = 0.15
    REMEDIATION_OUTCOME_WEIGHT: float = 0.15
    STALENESS_WEIGHT: float = 0.15
    TRUST_WEIGHT: float = 0.10
    COMPATIBILITY_WEIGHT: float = 0.10
    STALENESS_DECAY_RATE: float = 0.05
    STALENESS_DECAY_HALF_LIFE_DAYS: float = 30.0
    EMBEDDING_DIMENSION: int = 1536
    COCKROACH_VECTOR_ENABLED: bool = True
    RETRIEVAL_STRUCTURED_POOL_SIZE: int = 50
    RETRIEVAL_VECTOR_POOL_SIZE: int = 50

    # Sentinel Policy Settings
    SENTINEL_ENABLED: bool = True
    SENTINEL_POLL_INTERVAL_SECONDS: int = 30

    # Safety, Timeouts & Budgets
    EXECUTION_TIMEOUT_SECONDS: int = 300
    MAX_SAGA_RETRIES: int = 3
    INVESTIGATION_BUDGET_MAX_STEPS: int = 10
    REPLAY_BUDGET_MAX_STEPS: int = 10
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 120
    REQUEST_TIMEOUT_SECONDS: int = 30
    PLAN_EXPIRATION_HOURS: int = 24
    EXECUTION_LOCK_EXPIRATION_SECONDS: int = 600
    LOG_LEVEL: str = "INFO"

    @field_validator("APP_ENV", "ENVIRONMENT")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        valid_envs = ["development", "test", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"APP_ENV must be one of {valid_envs}")
        return v.lower()

    def validate_production_configuration(self):
        """
        Fail-fast startup validation for production mode.
        Guarantees production mode never silently runs with mock infrastructure or missing secrets.
        """
        if self.APP_ENV == "production" or self.ENVIRONMENT == "production":
            if self.AWS_MOCK_MODE:
                raise ValueError("PRODUCTION ERROR: AWS_MOCK_MODE must be False in production environment.")
            if self.BEDROCK_MOCK_MODE:
                raise ValueError("PRODUCTION ERROR: BEDROCK_MOCK_MODE must be False in production environment.")
            if not self.DATABASE_URL or "sqlite" in self.DATABASE_URL.lower():
                raise ValueError("PRODUCTION ERROR: Production requires a real CockroachDB PostgreSQL DATABASE_URL.")
            if not self.AWS_ACCESS_KEY_ID or not self.AWS_SECRET_ACCESS_KEY:
                raise ValueError("PRODUCTION ERROR: AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) are required in production.")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

settings = Settings()
# Execute startup validation
try:
    settings.validate_production_configuration()
except ValueError as e:
    if settings.APP_ENV == "production" or settings.ENVIRONMENT == "production":
        raise e
