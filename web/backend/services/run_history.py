"""
SQLite-based run history manager.

Stores monitoring run records (status, keywords, results, reports).
Follows the same per-operation connect/close pattern as src/dedup.py.
"""

import json
import logging
import os
import sqlite3
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class RunHistoryManager:
    """
    SQLite run history manager.

    Stores and retrieves monitoring run records. Each operation opens
    and closes its own connection (no persistent connection), matching
    the pattern established by DedupManager.
    """

    def __init__(self, db_path: str = "data/run_history.db"):
        """
        Initialize the run history manager.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self._ensure_database()
        logger.info("RunHistoryManager initialized with database: %s", db_path)

    def _ensure_database(self):
        """Ensure the database file and schema exist."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info("Created directory: %s", db_dir)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'pending',
                keywords TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                result_json TEXT,
                report_markdown TEXT,
                stats_json TEXT,
                error_message TEXT
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_runs_created_at
            ON runs(created_at DESC)
        """)

        conn.commit()
        conn.close()
        logger.debug("Database and table ensured")

    def create_run(self, run_id: str, keywords: List[str]) -> bool:
        """
        Create a new run record with pending status.

        Args:
            run_id: Unique identifier for the run.
            keywords: List of keywords to monitor.

        Returns:
            bool: True if created successfully, False otherwise.
        """
        if not run_id or not isinstance(run_id, str):
            logger.warning("Invalid run_id: %s", run_id)
            return False

        if not keywords or not isinstance(keywords, list):
            logger.warning("Invalid keywords: %s", keywords)
            return False

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            keywords_json = json.dumps(keywords, ensure_ascii=False)
            cursor.execute(
                "INSERT INTO runs (id, status, keywords) VALUES (?, 'pending', ?)",
                (run_id, keywords_json),
            )

            conn.commit()
            logger.info("Created run: %s with keywords: %s", run_id, keywords)
            return True

        except sqlite3.IntegrityError:
            logger.warning("Duplicate run_id: %s", run_id)
            return False

        except Exception as e:
            logger.error("Failed to create run %s: %s", run_id, e)
            return False

        finally:
            if conn is not None:
                conn.close()

    def update_status(self, run_id: str, status: str, **kwargs) -> bool:
        """
        Update the status and optional fields of a run record.

        Args:
            run_id: The run identifier to update.
            status: New status value (pending, running, completed, failed).
            **kwargs: Optional fields to update. Supported keys:
                - result_json (str): Full analyzed posts JSON.
                - report_markdown (str): Generated Markdown report.
                - stats_json (str): Pipeline statistics JSON.
                - error_message (str): Error message for failed runs.
                - completed_at (str): ISO timestamp when the run finished.

        Returns:
            bool: True if updated successfully, False otherwise.
        """
        if not run_id or not isinstance(run_id, str):
            logger.warning("Invalid run_id for update: %s", run_id)
            return False

        valid_statuses = {"pending", "running", "completed", "failed"}
        if status not in valid_statuses:
            logger.warning("Invalid status: %s", status)
            return False

        allowed_fields = {
            "result_json", "report_markdown", "stats_json",
            "error_message", "completed_at",
        }

        # Build SET clause from status + valid kwargs (immutable approach)
        set_parts = ["status = ?"]
        params = [status]

        for key, value in kwargs.items():
            if key in allowed_fields:
                set_parts.append(f"{key} = ?")
                params.append(value)
            else:
                logger.warning("Ignoring unknown field: %s", key)

        params.append(run_id)
        set_clause = ", ".join(set_parts)

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                f"UPDATE runs SET {set_clause} WHERE id = ?",
                params,
            )

            updated = cursor.rowcount > 0
            conn.commit()

            if updated:
                logger.info("Updated run %s to status: %s", run_id, status)
            else:
                logger.warning("Run not found for update: %s", run_id)

            return updated

        except Exception as e:
            logger.error("Failed to update run %s: %s", run_id, e)
            return False

        finally:
            if conn is not None:
                conn.close()

    def get_run(self, run_id: str) -> Optional[Dict]:
        """
        Retrieve a single run record by ID.

        Args:
            run_id: The run identifier.

        Returns:
            dict or None: Run record as a dictionary, or None if not found.
        """
        if not run_id or not isinstance(run_id, str):
            return None

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
            row = cursor.fetchone()

            if row is None:
                logger.debug("Run not found: %s", run_id)
                return None

            return _row_to_dict(row)

        except Exception as e:
            logger.error("Failed to get run %s: %s", run_id, e)
            return None

        finally:
            if conn is not None:
                conn.close()

    def list_runs(self, page: int = 1, limit: int = 20) -> Dict:
        """
        List run records with pagination, ordered by created_at descending.

        Args:
            page: Page number (1-based).
            limit: Number of records per page.

        Returns:
            dict: {"runs": [...], "total": int} with parsed keywords.
        """
        page = max(1, page)
        limit = max(1, min(100, limit))
        offset = (page - 1) * limit

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get total count
            cursor.execute("SELECT COUNT(*) FROM runs")
            total = cursor.fetchone()[0]

            # Get paginated results
            cursor.execute(
                "SELECT * FROM runs ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
            rows = cursor.fetchall()

            runs = [_row_to_dict(row) for row in rows]

            logger.debug(
                "Listed runs: page=%d, limit=%d, total=%d, returned=%d",
                page, limit, total, len(runs),
            )

            return {"runs": runs, "total": total}

        except Exception as e:
            logger.error("Failed to list runs: %s", e)
            return {"runs": [], "total": 0}

        finally:
            if conn is not None:
                conn.close()

    def close(self):
        """Close the manager (no-op, connections are per-operation)."""
        logger.debug("RunHistoryManager closed")


def _row_to_dict(row: sqlite3.Row) -> Dict:
    """
    Convert a sqlite3.Row to a plain dictionary with parsed JSON fields.

    Keywords are parsed from JSON string back to a list.
    This is a pure function (no side effects).

    Args:
        row: A sqlite3.Row object from the runs table.

    Returns:
        dict: Run record with keywords as list and parsed JSON fields.
    """
    record = dict(row)

    # Parse keywords from JSON string to list
    keywords_raw = record.get("keywords", "[]")
    try:
        record["keywords"] = json.loads(keywords_raw)
    except (json.JSONDecodeError, TypeError):
        record["keywords"] = []

    # Parse stats_json to dict if present
    stats_raw = record.get("stats_json")
    if stats_raw:
        try:
            record["stats"] = json.loads(stats_raw)
        except (json.JSONDecodeError, TypeError):
            record["stats"] = None
    else:
        record["stats"] = None

    return record
