"""Shared utility functions for the web backend."""

import re

from fastapi import HTTPException

from web.backend.models import RunRecord

UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


def validate_run_id(run_id: str) -> str:
    """Validate that run_id is a valid UUID format. Raises HTTPException 400 if not."""
    if not UUID_PATTERN.match(run_id):
        raise HTTPException(status_code=400, detail="Invalid run_id format")
    return run_id


def build_run_record(run_data: dict) -> RunRecord:
    """
    Build a RunRecord model from a raw database row dictionary.

    Args:
        run_data: Dictionary from RunHistoryManager.get_run() or list_runs().

    Returns:
        RunRecord: Validated Pydantic model.
    """
    return RunRecord(
        id=run_data.get("id", ""),
        status=run_data.get("status", "pending"),
        keywords=run_data.get("keywords", []),
        created_at=run_data.get("created_at", ""),
        completed_at=run_data.get("completed_at"),
        report_markdown=run_data.get("report_markdown"),
        stats=run_data.get("stats"),
        error_message=run_data.get("error_message"),
    )
