"""
FastAPI routes for report retrieval.

Provides endpoints to fetch detailed reports for completed monitoring runs.
"""

import json
import logging

from fastapi import APIRouter, HTTPException

from web.backend.config import DB_PATH
from web.backend.models import ReportResponse
from web.backend.services.run_history import RunHistoryManager
from web.backend.utils import build_run_record, validate_run_id

from report_generator import (
    classify_posts_by_category,
    compute_category_stats,
    identify_big_fish,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{run_id}", response_model=ReportResponse)
async def get_report(run_id: str) -> ReportResponse:
    """
    Retrieve the detailed report for a specific monitoring run.

    Args:
        run_id: The unique identifier of the monitoring run.

    Returns:
        ReportResponse with run record, analyzed posts, big fish, and category stats.

    Raises:
        HTTPException 400: If run_id is not a valid UUID.
        HTTPException 404: If the run_id does not exist.
        HTTPException 500: If an unexpected error occurs.
    """
    validate_run_id(run_id)

    try:
        history = RunHistoryManager(db_path=DB_PATH)
        run_data = history.get_run(run_id)
    except Exception as e:
        logger.error("Database error fetching run %s: %s", run_id, e)
        raise HTTPException(status_code=500, detail="Database error") from e

    if run_data is None:
        raise HTTPException(status_code=404, detail="Run not found")

    run_record = build_run_record(run_data)

    analyzed_posts = _parse_result_json(run_data.get("result_json"))

    big_fish = None
    category_stats = None

    if analyzed_posts:
        try:
            big_fish = identify_big_fish(analyzed_posts)
            categorized = classify_posts_by_category(analyzed_posts)
            category_stats = compute_category_stats(categorized)
        except Exception as e:
            logger.warning(
                "Failed to compute report analytics for run %s: %s", run_id, e
            )

    return ReportResponse(
        run=run_record,
        analyzed_posts=analyzed_posts,
        big_fish=big_fish,
        category_stats=category_stats,
    )


def _parse_result_json(result_json_str: str | None) -> list[dict] | None:
    """
    Parse the result_json column into a list of analyzed post dicts.

    Args:
        result_json_str: Raw JSON string from the database, or None.

    Returns:
        List of post dicts if parsing succeeds, None otherwise.
    """
    if not result_json_str:
        return None

    try:
        parsed = json.loads(result_json_str)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Failed to parse result_json: %s", e)
        return None

    if isinstance(parsed, list):
        return parsed

    if isinstance(parsed, dict):
        return parsed.get("analyzed_posts")

    return None
