"""Pydantic models for API request/response schemas."""

import enum
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

# Strict keyword pattern: alphanumeric, CJK, spaces, basic punctuation
_ALLOWED_KEYWORD_RE = re.compile(
    r"^[\w\s\u4e00-\u9fff\u3400-\u4dbf\-,.\u3000-\u303f\uff00-\uffef]+$",
    re.UNICODE,
)
MAX_KEYWORD_LENGTH = 50


class MonitorRequest(BaseModel):
    """Request schema for starting a new monitoring run."""

    keywords: List[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Keywords to monitor (1-10 items)",
    )

    @field_validator("keywords")
    @classmethod
    def strip_and_validate_keywords(cls, v: List[str]) -> List[str]:
        """Strip whitespace, remove empties, validate content for safety."""
        stripped = [kw.strip() for kw in v]
        non_empty = [kw for kw in stripped if kw]
        if not non_empty:
            raise ValueError("At least one non-empty keyword is required")
        for kw in non_empty:
            if len(kw) > MAX_KEYWORD_LENGTH:
                raise ValueError(
                    f"Keyword too long: {kw[:20]}... (max {MAX_KEYWORD_LENGTH} chars)"
                )
            if any(c in kw for c in "\n\r\x00"):
                raise ValueError("Keywords must not contain control characters")
            if not _ALLOWED_KEYWORD_RE.match(kw):
                raise ValueError(
                    f"Keyword contains disallowed characters: {kw!r}"
                )
        return non_empty


class MonitorResponse(BaseModel):
    """Response schema after starting a monitoring run."""

    run_id: str = Field(..., description="Unique identifier for this run")
    status: str = Field(..., description="Current status of the run")
    message: str = Field(..., description="Human-readable status message")


class RunStatus(str, enum.Enum):
    """Enumeration of possible run statuses."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ProgressMessage(BaseModel):
    """WebSocket progress message sent during a monitoring run."""

    type: str = Field(
        ...,
        pattern=r"^(status|keyword_progress|pipeline_stats|completed|error)$",
        description="Message type",
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Payload data for this progress update",
    )


class RunRecord(BaseModel):
    """A single monitoring run record."""

    id: str = Field(..., description="Unique run identifier")
    status: RunStatus = Field(..., description="Current run status")
    keywords: List[str] = Field(..., description="Keywords monitored in this run")
    created_at: datetime = Field(..., description="When the run was created")
    completed_at: Optional[datetime] = Field(
        None, description="When the run completed (or failed)"
    )
    report_markdown: Optional[str] = Field(
        None, description="Generated Markdown report"
    )
    stats: Optional[Dict[str, Any]] = Field(
        None, description="Pipeline statistics"
    )
    error_message: Optional[str] = Field(
        None, description="Error message if the run failed"
    )


class RunListResponse(BaseModel):
    """Paginated list of monitoring run records."""

    runs: List[RunRecord] = Field(..., description="List of run records")
    total: int = Field(..., ge=0, description="Total number of runs")
    page: int = Field(..., ge=1, description="Current page number")
    limit: int = Field(..., ge=1, description="Items per page")


class ReportResponse(BaseModel):
    """Detailed report for a single monitoring run."""

    run: RunRecord = Field(..., description="The run record")
    analyzed_posts: Optional[List[Dict[str, Any]]] = Field(
        None, description="List of analyzed posts with AI annotations"
    )
    big_fish: Optional[List[Dict[str, Any]]] = Field(
        None, description="High-importance posts flagged as big fish"
    )
    category_stats: Optional[List[Dict[str, Any]]] = Field(
        None, description="Statistics per category"
    )
