from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.health import HealthService
from app.schemas.health import HealthResponse
from app.core.config import settings
from app.core.metrics import ApplicationMetricsRegistry

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db)):
    return HealthService.get_health_status(db)

@router.get("/ready")
def get_readiness(db: Session = Depends(get_db)):
    health = HealthService.get_health_status(db)
    if health.status.lower() in ["ok", "healthy", "degraded"]:
        return {"status": "READY", "environment": settings.APP_ENV, "mode": "MOCK" if settings.AWS_MOCK_MODE else "LIVE"}
    return Response(content='{"status": "NOT_READY"}', status_code=status.HTTP_503_SERVICE_UNAVAILABLE, media_type="application/json")

@router.get("/live")
def get_liveness():
    return {"status": "LIVE", "timestamp": "2026-08-18T00:59:00Z"}

@router.get("/metrics")
def get_metrics():
    metrics_text = ApplicationMetricsRegistry.get_metrics_text()
    return Response(content=metrics_text, media_type="text/plain; version=0.0.4; charset=utf-8")
