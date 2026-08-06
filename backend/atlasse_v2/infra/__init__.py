"""Production infrastructure — logging, cache, background jobs."""

from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


def setup_logging(name: str = "atlasse_v2") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def log_event(logger: logging.Logger, event: str, **fields) -> None:
    payload = {"event": event, "timestamp": datetime.now(timezone.utc).isoformat(), **fields}
    logger.info(json.dumps(payload))
    trace_span(event, fields)


def trace_span(name: str, attributes: dict | None = None) -> None:
    """OpenTelemetry hook — no-op unless opentelemetry-sdk is installed."""
    try:
        from opentelemetry import trace
        tracer = trace.get_tracer("atlasse_v2")
        with tracer.start_as_current_span(name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))
    except ImportError:
        return


class FileCache:
    """Simple file-backed cache (Redis optional in production)."""

    def __init__(self, cache_dir: str = "data/v2/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> dict | None:
        path = self.cache_dir / f"{key}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def set(self, key: str, value: dict) -> None:
        path = self.cache_dir / f"{key}.json"
        path.write_text(json.dumps(value))


class JobQueue:
    """In-process background job queue with persisted status."""

    def __init__(self, job_dir: str = "data/v2/jobs"):
        self.job_dir = Path(job_dir)
        self.job_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def submit(self, fn: Callable, *args, **kwargs) -> str:
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        status = {"job_id": job_id, "status": "pending", "created_at": datetime.now(timezone.utc).isoformat()}
        self._write(job_id, status)

        def runner():
            self._write(job_id, {**status, "status": "running"})
            try:
                result = fn(*args, **kwargs)
                self._write(job_id, {
                    "job_id": job_id,
                    "status": "completed",
                    "result": result,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                })
            except Exception as exc:
                self._write(job_id, {
                    "job_id": job_id,
                    "status": "failed",
                    "error": str(exc),
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                })

        threading.Thread(target=runner, daemon=True).start()
        return job_id

    def get(self, job_id: str) -> dict | None:
        path = self.job_dir / f"{job_id}.json"
        if not path.exists():
            return None
        for _ in range(5):
            text = path.read_text()
            if text.strip():
                return json.loads(text)
            import time
            time.sleep(0.01)
        return None

    def _write(self, job_id: str, payload: dict) -> None:
        with self._lock:
            path = self.job_dir / f"{job_id}.json"
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(payload, indent=2))
            tmp.replace(path)
