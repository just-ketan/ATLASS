"""Phase 9: Fill family-specific templates from research graph and write project files."""

from __future__ import annotations

import json
from pathlib import Path

from atlasse_v2.baseline.family_detector import FamilyDetector
from atlasse_v2.baseline.template_renderer import write_project
from atlasse_v2.core.types import ModelFamily
from atlasse_v2.graph.semantic_graph import SemanticPaperGraph


class BaselineGenerator:
    BASELINE_DIR = "data/v2/baselines"

    SUPPORTED_FAMILIES = {
        ModelFamily.LORA,
        ModelFamily.TRANSFORMER,
        ModelFamily.MLP,
        ModelFamily.CNN,
    }

    def __init__(self, graph: SemanticPaperGraph, spec: dict | None = None):
        self.graph = graph
        self.spec = spec or {}
        self.detector = FamilyDetector(graph)

    def generate(self, paper_id: str) -> dict:
        family, confidence = self.detector.detect()
        if family not in self.SUPPORTED_FAMILIES:
            return {
                "paper_id": paper_id,
                "family": family.value,
                "supported": False,
                "confidence": confidence,
                "message": f"Model family '{family.value}' is not yet supported. Refusing to generate misleading code.",
                "assumptions": [],
                "files": [],
                "project_dir": None,
            }

        assumptions = self._collect_assumptions()
        file_specs = self._template_files(family)
        evidence_ids = list(self.graph.entities.keys())

        return {
            "paper_id": paper_id,
            "family": family.value,
            "supported": True,
            "confidence": confidence,
            "assumptions": assumptions,
            "files": file_specs,
            "manifest": {
                "evidence_entities": evidence_ids,
                "spec_version": self.spec.get("version"),
            },
            "project_dir": f"project",
        }

    def _collect_assumptions(self) -> list[str]:
        assumptions = []
        for field_name in ("training", "loss", "dataset", "architecture"):
            field = self.spec.get("fields", {}).get(field_name, {})
            if field.get("missing"):
                assumptions.append(f"{field_name}: not specified in paper — using defaults.")
            for a in field.get("assumptions", []):
                assumptions.append(a)
        return assumptions

    def save(self, baseline: dict, base_dir: str | None = None) -> str:
        paper_id = baseline["paper_id"]
        base = Path(base_dir or self.BASELINE_DIR) / paper_id
        base.mkdir(parents=True, exist_ok=True)
        path = base / "baseline.json"
        path.write_text(json.dumps({k: v for k, v in baseline.items() if k != "file_manifest"}, indent=2))

        if baseline.get("supported") and baseline.get("files"):
            family = ModelFamily(baseline["family"])
            project_dir = base / baseline.get("project_dir", "project")
            manifest = write_project(
                project_dir=project_dir,
                paper_id=paper_id,
                family=family,
                file_specs=baseline["files"],
                spec=self.spec,
                assumptions=baseline.get("assumptions", []),
                evidence_entity_ids=baseline.get("manifest", {}).get("evidence_entities", []),
            )
            baseline["file_manifest"] = manifest
            path.write_text(json.dumps(baseline, indent=2))

        return str(path)

    @staticmethod
    def _template_files(family: ModelFamily) -> list[dict]:
        common = [
            {"path": "src/data/dataset.py", "template": "dataset"},
            {"path": "src/train.py", "template": "train"},
            {"path": "src/evaluate.py", "template": "evaluate"},
            {"path": "config.yaml", "template": "config"},
            {"path": "README.md", "template": "readme"},
        ]
        family_files = {
            ModelFamily.LORA: [
                {"path": "src/model/lora.py", "template": "lora"},
                {"path": "src/model/base_model.py", "template": "base_model"},
            ],
            ModelFamily.TRANSFORMER: [
                {"path": "src/model/transformer.py", "template": "transformer"},
                {"path": "src/model/attention.py", "template": "attention"},
            ],
            ModelFamily.MLP: [
                {"path": "src/model/mlp.py", "template": "transformer"},
            ],
            ModelFamily.CNN: [
                {"path": "src/model/cnn.py", "template": "transformer"},
            ],
        }
        return family_files.get(family, []) + common
