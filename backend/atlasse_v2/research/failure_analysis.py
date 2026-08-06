"""Rank likely root causes when reproduction diverges from paper metrics."""

from __future__ import annotations

import re

from atlasse_v2.core.types import EvidenceLabel
from atlasse_v2.research.types import labeled_item, ResearchContext


KNOWN_CAUSES = [
    ("missing augmentation", ["augment", "augmentation"], EvidenceLabel.HEURISTIC_SUGGESTION),
    ("small batch size", ["batch size", "batch_size"], EvidenceLabel.HEURISTIC_SUGGESTION),
    ("dataset mismatch", ["dataset", "benchmark"], EvidenceLabel.EVIDENCE_BACKED_INFERENCE),
    ("different tokenizer", ["tokenizer", "vocab"], EvidenceLabel.HEURISTIC_SUGGESTION),
    ("different optimizer", ["optimizer", "adam", "sgd"], EvidenceLabel.EVIDENCE_BACKED_INFERENCE),
    ("different random seed", ["seed", "random"], EvidenceLabel.HEURISTIC_SUGGESTION),
    ("insufficient epochs", ["epoch", "training steps"], EvidenceLabel.HEURISTIC_SUGGESTION),
    ("checkpoint unavailable", ["checkpoint", "pretrained"], EvidenceLabel.HEURISTIC_SUGGESTION),
    ("hyperparameters missing from spec", ["training", "hyperparameter"], EvidenceLabel.PAPER_SUPPORTED),
    ("dataset not specified in paper evidence", ["dataset"], EvidenceLabel.PAPER_SUPPORTED),
    ("smoke compile only — no training run", ["smoke", "compile"], EvidenceLabel.EVIDENCE_BACKED_INFERENCE),
    ("baseline family not supported", ["supported", "family"], EvidenceLabel.EVIDENCE_BACKED_INFERENCE),
]


class FailureAnalyzer:
    def analyze(self, ctx: ResearchContext) -> dict:
        causes: list[dict] = []
        report = ctx.reproduction_report
        fields = ctx.spec.get("fields", {})
        blob = self._context_blob(ctx)

        if report.get("metric_comparable") is False:
            verdict = report.get("comparability_verdict", {})
            causes.append(labeled_item(
                verdict.get("reason", "Metrics not comparable to paper."),
                EvidenceLabel.EVIDENCE_BACKED_INFERENCE,
                confidence=0.9,
                evidence=["reproduction_report.comparability_verdict"],
                likelihood=0.95,
            ))

        if fields.get("training", {}).get("missing"):
            causes.append(labeled_item(
                "Training hyperparameters missing from extracted specification.",
                EvidenceLabel.PAPER_SUPPORTED,
                confidence=fields.get("training", {}).get("confidence", 0.0),
                evidence=self._field_evidence(fields, "training"),
                likelihood=0.85,
            ))

        if fields.get("dataset", {}).get("missing"):
            causes.append(labeled_item(
                "Dataset not extracted from paper — reproduction cannot match paper setup.",
                EvidenceLabel.PAPER_SUPPORTED,
                confidence=fields.get("dataset", {}).get("confidence", 0.0),
                evidence=self._field_evidence(fields, "dataset"),
                likelihood=0.9,
            ))

        smoke = report.get("smoke_validation", {})
        if smoke.get("skipped"):
            causes.append(labeled_item(
                "Smoke validation skipped — baseline project not generated.",
                EvidenceLabel.EVIDENCE_BACKED_INFERENCE,
                confidence=0.85,
                likelihood=0.8,
            ))
        elif smoke.get("passed") is False:
            causes.append(labeled_item(
                "Generated baseline failed compile smoke check.",
                EvidenceLabel.EVIDENCE_BACKED_INFERENCE,
                confidence=0.9,
                evidence=[str(e) for e in smoke.get("errors", [])[:3]],
                likelihood=0.75,
            ))

        for name, keywords, default_label in KNOWN_CAUSES:
            if any(kw in blob for kw in keywords):
                label = (
                    EvidenceLabel.PAPER_SUPPORTED
                    if name in ("hyperparameters missing from spec", "dataset not specified in paper evidence")
                    else default_label
                )
                score = sum(1 for kw in keywords if kw in blob) / len(keywords)
                if score > 0 and not any(c["text"].startswith(name.split()[0]) for c in causes):
                    causes.append(labeled_item(
                        f"Possible factor: {name}.",
                        label,
                        confidence=min(0.5 + score * 0.3, 0.85),
                        likelihood=round(0.4 + score * 0.25, 2),
                    ))

        if ctx.training_logs:
            log_lower = ctx.training_logs.lower()
            if "cuda" in log_lower or "oom" in log_lower:
                causes.append(labeled_item(
                    "Training logs suggest GPU memory or device issues.",
                    EvidenceLabel.EVIDENCE_BACKED_INFERENCE,
                    confidence=0.7,
                    evidence=["training_logs"],
                    likelihood=0.6,
                ))

        causes.sort(key=lambda c: c.get("likelihood", 0), reverse=True)
        return {
            "paper_id": ctx.paper_id,
            "root_causes": causes[:12],
            "observed_metrics": ctx.observed_metrics,
            "paper_metrics": report.get("paper_reported_metrics"),
            "summary": (
                f"Identified {len(causes)} potential factors ranked by likelihood."
                if causes
                else "No divergence signals — reproduction may be aligned or not yet run."
            ),
        }

    @staticmethod
    def _context_blob(ctx: ResearchContext) -> str:
        parts = []
        for field in ctx.spec.get("fields", {}).values():
            if field.get("value"):
                parts.append(str(field["value"]).lower())
        parts.extend(ctx.baseline.get("assumptions", []))
        parts.extend(ctx.reproduction_report.get("limitations", []))
        return " ".join(parts).lower()

    @staticmethod
    def _field_evidence(fields: dict, name: str) -> list[str]:
        field = fields.get(name, {})
        chunks = field.get("source_chunks", [])
        return [f"spec.fields.{name}"] + chunks[:3]
