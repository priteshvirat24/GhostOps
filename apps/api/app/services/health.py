from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import check_db_health
from app.integrations.aws import MockCloudWatchAdapter
from app.schemas.health import HealthResponse

class HealthService:
    @staticmethod
    def get_health_status(db: Session) -> HealthResponse:
        db_ok = check_db_health()
        cw = MockCloudWatchAdapter()
        alarms_count = len(cw.get_alarms())

        return HealthResponse(
            status="ok" if db_ok else "degraded",
            environment=settings.ENVIRONMENT,
            database_connected=db_ok,
            aws_mock_mode=settings.AWS_MOCK_MODE,
            system_time=datetime.now(timezone.utc).isoformat(),
            details={
                "project": settings.PROJECT_NAME,
                "bedrock_model": settings.BEDROCK_MODEL_ID,
                "mock_cloudwatch_alarms_count": alarms_count,
            }
        )
