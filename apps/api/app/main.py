from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.core.errors import GhostOpsException, ghostops_exception_handler, global_generic_exception_handler
from app.api.v1.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting GhostOps API Server v0.1.0 in {settings.ENVIRONMENT} mode")
    logger.info(f"AWS Mock Mode: {settings.AWS_MOCK_MODE}")
    logger.info(f"Bedrock Model Target: {settings.BEDROCK_MODEL_ID}")
    yield
    logger.info("Shutting down GhostOps API Server")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="The production memory that survives the engineer - Institutional Memory & Remediation System",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register Exception Handlers
app.add_exception_handler(GhostOpsException, ghostops_exception_handler)
app.add_exception_handler(Exception, global_generic_exception_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 router
app.include_router(api_router, prefix="/api/v1")

# Root health check for container healthchecks
@app.get("/health", tags=["Health"])
def root_health():
    return {"status": "ok", "service": "ghostops-api", "version": "1.0.0"}
