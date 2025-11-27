"""
Asynchronous scheduler that runs the data pipeline every N days.

This module is designed to be the container entrypoint. It keeps the process
alive, triggers the pipeline, and gracefully handles shutdown signals.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
from datetime import datetime, timedelta, timezone

from . import pipeline


def _str_to_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _build_logger() -> logging.Logger:
    level = os.getenv("PIPELINE_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger("pipeline-scheduler")


logger = _build_logger()


def _interval_seconds() -> int:
    """Returns the interval in seconds, defaulting to three days."""
    raw = os.getenv("PIPELINE_INTERVAL_DAYS", "3")
    try:
        days = float(raw)
    except ValueError:
        logger.warning(
            "Invalid PIPELINE_INTERVAL_DAYS=%s; falling back to 3 days.", raw
        )
        days = 3.0

    # Guard against extremely small or negative values.
    interval = max(int(days * 24 * 60 * 60), 60)
    return interval


async def _sleep_with_stop(
    stop_event: asyncio.Event, seconds: int, reason: str
) -> None:
    """Sleeps unless stop_event is set; logs the reason for sleeping."""
    if seconds <= 0:
        return

    logger.info("Next pipeline run in %s (reason: %s).", timedelta(seconds=seconds), reason)
    try:
        await asyncio.wait_for(stop_event.wait(), timeout=seconds)
    except asyncio.TimeoutError:
        return


async def _run_pipeline_once() -> None:
    logger.info(
        "Starting pipeline run at %s",
        datetime.now(timezone.utc).isoformat(),
    )
    try:
        await pipeline.main()
        logger.info("Pipeline run finished successfully.")
    except Exception:  # pragma: no cover - best-effort logging
        logger.exception("Pipeline run failed.")


async def scheduler_loop() -> None:
    interval = _interval_seconds()
    run_immediately = _str_to_bool(os.getenv("PIPELINE_RUN_ON_START"), True)
    initial_delay = int(os.getenv("PIPELINE_INITIAL_DELAY_SECONDS", "0") or 0)

    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    if initial_delay > 0:
        await _sleep_with_stop(stop_event, initial_delay, "initial delay")

    if run_immediately:
        await _run_pipeline_once()

    while not stop_event.is_set():
        await _sleep_with_stop(stop_event, interval, "interval")
        if stop_event.is_set():
            break
        await _run_pipeline_once()

    logger.info("Scheduler exiting gracefully.")


def main() -> None:
    asyncio.run(scheduler_loop())


if __name__ == "__main__":
    main()

