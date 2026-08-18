import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

class APIErrorResponse(BaseModel):
    error_code: str
    message: str
    request_id: str
    timestamp: str
    details: Dict[str, Any] = {}

class GhostOpsException(Exception):
    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

async def ghostops_exception_handler(request: Request, exc: GhostOpsException) -> JSONResponse:
    req_id = getattr(request.state, "request_id", f"req-{uuid.uuid4().hex[:8]}")
    payload = APIErrorResponse(
        error_code=exc.error_code,
        message=exc.message,
        request_id=req_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        details=exc.details
    )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

async def global_generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    req_id = getattr(request.state, "request_id", f"req-{uuid.uuid4().hex[:8]}")

    # Standardize HTTPExceptions if raised by FastAPI framework
    if isinstance(exc, HTTPException):
        payload = APIErrorResponse(
            error_code="HTTP_ERROR",
            message=str(exc.detail),
            request_id=req_id,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

    # Generic internal unhandled errors (hide stack trace & SQL statements from clients)
    payload = APIErrorResponse(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected system error occurred. Please contact ops administrator.",
        request_id=req_id,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload.model_dump())
