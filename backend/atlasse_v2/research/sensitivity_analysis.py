"""Parameter sensitivity study plans and plot-ready series."""

from __future__ import annotations

import re

from atlasse_v2.core.types import EvidenceLabel
from atlasse_v2.research.types import labeled_item, ResearchContext

DEFAULT_PARAMS = {
    "learning_rate": [1e-5, 3e-5, 1e-4, 3e-4, 1e-3],
    "batch_size": [8, 16, 32, 64],
    "dropout": [0.0, 0.1, 0.2, 0.3, 0.5],
    "weight_decay": [0.0, 0.01, 0.1],
    "seed": [0, 1, 42, 123],
}

OPTIMIZERS = ["adam", "adamw", "sgd"]
SCHEDULERS = ["cosine", "linear", "constant"]


class SensitivityAnalyzer:
    def analyze(self, ctx: ResearchContext) -> dict:
        training_text = str(ctx.spec.get("fields", {}).get("training", {}).get("value") or "")
        parsed = self._parse_training_hints(training_text)
        variations = []

        for param, values in DEFAULT_PARAMS.items():
            paper_value = parsed.get(param)
            sweep = values
            label = EvidenceLabel.HEURISTIC_SUGGESTION
            confidence = 0.5
            evidence = []
            if paper_value is not None:
                label = EvidenceLabel.PAPER_SUPPORTED
                confidence = ctx.spec["fields"]["training"].get("confidence", 0.6)
                evidence = ["spec.fields.training"]
                if paper_value in values:
                    sweep = sorted(set(values + [paper_value]))

            variations.append({
                "parameter": param,
                "paper_value": paper_value,
                "sweep_values": sweep,
                "item": labeled_item(
                    f"Vary {param} across {sweep}",
                    label,
                    confidence=confidence,
                    evidence=evidence,
                ),
                "plot": self._plot_spec(param, sweep, paper_value),
            })

        for opt in OPTIMIZERS:
            in_paper = opt in training_text.lower()
            variations.append({
                "parameter": "optimizer",
                "paper_value": opt if in_paper else None,
                "sweep_values": OPTIMIZERS,
                "item": labeled_item(
                    f"Compare optimizer: {opt}",
                    EvidenceLabel.PAPER_SUPPORTED if in_paper else EvidenceLabel.HEURISTIC_SUGGESTION,
                    confidence=0.7 if in_paper else 0.45,
                    evidence=["spec.fields.training"] if in_paper else [],
                ),
                "plot": self._plot_spec("optimizer", OPTIMIZERS, opt if in_paper else None),
            })

        for sched in SCHEDULERS:
            in_paper = sched in training_text.lower()
            variations.append({
                "parameter": "scheduler",
                "paper_value": sched if in_paper else None,
                "sweep_values": SCHEDULERS,
                "item": labeled_item(
                    f"Compare scheduler: {sched}",
                    EvidenceLabel.PAPER_SUPPORTED if in_paper else EvidenceLabel.HEURISTIC_SUGGESTION,
                    confidence=0.65 if in_paper else 0.4,
                ),
                "plot": self._plot_spec("scheduler", SCHEDULERS, sched if in_paper else None),
            })

        return {
            "paper_id": ctx.paper_id,
            "variations": variations,
            "plots": [v["plot"] for v in variations],
            "note": labeled_item(
                "Sensitivity curves require actual training runs — values below are sweep plans, not measured sensitivities.",
                EvidenceLabel.EVIDENCE_BACKED_INFERENCE,
                confidence=1.0,
            ),
        }

    @staticmethod
    def _parse_training_hints(text: str) -> dict:
        hints: dict = {}
        lr = re.search(r"learning rate[:\s]+([0-9.e\-]+)", text, re.I)
        if lr:
            try:
                hints["learning_rate"] = float(lr.group(1))
            except ValueError:
                pass
        bs = re.search(r"batch size[:\s]+(\d+)", text, re.I)
        if bs:
            hints["batch_size"] = int(bs.group(1))
        drop = re.search(r"dropout[:\s]+([0.0-9]+)", text, re.I)
        if drop:
            try:
                hints["dropout"] = float(drop.group(1))
            except ValueError:
                pass
        return hints

    @staticmethod
    def _plot_spec(param: str, values: list, paper_value) -> dict:
        """Plot-ready structure for frontend charting (no matplotlib dependency)."""
        x = [str(v) for v in values]
        # Placeholder y — real runs populate observed metrics
        y = [None] * len(values)
        if paper_value is not None and str(paper_value) in x:
            idx = x.index(str(paper_value))
            y[idx] = "paper_reported"
        return {
            "type": "sensitivity",
            "parameter": param,
            "x": x,
            "y": y,
            "paper_marker": str(paper_value) if paper_value is not None else None,
            "title": f"Sensitivity: {param}",
        }
