"""Typed handoff objects between agents — never free-form text."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class AgentResult:
    agent_name: str
    success: bool
    output_type: str
    payload: dict[str, Any]
    duration_ms: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "success": self.success,
            "output_type": self.output_type,
            "payload_keys": list(self.payload.keys()),
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


@dataclass
class AgentTrace:
    paper_id: str
    started_at: str
    completed_at: str | None = None
    steps: list[dict] = field(default_factory=list)
    success: bool = False

    def add(self, result: AgentResult) -> None:
        self.steps.append(result.to_dict())

    def to_dict(self) -> dict:
        return {
            "paper_id": self.paper_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "success": self.success,
            "steps": self.steps,
        }
