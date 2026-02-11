"""
FastAPI routes for monitoring operations.

Provides endpoints to start new monitoring runs and stream progress via WebSocket.
"""

import asyncio
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from web.backend.config import DB_PATH
from web.backend.models import MonitorRequest, MonitorResponse, ProgressMessage
from web.backend.services.run_history import RunHistoryManager
from web.backend.utils import validate_run_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitor", tags=["monitor"])

# Module-level shared state: run_id -> asyncio.Queue[ProgressMessage dict]
active_monitors: dict[str, asyncio.Queue] = {}

MAX_CONCURRENT_RUNS = 5


@router.post("/start", response_model=MonitorResponse)
async def start_monitor(request: MonitorRequest) -> MonitorResponse:
    """Start a new monitoring run and return run_id immediately."""
    # Enforce concurrent run limit
    if len(active_monitors) >= MAX_CONCURRENT_RUNS:
        return MonitorResponse(
            run_id="",
            status="failed",
            message="Too many concurrent runs. Please try again later.",
        )

    run_id = str(uuid.uuid4())
    keywords = request.keywords

    try:
        history = RunHistoryManager(db_path=DB_PATH)
        created = history.create_run(run_id, keywords)
        if not created:
            logger.error("Failed to create run record for %s", run_id)
            return MonitorResponse(
                run_id=run_id,
                status="failed",
                message="Failed to create run record in database",
            )
    except Exception as e:
        logger.error("Database error creating run %s: %s", run_id, e)
        return MonitorResponse(
            run_id=run_id,
            status="failed",
            message="Internal server error. Please try again later.",
        )

    # Create the progress queue for this run
    queue: asyncio.Queue = asyncio.Queue()
    active_monitors[run_id] = queue

    # Launch background task
    asyncio.create_task(_run_monitor_background(run_id, keywords, queue))

    logger.info("Monitor started: run_id=%s, keyword_count=%d", run_id, len(keywords))

    return MonitorResponse(
        run_id=run_id,
        status="pending",
        message=f"Monitoring started for {len(keywords)} keyword(s)",
    )


async def _run_monitor_background(
    run_id: str,
    keywords: list[str],
    queue: asyncio.Queue,
) -> None:
    """Background task: run the monitor and push progress to the queue."""
    try:
        from web.backend.services import monitor_service

        await monitor_service.run_monitor(run_id, keywords, queue)
    except ImportError:
        logger.warning(
            "monitor_service not available; sending placeholder completion for %s",
            run_id,
        )
        await queue.put(
            {"type": "error", "data": {"message": "Monitor service not implemented yet"}}
        )
    except Exception as e:
        logger.error("Monitor background task failed for %s: %s", run_id, e)
        await queue.put(
            {"type": "error", "data": {"message": "Monitoring failed unexpectedly."}}
        )
    finally:
        # Grace period for late WebSocket connections, then clean up
        await asyncio.sleep(300)
        active_monitors.pop(run_id, None)


@router.websocket("/ws/{run_id}")
async def monitor_websocket(websocket: WebSocket, run_id: str) -> None:
    """Stream monitoring progress via WebSocket. Closes on 'completed' or 'error'."""
    validate_run_id(run_id)
    await websocket.accept()

    # Verify the run exists
    try:
        history = RunHistoryManager(db_path=DB_PATH)
        run = history.get_run(run_id)
    except Exception as e:
        logger.error("Database error checking run %s: %s", run_id, e)
        await websocket.close(code=4004, reason="Database error")
        return

    if run is None:
        logger.warning("WebSocket: run not found: %s", run_id)
        await websocket.close(code=4004, reason="Run not found")
        return

    queue = active_monitors.get(run_id)
    if queue is None:
        logger.info("WebSocket: no active monitor for run %s (may be completed)", run_id)
        await websocket.close(
            code=4004, reason="No active monitor for this run"
        )
        return

    logger.info("WebSocket connected for run %s", run_id)

    try:
        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=60.0)
            except asyncio.TimeoutError:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(
                        {"type": "status", "data": {"message": "waiting for progress..."}}
                    )
                continue

            try:
                progress = ProgressMessage(**message)
            except Exception:
                progress = None

            payload = progress.model_dump() if progress else message

            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json(payload)

            msg_type = message.get("type", "")
            if msg_type in ("completed", "error"):
                logger.info(
                    "WebSocket: terminal message received for run %s (type=%s)",
                    run_id,
                    msg_type,
                )
                break

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected by client for run %s", run_id)
    except Exception as e:
        logger.error("WebSocket error for run %s: %s", run_id, e)
    finally:
        active_monitors.pop(run_id, None)

        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.close()
            except Exception:
                pass

        logger.info("WebSocket closed for run %s", run_id)
