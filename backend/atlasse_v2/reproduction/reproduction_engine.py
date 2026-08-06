"""Phase 10: Reproduction classification, smoke validation, and honest comparability."""

from __future__ import annotations

import json
import py_compile
from datetime import datetime, timezone
from pathlib import Path

from atlasse_v2.core.types import ReproductionLevel, ReproductionStatus


class ReproductionEngine:
    REPORT_DIR = "data/v2/reproduction_reports"

    def classify_level(self, baseline: dict, spec: dict) -> ReproductionLevel:
        if not baseline.get("supported"):
            return ReproductionLevel.SMOKE_TEST
        fields = spec.get("fields", {})
        missing_training = fields.get("training", {}).get("missing", True)
        missing_dataset = fields.get("dataset", {}).get("missing", True)
        project_exists = baseline.get("file_manifest") or baseline.get("files")
        if not project_exists:
            return ReproductionLevel.SMOKE_TEST
        if missing_training or missing_dataset:
            return ReproductionLevel.PARTIAL
        return ReproductionLevel.FULL

    def classify(self, baseline: dict, spec: dict) -> dict:
        statuses: list[str] = []
        family = baseline.get("family", "unknown")
        supported = baseline.get("supported", False)
        fields = spec.get("fields", {})

        if supported:
            statuses.append(ReproductionStatus.EXECUTABLE.value)
        else:
            statuses.append(ReproductionStatus.TRAINING_INFEASIBLE.value)

        if family != "unknown":
            statuses.append(ReproductionStatus.ARCHITECTURE_MATCHED.value)

        dataset_field = fields.get("dataset", {})
        if dataset_field.get("missing"):
            statuses.append(ReproductionStatus.DATASET_UNAVAILABLE.value)

        training_field = fields.get("training", {})
        if training_field.get("missing"):
            statuses.append(ReproductionStatus.HYPERPARAMETERS_MISSING.value)

        comparability = self._comparability_verdict(baseline, spec, supported, dataset_field)
        if comparability["comparable"]:
            statuses.append(ReproductionStatus.METRIC_COMPARABLE.value)

        level = self.classify_level(baseline, spec)
        confidence = baseline.get("confidence", 0.0)
        if dataset_field.get("missing"):
            confidence *= 0.5
        if training_field.get("missing"):
            confidence *= 0.7

        return {
            "paper_id": baseline.get("paper_id"),
            "level": level.value,
            "statuses": statuses,
            "metric_comparable": comparability["comparable"],
            "comparability_verdict": comparability,
            "overall_confidence": round(confidence, 2),
            "limitations": list(baseline.get("assumptions", [])) + comparability.get("limitations", []),
            "paper_reported_metrics": self._paper_metrics(fields),
            "synthetic_warning": (
                "Synthetic or smoke metrics must never be compared against paper-reported metrics."
            ),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def _comparability_verdict(
        self,
        baseline: dict,
        spec: dict,
        supported: bool,
        dataset_field: dict,
    ) -> dict:
        limitations = []
        if not supported:
            return {
                "comparable": False,
                "status": "not_comparable",
                "reason": "Baseline family not supported — cannot run paper-aligned experiment.",
                "limitations": limitations,
            }
        if dataset_field.get("missing"):
            limitations.append("Dataset not extracted from paper evidence.")
            return {
                "comparable": False,
                "status": "not_comparable",
                "reason": "Dataset unavailable or not specified in paper.",
                "limitations": limitations,
            }
        if any("synthetic" in a.lower() for a in baseline.get("assumptions", [])):
            return {
                "comparable": False,
                "status": "not_comparable",
                "reason": "Synthetic data path — execution only, not comparable to paper metrics.",
                "limitations": limitations,
            }
        metric_field = spec.get("fields", {}).get("metric", {})
        if metric_field.get("missing"):
            limitations.append("Paper metrics not extracted — comparison impossible.")
            return {
                "comparable": False,
                "status": "not_comparable",
                "reason": "Paper-reported metrics not available in specification.",
                "limitations": limitations,
            }
        return {
            "comparable": True,
            "status": "potentially_comparable",
            "reason": "Real-data baseline with extracted dataset and metrics — comparison possible after full training run.",
            "limitations": limitations,
        }

    @staticmethod
    def _paper_metrics(fields: dict) -> dict:
        metric = fields.get("metric", {})
        return {
            "text": metric.get("value"),
            "missing": metric.get("missing", True),
            "confidence": metric.get("confidence", 0.0),
        }

    def smoke_validate_project(self, project_dir: Path) -> dict:
        """Bounded validation: compile-check generated Python files."""
        project_dir = Path(project_dir)
        if not project_dir.is_dir():
            return {"passed": False, "reason": "project_dir_missing", "files_checked": 0}

        py_files = list(project_dir.rglob("*.py"))
        errors = []
        for py_file in py_files:
            try:
                py_compile.compile(str(py_file), doraise=True)
            except py_compile.PyCompileError as exc:
                errors.append({"file": str(py_file.relative_to(project_dir)), "error": str(exc)})

        return {
            "passed": len(errors) == 0,
            "files_checked": len(py_files),
            "errors": errors,
            "is_smoke_run": True,
        }

    def run_smoke(self, baseline: dict, spec: dict, data_dir: str) -> dict:
        report = self.classify(baseline, spec)
        paper_id = baseline.get("paper_id")
        project_rel = baseline.get("project_dir", "project")
        project_dir = Path(data_dir) / "baselines" / paper_id / project_rel
        smoke = self.smoke_validate_project(project_dir)
        report["smoke_validation"] = smoke
        report["observed_metrics"] = None
        if smoke["passed"]:
            report["run_status"] = "smoke_compile_ok"
        else:
            report["run_status"] = "smoke_compile_failed"
            report["comparability_verdict"] = {
                "comparable": False,
                "status": "not_comparable",
                "reason": "Generated project failed compile smoke check.",
                "limitations": report.get("limitations", []),
            }
            report["metric_comparable"] = False
        return report

    def build_report(self, baseline: dict, spec: dict, data_dir: str) -> dict:
        return self.run_smoke(baseline, spec, data_dir)

    def save(self, report: dict, base_dir: str | None = None) -> str:
        paper_id = report["paper_id"]
        base = Path(base_dir or self.REPORT_DIR) / paper_id
        base.mkdir(parents=True, exist_ok=True)
        path = base / "reproduction_report.json"
        path.write_text(json.dumps(report, indent=2))
        return str(path)

    @classmethod
    def load(cls, paper_id: str, base_dir: str | None = None) -> dict | None:
        path = Path(base_dir or cls.REPORT_DIR) / paper_id / "reproduction_report.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())
