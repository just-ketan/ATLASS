"""Persist agent execution traces."""

from __future__ import annotations

import json
from pathlib import Path

from atlasse_v2.agents.base import AgentTrace


class AgentTraceStore:
    TRACE_DIR = "data/v2/agent_traces"

    def save(self, trace: AgentTrace, base_dir: str | None = None) -> str:
        base = Path(base_dir or self.TRACE_DIR) / trace.paper_id
        base.mkdir(parents=True, exist_ok=True)
        path = base / "latest_trace.json"
        path.write_text(json.dumps(trace.to_dict(), indent=2))
        return str(path)

    def load(self, paper_id: str, base_dir: str | None = None) -> dict | None:
        path = Path(base_dir or self.TRACE_DIR) / paper_id / "latest_trace.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())
