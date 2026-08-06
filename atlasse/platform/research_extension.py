"""Bridge platform workspace artifacts to the v2 research extension engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPORT_DIR = Path("data/research_reports")


PLATFORM_TO_V2_FIELDS = {
    "problem_statement": "problem",
    "contribution": "contribution",
    "task_definition": "task",
    "model_components": "architecture",
    "objective": "loss",
    "training_setup": "training",
    "datasets": "dataset",
    "metrics": "metric",
    "baselines": "baseline",
    "limitations": "limitation",
    "reported_results": "metric",
}


class PlatformResearchExtension:
    """Run research mode using platform system spec, blueprint, manifest, and smoke report."""

    def run(
        self,
        paper_id: str,
        platform_spec: dict,
        platform_blueprint: dict,
        manifest: dict,
        reproduction_report: dict | None,
    ) -> dict:
        from atlasse_v2.research.engine import ResearchExtensionEngine
        from atlasse_v2.research.types import ResearchContext

        ctx = ResearchContext(
            paper_id=paper_id,
            spec=self._normalize_spec(platform_spec),
            blueprint=self._normalize_blueprint(platform_blueprint, paper_id),
            baseline=self._normalize_baseline(manifest, paper_id),
            reproduction_report=self._normalize_reproduction(reproduction_report, platform_spec, paper_id),
            graph_entities=self._entities_from_blueprint(platform_blueprint),
            observed_metrics=(reproduction_report or {}).get("observed_metrics"),
            training_logs=self._training_logs(reproduction_report),
        )
        engine = ResearchExtensionEngine()
        report = engine.run(ctx)
        path = self._save(report, paper_id)
        report["storage_path"] = path
        return report

    def load(self, paper_id: str) -> dict | None:
        path = REPORT_DIR / paper_id / "research_report.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    @staticmethod
    def _save(report: dict, paper_id: str) -> str:
        base = REPORT_DIR / paper_id
        base.mkdir(parents=True, exist_ok=True)
        path = base / "research_report.json"
        path.write_text(json.dumps(report, indent=2))
        nb = base / "research_notebook.md"
        nb.write_text(report.get("notebook", {}).get("markdown", ""))
        return str(path)

    @staticmethod
    def _normalize_spec(platform_spec: dict) -> dict:
        fields_src = platform_spec.get("fields", {})
        fields: dict[str, Any] = {}
        for platform_key, v2_key in PLATFORM_TO_V2_FIELDS.items():
            raw = fields_src.get(platform_key, {})
            if v2_key in fields and fields[v2_key].get("value"):
                continue
            value = raw.get("value")
            assumptions = []
            if raw.get("assumption"):
                assumptions.append(raw["assumption"])
            fields[v2_key] = {
                "value": value,
                "confidence": raw.get("confidence", 0.0),
                "missing": not value,
                "assumptions": assumptions,
                "source_chunks": [],
            }
        return {
            "paper_id": platform_spec.get("paper_id"),
            "version": platform_spec.get("review", {}).get("version", 1),
            "fields": fields,
        }

    @staticmethod
    def _normalize_blueprint(platform_blueprint: dict, paper_id: str) -> dict:
        modules = []
        for m in platform_blueprint.get("modules", []):
            modules.append({
                "module": m.get("responsibility") or m.get("path"),
                "file": m.get("path"),
                "evidence_entity_id": m.get("evidence_entity_id") or f"module_{len(modules)}",
                "confidence": m.get("confidence", 0.5),
            })
        return {
            "paper_id": paper_id,
            "version": platform_blueprint.get("review", {}).get("version", 1),
            "modules": modules,
            "data_flow": platform_blueprint.get("data_flow", []),
            "training_flow": platform_blueprint.get("training_plan", []),
        }

    @staticmethod
    def _normalize_baseline(manifest: dict, paper_id: str) -> dict:
        return {
            "paper_id": paper_id,
            "family": manifest.get("model_family", "mlp"),
            "supported": True,
            "confidence": 0.7,
            "assumptions": [
                a.get("description", a) if isinstance(a, dict) else str(a)
                for a in manifest.get("assumptions", [])
            ],
            "files": list(manifest.get("source_mapping", {}).keys()),
            "project_dir": "project",
        }

    @staticmethod
    def _normalize_reproduction(
        report: dict | None,
        platform_spec: dict,
        paper_id: str,
    ) -> dict:
        if not report:
            return {
                "paper_id": paper_id,
                "level": "smoke_test",
                "metric_comparable": False,
                "comparability_verdict": {
                    "comparable": False,
                    "status": "not_comparable",
                    "reason": "No smoke run completed yet.",
                },
                "limitations": [],
                "paper_reported_metrics": {
                    "text": platform_spec.get("fields", {}).get("reported_results", {}).get("value"),
                    "missing": not platform_spec.get("fields", {}).get("reported_results", {}).get("value"),
                },
                "run_status": "not_run",
                "smoke_validation": {"passed": False, "skipped": True},
            }

        comparison = report.get("comparison", {})
        comparable = comparison.get("status") == "comparable"
        return {
            "paper_id": paper_id,
            "level": "smoke_test" if report.get("is_smoke_run") else "partial_reproduction",
            "metric_comparable": comparable,
            "comparability_verdict": {
                "comparable": comparable,
                "status": comparison.get("status", "not_comparable"),
                "reason": comparison.get("reason", ""),
            },
            "limitations": [
                report.get("baseline_scope", ""),
            ],
            "paper_reported_metrics": {
                "text": report.get("paper_reported_results"),
                "missing": not report.get("paper_reported_results"),
            },
            "observed_metrics": report.get("observed_metrics"),
            "run_status": report.get("status"),
            "smoke_validation": {
                "passed": report.get("status") == "completed",
                "is_smoke_run": report.get("is_smoke_run", False),
            },
        }

    @staticmethod
    def _entities_from_blueprint(platform_blueprint: dict) -> list[dict]:
        entities = []
        for i, m in enumerate(platform_blueprint.get("modules", [])):
            entities.append({
                "entity_id": f"ent_{i}",
                "entity_type": "module",
                "text": f"{m.get('responsibility', '')} {m.get('path', '')}",
                "normalized_name": m.get("path", f"module_{i}"),
            })
        return entities

    @staticmethod
    def _training_logs(report: dict | None) -> str | None:
        if not report:
            return None
        cmds = report.get("commands", {})
        parts = []
        for key in ("train", "evaluate"):
            block = cmds.get(key, {})
            if block.get("stderr"):
                parts.append(block["stderr"])
            if block.get("stdout"):
                parts.append(block["stdout"][-2000:])
        return "\n".join(parts) if parts else None
