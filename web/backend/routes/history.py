"""
FastAPI routes for run history.

Provides endpoints to list past monitoring runs with pagination.
"""

import logging

from fastapi import APIRouter, Query

from web.backend.config import DB_PATH
from web.backend.models import RunListResponse
from web.backend.services.run_history import RunHistoryManager
from web.backend.utils import build_run_record

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/", response_model=RunListResponse)
async def list_runs(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> RunListResponse:
    """
    List monitoring runs with pagination, ordered by creation time (newest first).

    Args:
        page: Page number (1-based, default 1).
        limit: Number of items per page (1-100, default 20).

    Returns:
        RunListResponse with paginated run records and total count.
    """
    try:
        history = RunHistoryManager(db_path=DB_PATH)
        result = history.list_runs(page=page, limit=limit)
    except Exception as e:
        logger.error("Database error listing runs: %s", e)
        return RunListResponse(runs=[], total=0, page=page, limit=limit)

    raw_runs = result.get("runs", [])
    total = result.get("total", 0)

    runs = [build_run_record(r) for r in raw_runs]

    logger.debug(
        "Listed runs: page=%d, limit=%d, total=%d, returned=%d",
        page,
        limit,
        total,
        len(runs),
    )

    return RunListResponse(
        runs=runs,
        total=total,
        page=page,
        limit=limit,
    )
