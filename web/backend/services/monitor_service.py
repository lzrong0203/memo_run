"""Monitor service -- orchestrates OpenClaw agent execution and progress tracking."""

import asyncio
import json
import logging
import os
import re
import shutil
from datetime import datetime, timezone
from typing import Optional

from web.backend.config import DB_PATH, PROJECT_ROOT
from web.backend.services.run_history import RunHistoryManager

logger = logging.getLogger(__name__)

KEYWORD_PROGRESS_RE = re.compile(
    r"正在搜尋關鍵字[:：]\s*(.+?)（第\s*(\d+)\s*/\s*(\d+)\s*個）"
)
PIPELINE_STATS_RE = re.compile(
    r"掃描\s*(\d+)\s*篇.*過濾\s*(\d+)\s*篇.*重複\s*(\d+)\s*篇.*有效\s*(\d+)\s*篇"
)
EXTRACTION_RE = re.compile(r"(?:JS 抽取完成|抽取到\s*(\d+)\s*篇)")

SUBPROCESS_TIMEOUT_SECONDS = 600
MAX_CAPTURED_LINES = 5000


def _parse_progress_line(line: str) -> Optional[dict]:
    """Parse a single stdout line into a ProgressMessage dict, or None."""
    match = KEYWORD_PROGRESS_RE.search(line)
    if match:
        return {
            "type": "keyword_progress",
            "data": {
                "keyword": match.group(1).strip(),
                "current": int(match.group(2)),
                "total": int(match.group(3)),
            },
        }

    match = PIPELINE_STATS_RE.search(line)
    if match:
        return {
            "type": "pipeline_stats",
            "data": {
                "scanned": int(match.group(1)),
                "filtered": int(match.group(2)),
                "duplicated": int(match.group(3)),
                "valid": int(match.group(4)),
            },
        }

    match = EXTRACTION_RE.search(line)
    if match:
        count = match.group(1)
        message = f"抽取到 {count} 篇貼文" if count else "JS 抽取完成"
        return {"type": "status", "data": {"status": "running", "message": message}}

    return None


def _find_json_output(lines: list[str]) -> Optional[dict]:
    """Scan captured stdout (backwards) for a JSON object with 'analyzed_posts'."""
    json_candidates: list[str] = []
    accumulating = False
    buffer: list[str] = []
    for line in reversed(lines):
        stripped = line.strip()
        if not accumulating and (stripped.endswith("}") or stripped == "}"):
            accumulating = True
            buffer = [stripped]
        elif accumulating:
            buffer.append(stripped)
            if stripped.startswith("{"):
                buffer.reverse()
                json_candidates.append("\n".join(buffer))
                accumulating = False
                buffer = []

    for candidate in json_candidates:
        try:
            data = json.loads(candidate)
            if isinstance(data, dict) and "analyzed_posts" in data:
                return data
        except (json.JSONDecodeError, TypeError):
            continue

    for line in reversed(lines):
        stripped = line.strip()
        if stripped.startswith("{"):
            try:
                data = json.loads(stripped)
                if isinstance(data, dict) and "analyzed_posts" in data:
                    return data
            except (json.JSONDecodeError, TypeError):
                continue

    return None


async def _fail_run(
    run_id: str,
    error_msg: str,
    history: RunHistoryManager,
    progress_queue: asyncio.Queue,
) -> None:
    """Record a failure in the database and notify via the progress queue."""
    logger.error("Run %s failed: %s", run_id, error_msg)
    history.update_status(
        run_id, "failed",
        error_message=error_msg,
        completed_at=datetime.now(timezone.utc).isoformat(),
    )
    # Send generic message to client, not raw internal details
    await progress_queue.put({
        "type": "error",
        "data": {"message": "Monitoring run failed. Check server logs for details."},
    })


async def _complete_run(
    run_id: str,
    history: RunHistoryManager,
    progress_queue: asyncio.Queue,
    report_available: bool = False,
    **update_kwargs,
) -> None:
    """Record a completion in the database and notify via the progress queue."""
    history.update_status(
        run_id, "completed",
        completed_at=datetime.now(timezone.utc).isoformat(),
        **update_kwargs,
    )
    await progress_queue.put({
        "type": "completed",
        "data": {"run_id": run_id, "report_available": report_available},
    })


