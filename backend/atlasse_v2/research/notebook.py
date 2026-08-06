"""Assemble the permanent research notebook for a project."""

from __future__ import annotations

from datetime import datetime, timezone

from atlasse_v2.core.types import EVIDENCE_LABEL_DISPLAY


class ResearchNotebookBuilder:
    def build(
        self,
        ctx,
        failure: dict,
        sensitivity: dict,
        ablations: dict,
        improvements: dict,
        experiments: dict,
    ) -> dict:
        sections = {
            "background": self._background(ctx),
            "paper_summary": self._paper_summary(ctx),
            "architecture": self._architecture(ctx),
            "implementation": self._implementation(ctx),
            "training": self._training(ctx),
            "results": self._results(ctx),
            "comparison": self._comparison(ctx),
            "failure_analysis": failure,
            "sensitivity_analysis": sensitivity,
            "ablation_plan": ablations,
            "improvements": improvements,
            "future_experiments": experiments,
        }
        markdown = self._to_markdown(ctx.paper_id, sections)
        return {
            "paper_id": ctx.paper_id,
            "title": f"ATLASS Research Notebook — {ctx.paper_id}",
            "sections": sections,
            "markdown": markdown,
            "label_legend": EVIDENCE_LABEL_DISPLAY,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _background(self, ctx) -> dict:
        problem = ctx.spec.get("fields", {}).get("problem", {})
        return {
            "problem": problem.get("value"),
            "contribution": ctx.spec.get("fields", {}).get("contribution", {}).get("value"),
        }

    def _paper_summary(self, ctx) -> dict:
        return {
            "method": ctx.spec.get("fields", {}).get("method", {}).get("value"),
            "task": ctx.spec.get("fields", {}).get("task", {}).get("value"),
            "dataset": ctx.spec.get("fields", {}).get("dataset", {}).get("value"),
            "metric": ctx.spec.get("fields", {}).get("metric", {}).get("value"),
        }

    def _architecture(self, ctx) -> dict:
        return {
            "description": ctx.spec.get("fields", {}).get("architecture", {}).get("value"),
            "modules": ctx.blueprint.get("modules", []),
            "family": ctx.baseline.get("family"),
        }

    def _implementation(self, ctx) -> dict:
        return {
            "baseline_supported": ctx.baseline.get("supported"),
            "files": ctx.baseline.get("files", []),
            "assumptions": ctx.baseline.get("assumptions", []),
        }

    def _training(self, ctx) -> dict:
        return {
            "training": ctx.spec.get("fields", {}).get("training", {}).get("value"),
            "loss": ctx.spec.get("fields", {}).get("loss", {}).get("value"),
        }

    def _results(self, ctx) -> dict:
        return {
            "observed_metrics": ctx.observed_metrics,
            "paper_metrics": ctx.reproduction_report.get("paper_reported_metrics"),
            "run_status": ctx.reproduction_report.get("run_status"),
        }

    def _comparison(self, ctx) -> dict:
        return {
            "metric_comparable": ctx.reproduction_report.get("metric_comparable"),
            "comparability_verdict": ctx.reproduction_report.get("comparability_verdict"),
            "level": ctx.reproduction_report.get("level"),
        }

    def _to_markdown(self, paper_id: str, sections: dict) -> str:
        lines = [
            f"# ATLASS Research Notebook — {paper_id}",
            "",
            "## Label legend",
            "",
        ]
        for key, display in EVIDENCE_LABEL_DISPLAY.items():
            lines.append(f"- `{key}`: {display}")
        lines.extend(["", "## Background", "", str(sections["background"]), "", "## Paper summary", "", str(sections["paper_summary"])])
        lines.extend(["", "## Architecture", "", str(sections["architecture"])])
        lines.extend(["", "## Implementation", "", str(sections["implementation"])])
        lines.extend(["", "## Training", "", str(sections["training"])])
        lines.extend(["", "## Results", "", str(sections["results"])])
        lines.extend(["", "## Comparison", "", str(sections["comparison"])])
        lines.extend(["", "## Failure analysis", "", str(sections["failure_analysis"].get("summary", ""))])
        for cause in sections["failure_analysis"].get("root_causes", [])[:5]:
            lines.append(f"- [{cause.get('label_display')}] {cause.get('text')}")
        lines.extend(["", "## Future experiments", ""])
        for exp in sections["future_experiments"].get("experiments", [])[:7]:
            item = exp.get("item", {})
            lines.append(f"- [{item.get('label_display', 'n/a')}] {exp.get('title')}: {exp.get('description', '')[:200]}")
        lines.append("")
        return "\n".join(lines)
