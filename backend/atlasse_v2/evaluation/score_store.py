"""Persist benchmark scores across runs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class ScoreStore:
    SCORES_PATH = "data/v2/benchmark/scores.json"

    def __init__(self, path: str | None = None):
        self.path = Path(path or self.SCORES_PATH)

    def load(self) -> dict:
        if not self.path.exists():
            return {"runs": []}
        return json.loads(self.path.read_text())

    def append(self, run_result: dict) -> str:
        data = self.load()
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **run_result,
        }
        data["runs"].append(entry)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2))
        return str(self.path)

    def latest(self) -> dict | None:
        data = self.load()
        runs = data.get("runs", [])
        return runs[-1] if runs else None
