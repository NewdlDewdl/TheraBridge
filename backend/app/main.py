"""
TherapyBridge Backend API
FastAPI application for therapy session management and AI note extraction
"""
import os
import time
import logging
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
from sqlalchemy import text
from openai import AsyncOpenAI

from app.database import init_db, close_db, engine
from app.routers import sessions, patients, cleanup
from app.auth.router import router as auth_router
from app.middleware.rate_limit import limiter, custom_rate_limit_handler
from app.middleware.error_handler import register_exception_handlers
from app.middleware.correlation_id import CorrelationIdMiddleware
from app.logging_config import setup_logging
from app.services.cleanup import run_startup_cleanup

load_dotenv()

# Configure structured logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
JSON_LOGS = os.getenv("JSON_LOGS", "false").lower() in ("true", "1", "yes")
setup_logging(log_level=LOG_LEVEL, json_format=JSON_LOGS)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting TherapyBridge API")
    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down TherapyBridge API")
    await close_db()
    logger.info("Database connections closed")


# Security: Get debug mode from environment (defaults to False to prevent PHI exposure)
# WARNING: Enabling debug mode will expose Protected Health Information (PHI) in error messages.
# NEVER enable debug mode in production environments.
DEBUG_MODE = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

# Create FastAPI app
app = FastAPI(
    title="TherapyBridge API",
    description="AI-powered therapy session management and note extraction",
    version="1.0.0",
    lifespan=lifespan,
    debug=DEBUG_MODE  # CRITICAL: Must be False in production to protect patient PHI
)

# Configure rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

# Register global exception handlers
register_exception_handlers(app)

# Correlation ID middleware (MUST be first to ensure request ID available everywhere)
# This middleware:
# - Accepts X-Request-ID header from clients/proxies
# - Generates UUID if no ID provided
# - Stores ID in context variable for logging and tracing
# - Adds X-Request-ID to response headers
app.add_middleware(CorrelationIdMiddleware)

# CORS middleware (allow frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],  # Allow frontend to read request ID
)

# Include routers
app.include_router(auth_router, prefix="/api/v1", tags=["authentication"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(patients.router, prefix="/api/patients", tags=["Patients"])


@app.get("/")
async def root():
    """Basic service info endpoint"""
    return {
        "service": "TherapyBridge API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check(response: Response):
    """
    Comprehensive health check endpoint

    Tests:
    - Database connectivity and query execution
    - Database connection pool status
    - OpenAI API connectivity (lightweight check)

    Returns 200 if all services healthy, 503 if any service is degraded
    """
    health_status = {
        "status": "healthy",
        "timestamp": int(time.time()),
        "checks": {}
    }

    overall_healthy = True

    # Check 1: Database connectivity
    try:
        start = time.time()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_response_time = round((time.time() - start) * 1000, 2)

        # Check connection pool status
        pool_status = {
            "size": engine.pool.size(),
            "checked_in": engine.pool.checkedin(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
        }

        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": db_response_time,
            "pool": pool_status
        }
    except Exception as e:
        overall_healthy = False
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # Check 2: OpenAI API connectivity (lightweight - just check if client can be initialized)
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            health_status["checks"]["openai"] = {
                "status": "degraded",
                "message": "API key not configured"
            }
        else:
            # Just verify client can be created (doesn't make actual API call)
            client = AsyncOpenAI(api_key=openai_api_key)
            health_status["checks"]["openai"] = {
                "status": "healthy",
                "message": "Client initialized"
            }
    except Exception as e:
        # Don't fail overall health for OpenAI issues (it's not critical for basic operations)
        health_status["checks"]["openai"] = {
            "status": "degraded",
            "error": str(e)
        }

    # Set overall status and HTTP status code
    if not overall_healthy:
        health_status["status"] = "unhealthy"
        response.status_code = 503

    return health_status


@app.get("/ready")
async def readiness_check(response: Response):
    """
    Kubernetes readiness probe endpoint

    Checks if the service is ready to accept traffic.
    Tests database connectivity only (critical dependency).

    Returns 200 if ready, 503 if not ready
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        response.status_code = 503
        return {
            "status": "not_ready",
            "reason": "database_unavailable",
            "error": str(e)
        }


@app.get("/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint

    Simple check to verify the application is running and not deadlocked.
    Does not test external dependencies.

    Always returns 200 unless the application is completely unresponsive.
    """
    return {
        "status": "alive",
        "timestamp": int(time.time())
    }
