"""
FastAPI application for the Threads monitoring web dashboard.

Provides REST API endpoints for monitoring runs, reports, and history.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from web.backend.config import ALLOWED_ORIGINS, PROJECT_ROOT

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Log server startup and shutdown."""
    logger.info(
        "Threads Monitor API starting up — project_root=%s",
        PROJECT_ROOT,
    )
    yield
    logger.info("Threads Monitor API shutting down")


app = FastAPI(
    title="Threads Monitor API",
    description="Threads social media monitoring system API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware -- use explicit origins from environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# --- Health Check ---

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
    }


# --- Include Routers ---

try:
    from web.backend.routes.monitor import router as monitor_router
    app.include_router(monitor_router, prefix="/api")
    logger.info("Included monitor router")
except ImportError:
    logger.warning("Monitor routes not available yet, skipping", exc_info=True)

try:
    from web.backend.routes.reports import router as reports_router
    app.include_router(reports_router, prefix="/api")
    logger.info("Included reports router")
except ImportError:
    logger.warning("Reports routes not available yet, skipping", exc_info=True)

try:
    from web.backend.routes.history import router as history_router
    app.include_router(history_router, prefix="/api")
    logger.info("Included history router")
except ImportError:
    logger.warning("History routes not available yet, skipping", exc_info=True)