async def run_monitor(
    run_id: str,
    keywords: list[str],
    progress_queue: asyncio.Queue,
) -> None:
    """Execute the OpenClaw agent subprocess, stream progress, generate report."""
    history = RunHistoryManager(db_path=DB_PATH)

    history.update_status(run_id, "running")
    await progress_queue.put({
        "type": "status",
        "data": {"status": "running", "message": "正在啟動 OpenClaw agent..."},
    })

    if not shutil.which("openclaw"):
        await _fail_run(run_id, "openclaw command not found in PATH", history, progress_queue)
        return

    keywords_joined = ",".join(keywords)
    cmd = [
        "openclaw", "agent",
        "--message", f"執行 threads-monitor 監控 關鍵字:{keywords_joined}",
        "--local", "--channel", "telegram",
        "--session-id", run_id,
    ]
    logger.info("Launching OpenClaw: run_id=%s, keyword_count=%d", run_id, len(keywords))

    captured_lines: list[str] = []
    stderr_lines: list[str] = []
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=PROJECT_ROOT,
        )

        async def _read_stdout():
            if process.stdout is None:
                return
            while True:
                raw = await process.stdout.readline()
                if not raw:
                    break
                line = raw.decode("utf-8", errors="replace").rstrip()
                if len(captured_lines) < MAX_CAPTURED_LINES:
                    captured_lines.append(line)
                logger.debug("openclaw stdout: %s", line)
                progress = _parse_progress_line(line)
                if progress is not None:
                    await progress_queue.put(progress)
                elif line.strip():
                    await progress_queue.put({
                        "type": "status",
                        "data": {"status": "running", "message": line.strip()},
                    })

        async def _read_stderr():
            if process.stderr is None:
                return
            while True:
                raw = await process.stderr.readline()
                if not raw:
                    break
                line = raw.decode("utf-8", errors="replace").rstrip()
                stderr_lines.append(line)
                logger.debug("openclaw stderr: %s", line)

        try:
            await asyncio.wait_for(
                asyncio.gather(_read_stdout(), _read_stderr(), process.wait()),
                timeout=SUBPROCESS_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            await _fail_run(
                run_id, f"監控超時（超過 {SUBPROCESS_TIMEOUT_SECONDS} 秒）",
                history, progress_queue,
            )
            return

        exit_code = process.returncode
        logger.info("OpenClaw exited with code: %s", exit_code)

        if exit_code == 0:
            await _handle_success(run_id, captured_lines, history, progress_queue)
        else:
            stderr_tail = "\n".join(stderr_lines[-20:]) if stderr_lines else ""
            logger.error(
                "OpenClaw failed for run %s (exit %s): %s",
                run_id, exit_code, stderr_tail,
            )
            await _fail_run(
                run_id,
                f"OpenClaw agent 執行失敗 (exit code {exit_code})",
                history, progress_queue,
            )

    except FileNotFoundError:
        await _fail_run(run_id, "openclaw command not found", history, progress_queue)
    except Exception as e:
        logger.exception("Unexpected error in run_monitor for %s", run_id)
        await _fail_run(
            run_id, f"監控過程中發生未預期錯誤: {type(e).__name__}", history, progress_queue,
        )


async def _handle_success(
    run_id: str,
    captured_lines: list[str],
    history: RunHistoryManager,
    progress_queue: asyncio.Queue,
) -> None:
    """Handle successful subprocess completion: parse output, generate report."""
    await progress_queue.put({
        "type": "status",
        "data": {"status": "running", "message": "正在解析結果並生成戰報..."},
    })

    json_output = _find_json_output(captured_lines)
    if json_output is None:
        logger.warning("No valid JSON output found in OpenClaw stdout for run %s", run_id)
        await _complete_run(run_id, history, progress_queue, report_available=False)
        return

    result_json_str = json.dumps(json_output, ensure_ascii=False)
    try:
        from report_generator import generate_all_outputs

        reports_dir = os.path.join(PROJECT_ROOT, "data", "reports")
        outputs = generate_all_outputs(json_output, reports_dir=reports_dir)

        if outputs is not None:
            stats_json_str = json.dumps(json_output.get("stats", {}), ensure_ascii=False)
            await _complete_run(
                run_id, history, progress_queue,
                report_available=True,
                result_json=result_json_str,
                report_markdown=outputs.get("markdown_report", ""),
                stats_json=stats_json_str,
            )
        else:
            logger.warning("generate_all_outputs returned None for run %s", run_id)
            await _complete_run(
                run_id, history, progress_queue,
                report_available=False,
                result_json=result_json_str,
            )

    except ImportError as e:
        logger.error("Failed to import report_generator: %s", e)
        await _complete_run(
            run_id, history, progress_queue,
            report_available=False,
            result_json=result_json_str,
        )

    except Exception as e:
        logger.exception("Report generation failed for run %s: %s", run_id, e)
        await _complete_run(
            run_id, history, progress_queue,
            report_available=False,
            result_json=result_json_str,
            error_message=f"報告生成失敗: {type(e).__name__}",
        )
