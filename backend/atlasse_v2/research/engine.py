"""Research extension engine — post-reproduction research mode."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from atlasse_v2.research.ablation_generator import AblationGenerator
from atlasse_v2.research.experiment_planner import NovelExperimentPlanner
from atlasse_v2.research.export import ResearchExporter
from atlasse_v2.research.failure_analysis import FailureAnalyzer
from atlasse_v2.research.improvement_generator import ImprovementGenerator
from atlasse_v2.research.notebook import ResearchNotebookBuilder
from atlasse_v2.research.sensitivity_analysis import SensitivityAnalyzer
from atlasse_v2.research.types import ResearchContext


class ResearchExtensionEngine:
    """Orchestrates Phase 3 research modules after reproduction completes."""

    REPORT_DIR = "data/v2/research_reports"

    def run(self, ctx: ResearchContext) -> dict:
        failure = FailureAnalyzer().analyze(ctx)
        sensitivity = SensitivityAnalyzer().analyze(ctx)
        ablations = AblationGenerator().generate(ctx)
        improvements = ImprovementGenerator().generate(ctx)
        experiments = NovelExperimentPlanner().plan(ctx, improvements, ablations)
        notebook = ResearchNotebookBuilder().build(
            ctx, failure, sensitivity, ablations, improvements, experiments,
        )

        return {
            "paper_id": ctx.paper_id,
            "mode": "research",
            "reproduction_outcome": self._reproduction_outcome(ctx),
            "failure_analysis": failure,
            "sensitivity_analysis": sensitivity,
            "ablation_plan": ablations,
            "improvements": improvements,
            "experiment_plan": experiments,
            "notebook": notebook,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _reproduction_outcome(ctx: ResearchContext) -> dict:
        report = ctx.reproduction_report
        comparable = report.get("metric_comparable", False)
        smoke = report.get("smoke_validation", {})
        success = smoke.get("passed") and comparable
        return {
            "successful": success,
            "level": report.get("level"),
            "metric_comparable": comparable,
            "run_status": report.get("run_status"),
            "message": (
                "Reproduction metrics align with paper evidence."
                if success
                else "Reproduction incomplete or not comparable — research mode still available."
            ),
        }

    def save(self, report: dict, base_dir: str | None = None) -> str:
        paper_id = report["paper_id"]
        base = Path(base_dir or self.REPORT_DIR) / paper_id
        base.mkdir(parents=True, exist_ok=True)
        path = base / "research_report.json"
        path.write_text(json.dumps(report, indent=2))
        nb_md = base / "research_notebook.md"
        nb_md.write_text(report.get("notebook", {}).get("markdown", ""))
        return str(path)

    @classmethod
    def load(cls, paper_id: str, base_dir: str | None = None) -> dict | None:
        path = Path(base_dir or cls.REPORT_DIR) / paper_id / "research_report.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def export(self, report: dict, formats: list[str], base_dir: str | None = None) -> dict:
        paper_id = report["paper_id"]
        out_dir = Path(base_dir or self.REPORT_DIR) / paper_id / "exports"
        return ResearchExporter().export(report, formats, out_dir)
