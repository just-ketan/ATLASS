"""Phase 10: Classify reproduction feasibility — never compare synthetic vs paper metrics."""

from __future__ import annotations

import json
from pathlib import Path

from atlasse_v2.core.types import ReproductionLevel, ReproductionStatus


class ReproductionEngine:
    REPORT_DIR = "data/v2/reproduction_reports"

    def classify(self, baseline: dict, spec: dict) -> dict:
        statuses: list[str] = []
        family = baseline.get("family", "unknown")
        supported = baseline.get("supported", False)

        if supported:
            statuses.append(ReproductionStatus.EXECUTABLE.value)
        else:
            statuses.append(ReproductionStatus.TRAINING_INFEASIBLE.value)

        if family != "unknown":
            statuses.append(ReproductionStatus.ARCHITECTURE_MATCHED.value)

        dataset_field = spec.get("fields", {}).get("dataset", {})
        if dataset_field.get("missing"):
            statuses.append(ReproductionStatus.DATASET_UNAVAILABLE.value)

        training_field = spec.get("fields", {}).get("training", {})
        if training_field.get("missing"):
            statuses.append(ReproductionStatus.HYPERPARAMETERS_MISSING.value)

        is_synthetic = baseline.get("assumptions") and any(
            "synthetic" in a.lower() for a in baseline.get("assumptions", [])
        )
        metric_comparable = supported and not is_synthetic and not dataset_field.get("missing")

        if metric_comparable:
            statuses.append(ReproductionStatus.METRIC_COMPARABLE.value)

        confidence = baseline.get("confidence", 0.0)
        if dataset_field.get("missing"):
            confidence *= 0.5
        if training_field.get("missing"):
            confidence *= 0.7

        return {
            "paper_id": baseline.get("paper_id"),
            "level": ReproductionLevel.SMOKE_TEST.value,
            "statuses": statuses,
            "metric_comparable": metric_comparable,
            "overall_confidence": round(confidence, 2),
            "limitations": baseline.get("assumptions", []),
            "synthetic_warning": "Synthetic metrics must never be compared against paper-reported metrics.",
        }

    def save(self, report: dict, base_dir: str | None = None) -> str:
        paper_id = report["paper_id"]
        base = Path(base_dir or self.REPORT_DIR) / paper_id
        base.mkdir(parents=True, exist_ok=True)
        path = base / "reproduction_report.json"
        path.write_text(json.dumps(report, indent=2))
        return str(path)
