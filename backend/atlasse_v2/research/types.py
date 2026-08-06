"""Shared types for the research extension engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from atlasse_v2.core.types import EVIDENCE_LABEL_DISPLAY, EvidenceLabel


def labeled_item(
    text: str,
    label: EvidenceLabel,
    confidence: float = 0.0,
    evidence: list[str] | None = None,
    **extra: Any,
) -> dict:
    return {
        "text": text,
        "label": label.value,
        "label_display": EVIDENCE_LABEL_DISPLAY[label.value],
        "confidence": round(confidence, 2),
        "evidence": evidence or [],
        **extra,
    }


@dataclass
class ResearchContext:
    """Artifacts available after reproduction — inputs to research modules."""

    paper_id: str
    spec: dict
    blueprint: dict
    baseline: dict
    reproduction_report: dict
    graph_entities: list[dict] = field(default_factory=list)
    observed_metrics: dict | None = None
    training_logs: str | None = None
    configuration: dict = field(default_factory=dict)

    @classmethod
    def from_pipeline(
        cls,
        paper_id: str,
        spec: dict,
        blueprint: dict,
        baseline: dict,
        reproduction_report: dict,
        graph: Any | None = None,
        observed_metrics: dict | None = None,
        training_logs: str | None = None,
        configuration: dict | None = None,
    ) -> ResearchContext:
        entities = []
        if graph is not None:
            for e in graph.entities.values():
                entities.append({
                    "entity_id": e.entity_id,
                    "entity_type": e.entity_type.value,
                    "text": e.text[:300],
                    "normalized_name": e.normalized_name,
                })
        return cls(
            paper_id=paper_id,
            spec=spec,
            blueprint=blueprint,
            baseline=baseline,
            reproduction_report=reproduction_report,
            graph_entities=entities,
            observed_metrics=observed_metrics or reproduction_report.get("observed_metrics"),
            training_logs=training_logs,
            configuration=configuration or {},
        )
