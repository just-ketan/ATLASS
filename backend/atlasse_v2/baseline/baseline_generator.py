"""Phase 9: Fill family-specific templates from research graph."""

from __future__ import annotations

import json
from pathlib import Path

from atlasse_v2.baseline.family_detector import FamilyDetector
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
            }

        assumptions = []
        training = self.spec.get("fields", {}).get("training", {})
        if training.get("missing"):
            assumptions.append("Training hyperparameters not found in paper — defaults required.")

        return {
            "paper_id": paper_id,
            "family": family.value,
            "supported": True,
            "confidence": confidence,
            "assumptions": assumptions,
            "files": self._template_files(family),
            "manifest": {
                "evidence_entities": list(self.graph.entities.keys()),
                "spec_version": self.spec.get("version"),
            },
        }

    @staticmethod
    def _template_files(family: ModelFamily) -> list[dict]:
        common = [
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
                {"path": "src/model/mlp.py", "template": "mlp"},
            ],
            ModelFamily.CNN: [
                {"path": "src/model/cnn.py", "template": "cnn"},
            ],
        }
        return family_files.get(family, []) + common

    def save(self, baseline: dict, base_dir: str | None = None) -> str:
        paper_id = baseline["paper_id"]
        base = Path(base_dir or self.BASELINE_DIR) / paper_id
        base.mkdir(parents=True, exist_ok=True)
        path = base / "baseline.json"
        path.write_text(json.dumps(baseline, indent=2))
        return str(path)
