from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware import SlidingWindowRateLimiter, TelemetryMiddleware
from src.api.routes import router
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail-fast production security check
    settings.validate_production_security()
    logger.info("Initializing Enterprise Workforce Multi-Agent Platform [%s]...", settings.app_env)
    yield
    logger.info("Gracefully shutting down Enterprise Workforce Multi-Agent Platform.")


app = FastAPI(
    title="Enterprise Workforce Multi-Agent Orchestrator",
    description=(
        "Autonomous Enterprise Multi-Agent System with Human-in-the-Loop Gateways, "
        "Sandboxed SQL Tools, Deterministic State Graphs, and Cryptographic Audit Ledgers."
    ),
    version="0.1.0",
    lifespan=lifespan
)

# Restricted CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.add_middleware(TelemetryMiddleware)
app.add_middleware(SlidingWindowRateLimiter, max_requests_per_minute=settings.rate_limit_per_minute)

app.include_router(router)
