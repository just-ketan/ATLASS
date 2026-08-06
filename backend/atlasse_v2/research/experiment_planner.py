"""Rank novel experiments by novelty, feasibility, and expected contribution."""

from __future__ import annotations

from atlasse_v2.core.types import EvidenceLabel
from atlasse_v2.research.types import labeled_item, ResearchContext


class NovelExperimentPlanner:
    def plan(
        self,
        ctx: ResearchContext,
        improvements: dict,
        ablations: dict,
    ) -> dict:
        experiments: list[dict] = []

        for sug in improvements.get("suggestions", [])[:5]:
            item = sug["item"]
            experiments.append({
                "title": sug.get("category", "improvement"),
                "description": item["text"][:300],
                "reason": sug.get("motivation", ""),
                "expected_impact": sug.get("expected_impact", "Unknown"),
                "novelty": 0.5,
                "feasibility": 0.7,
                "contribution": 0.65,
                "item": item,
            })

        for ab in ablations.get("experiments", [])[:4]:
            if ab.get("component") == "full":
                continue
            experiments.append({
                "title": ab["ablation"],
                "description": ab["item"]["text"],
                "reason": f"Component ablation: {ab.get('component')}",
                "expected_impact": "Isolates component contribution.",
                "novelty": 0.4,
                "feasibility": 0.85,
                "contribution": 0.6,
                "item": ab["item"],
            })

        family = ctx.baseline.get("family", "")
        if family in ("lora", "peft"):
            experiments.append({
                "title": "Replace LoRA with DoRA",
                "description": "Swap low-rank adaptation for DoRA on the same backbone.",
                "reason": "Lower rank deficiency in recent PEFT literature.",
                "expected_impact": "Medium",
                "novelty": 0.55,
                "feasibility": 0.75,
                "contribution": 0.6,
                "item": labeled_item(
                    "Experiment: Replace LoRA with DoRA under matched rank budget.",
                    EvidenceLabel.SPECULATIVE_RESEARCH_IDEA,
                    confidence=0.4,
                ),
            })

        experiments.append({
            "title": "Seed sweep reproducibility",
            "description": "Run 3–5 seeds and report mean ± std on primary metric.",
            "reason": "Quantify variance not always reported in papers.",
            "expected_impact": "Medium",
            "novelty": 0.3,
            "feasibility": 0.9,
            "contribution": 0.55,
            "item": labeled_item(
                "Multi-seed evaluation for variance reporting.",
                EvidenceLabel.HEURISTIC_SUGGESTION,
                confidence=0.6,
            ),
        })

        for exp in experiments:
            score = (
                exp["novelty"] * 0.35
                + exp["feasibility"] * 0.35
                + exp["contribution"] * 0.30
            )
            exp["rank_score"] = round(score, 3)

        experiments.sort(key=lambda e: e["rank_score"], reverse=True)
        ranked = experiments[:10]
        if len(ranked) < 3:
            ranked = experiments

        return {
            "paper_id": ctx.paper_id,
            "experiments": ranked,
            "count": len(ranked),
            "ranking_note": labeled_item(
                "Experiments ranked by weighted novelty, feasibility, and contribution — not paper claims.",
                EvidenceLabel.EVIDENCE_BACKED_INFERENCE,
                confidence=0.9,
            ),
        }
