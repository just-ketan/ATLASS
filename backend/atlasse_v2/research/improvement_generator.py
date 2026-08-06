"""Suggest improvements from limitations, future work, and deviation signals."""

from __future__ import annotations

from atlasse_v2.core.types import EvidenceLabel
from atlasse_v2.research.types import labeled_item, ResearchContext


class ImprovementGenerator:
    def generate(self, ctx: ResearchContext) -> dict:
        suggestions: list[dict] = []
        fields = ctx.spec.get("fields", {})

        limitation = fields.get("limitation", {})
        if limitation.get("value") and not limitation.get("missing"):
            suggestions.append({
                "category": "address_limitation",
                "item": labeled_item(
                    f"Address stated limitation: {limitation['value'][:400]}",
                    EvidenceLabel.PAPER_SUPPORTED,
                    confidence=limitation.get("confidence", 0.7),
                    evidence=["spec.fields.limitation"],
                ),
                "motivation": "Paper explicitly lists this limitation.",
                "expected_impact": "High if limitation is binding.",
            })

        future = fields.get("future_work", {})
        if future.get("value") and not future.get("missing"):
            suggestions.append({
                "category": "future_work",
                "item": labeled_item(
                    f"Extend along future work: {future['value'][:400]}",
                    EvidenceLabel.PAPER_SUPPORTED,
                    confidence=future.get("confidence", 0.7),
                    evidence=["spec.fields.future_work"],
                ),
                "motivation": "Authors propose this direction.",
                "expected_impact": "Medium–high (author-suggested).",
            })

        for assumption in ctx.baseline.get("assumptions", []):
            suggestions.append({
                "category": "resolve_assumption",
                "item": labeled_item(
                    f"Resolve baseline assumption: {assumption}",
                    EvidenceLabel.EVIDENCE_BACKED_INFERENCE,
                    confidence=0.65,
                    evidence=["baseline.assumptions"],
                ),
                "motivation": "Baseline used a default due to missing paper detail.",
                "expected_impact": "Medium — may close reproduction gap.",
            })

        for lim in ctx.reproduction_report.get("limitations", []):
            suggestions.append({
                "category": "reproduction_gap",
                "item": labeled_item(
                    f"Close reproduction gap: {lim}",
                    EvidenceLabel.EVIDENCE_BACKED_INFERENCE,
                    confidence=0.7,
                    evidence=["reproduction_report.limitations"],
                ),
                "motivation": "Reproduction report flagged this gap.",
                "expected_impact": "High for comparability.",
            })

        family = ctx.baseline.get("family", "")
        if family == "lora":
            suggestions.append({
                "category": "architecture",
                "item": labeled_item(
                    "Try parameter-efficient alternatives (DoRA, AdaLoRA) on same base model.",
                    EvidenceLabel.SPECULATIVE_RESEARCH_IDEA,
                    confidence=0.35,
                ),
                "motivation": "PEFT family — common research extension.",
                "expected_impact": "Medium novelty.",
            })

        dataset_val = fields.get("dataset", {}).get("value", "")
        if dataset_val and "glue" in str(dataset_val).lower():
            suggestions.append({
                "category": "dataset",
                "item": labeled_item(
                    "Evaluate on additional NLP benchmarks beyond those in the paper excerpt.",
                    EvidenceLabel.HEURISTIC_SUGGESTION,
                    confidence=0.5,
                    evidence=["spec.fields.dataset"],
                ),
                "motivation": "Broader benchmark coverage is a standard robustness check.",
                "expected_impact": "Medium.",
            })

        if not ctx.reproduction_report.get("metric_comparable"):
            suggestions.append({
                "category": "training",
                "item": labeled_item(
                    "Recover full training recipe (epochs, LR schedule, warmup) from paper + appendix.",
                    EvidenceLabel.HEURISTIC_SUGGESTION,
                    confidence=0.55,
                ),
                "motivation": "Metrics not currently comparable.",
                "expected_impact": "High for faithful reproduction.",
            })

        return {
            "paper_id": ctx.paper_id,
            "suggestions": suggestions,
            "count": len(suggestions),
        }
