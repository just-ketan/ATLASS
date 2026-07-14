"""Execute ATLASS-generated baselines and record an honest reproduction report."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from uuid import uuid4


REPORT_DIR = "data/reproduction_reports"


class ReproductionRunner:
    """Runs only the fixed entry points emitted by BaselineProjectGenerator."""

    def __init__(self, report_dir: str | Path = REPORT_DIR):
        self.report_dir = Path(report_dir)

    def run_smoke(self, manifest: dict, system_spec: dict) -> tuple[dict, str]:
        project_dir = Path(manifest["project_dir"]).resolve()
        if not project_dir.is_dir() or not (project_dir / "atlass_manifest.json").exists():
            raise FileNotFoundError("Generated baseline project is unavailable")

        train = self._run(project_dir, [sys.executable, "-m", "src.train", "--config", "config/experiment.json", "--epochs", "1"])
        evaluate = self._run(project_dir, [sys.executable, "-m", "src.evaluate", "--config", "config/experiment.json"])
        observed = self._json_output(evaluate["stdout"])
        report = {
            "run_id": f"run_{uuid4().hex[:12]}",
            "paper_id": manifest["paper_id"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "completed" if train["return_code"] == 0 and evaluate["return_code"] == 0 else "failed",
            "baseline_scope": manifest["scope"],
            "commands": {"train": train, "evaluate": evaluate},
            "observed_metrics": observed,
            "paper_reported_results": system_spec.get("fields", {}).get("reported_results", {}).get("value"),
            "comparison": {
                "status": "not_comparable",
                "reason": "The generated smoke experiment uses synthetic data and validates execution only; it cannot be compared to paper metrics.",
            },
            "assumptions": manifest.get("assumptions", []),
            "evidence": {
                "reported_results": system_spec.get("fields", {}).get("reported_results", {}).get("evidence", []),
                "metrics": system_spec.get("fields", {}).get("metrics", {}).get("evidence", []),
            },
        }
        report_path = self.report_dir / manifest["paper_id"] / f"{report['run_id']}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2))
        return report, str(report_path)

    @staticmethod
    def _run(project_dir: Path, command: list[str]) -> dict:
        completed = subprocess.run(
            command,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        return {
            "command": command,
            "return_code": completed.returncode,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
        }

    @staticmethod
    def _json_output(output: str) -> dict:
        try:
            return json.loads(output.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError):
            return {}
