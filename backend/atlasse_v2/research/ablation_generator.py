"""Generate ablation experiments from blueprint modules and graph entities."""

from __future__ import annotations

from atlasse_v2.core.types import EvidenceLabel
from atlasse_v2.research.types import labeled_item, ResearchContext

ABLATION_TARGETS = [
    ("attention", ["attention", "self-attention", "multi-head"]),
    ("residual connections", ["residual", "skip"]),
    ("normalization", ["normalization", "batch norm", "layer norm"]),
    ("augmentation", ["augment", "augmentation"]),
    ("loss term", ["loss", "cross-entropy"]),
    ("adapters", ["lora", "adapter", "peft"]),
    ("dropout", ["dropout"]),
    ("positional encoding", ["positional", "position embedding"]),
]


class AblationGenerator:
    def generate(self, ctx: ResearchContext) -> dict:
        blob = self._component_blob(ctx)
        modules = ctx.blueprint.get("modules", [])
        experiments: list[dict] = []
        table_rows: list[dict] = []

        for name, keywords in ABLATION_TARGETS:
            if not any(kw in blob for kw in keywords):
                continue
            evidence_ids = [
                m.get("evidence_entity_id")
                for m in modules
                if m.get("evidence_entity_id") and any(kw in str(m).lower() for kw in keywords)
            ]
            label = (
                EvidenceLabel.PAPER_SUPPORTED
                if evidence_ids
                else EvidenceLabel.EVIDENCE_BACKED_INFERENCE
            )
            exp = {
                "ablation": f"Remove or disable {name}",
                "component": name,
                "item": labeled_item(
                    f"Ablation: remove {name} and measure metric delta.",
                    label,
                    confidence=0.75 if evidence_ids else 0.55,
                    evidence=evidence_ids[:3],
                ),
                "expected_metric": ctx.spec.get("fields", {}).get("metric", {}).get("value"),
            }
            experiments.append(exp)
            table_rows.append({
                "configuration": f"w/o {name}",
                "metric": None,
                "delta": None,
                "label": label.value,
                "label_display": exp["item"]["label_display"],
            })

        if not experiments:
            experiments.append({
                "ablation": "Full model (baseline run)",
                "component": "full",
                "item": labeled_item(
                    "No independent components identified for ablation — run full model baseline first.",
                    EvidenceLabel.EVIDENCE_BACKED_INFERENCE,
                    confidence=0.6,
                ),
            })

        return {
            "paper_id": ctx.paper_id,
            "experiments": experiments,
            "ablation_table": {
                "columns": ["configuration", "metric", "delta", "label"],
                "rows": table_rows,
            },
        }

    @staticmethod
    def _component_blob(ctx: ResearchContext) -> str:
        parts = []
        for m in ctx.blueprint.get("modules", []):
            parts.append(str(m.get("module", "")))
            parts.append(str(m.get("file", "")))
        for e in ctx.graph_entities:
            parts.append(e.get("text", ""))
        method = ctx.spec.get("fields", {}).get("method", {}).get("value", "")
        arch = ctx.spec.get("fields", {}).get("architecture", {}).get("value", "")
        parts.extend([method, arch])
        return " ".join(parts).lower()
