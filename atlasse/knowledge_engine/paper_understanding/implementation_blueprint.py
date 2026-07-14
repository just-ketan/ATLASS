"""Translate an approved system specification into a reviewable build plan."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path


BLUEPRINT_VERSION = "1.0"
BLUEPRINT_DIR = "data/implementation_blueprints"
_REQUIRED_FIELDS = ("task_definition", "inputs", "outputs", "model_components", "objective", "datasets")


class ImplementationBlueprintGenerator:
    """Produce an evidence-linked plan without inventing a paper reproduction."""

    def __init__(self, paper_id: str, output_dir: str | Path = BLUEPRINT_DIR):
        self.paper_id = paper_id
        self.output_dir = Path(output_dir)

    def generate(self, system_spec: dict) -> dict:
        fields = system_spec.get("fields", {})
        missing = [name for name in _REQUIRED_FIELDS if not self._value(fields, name)]
        family = self._infer_family(fields)
        assumptions = self._assumptions(fields, missing, family)

        return {
            "schema_version": BLUEPRINT_VERSION,
            "paper_id": self.paper_id,
            "system_spec_version": system_spec.get("schema_version"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "readiness": {
                "status": "ready_for_review" if not missing else "needs_specification",
                "supported_family": family,
                "missing_implementation_fields": missing,
                "scope_note": "This is a baseline plan. It must not be presented as a faithful reproduction until its assumptions are reviewed.",
            },
            "project_tree": [
                "README.md",
                "requirements.txt",
                "config/experiment.json",
                "src/data.py",
                "src/model.py",
                "src/train.py",
                "src/evaluate.py",
                "artifacts/",
            ],
            "modules": self._modules(fields),
            "data_contracts": self._data_contracts(fields),
            "training_plan": self._training_plan(fields),
            "configuration_schema": self._configuration_schema(fields),
            "dependencies": [
                {"package": "torch", "reason": "Model and training implementation."},
                {"package": "numpy", "reason": "Data and metric utilities."},
            ],
            "evidence_map": self._evidence_map(fields),
            "assumptions": assumptions,
            "review": {"status": "needs_review", "notes": "", "version": 1},
        }

    def save(self, blueprint: dict) -> str:
        output_dir = self.output_dir / self.paper_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "implementation_blueprint.json"
        with open(output_path, "w") as file:
            json.dump(blueprint, file, indent=2)
        return str(output_path)

    @staticmethod
    def _value(fields: dict, name: str) -> str | None:
        value = fields.get(name, {}).get("value")
        return value if isinstance(value, str) and value.strip() else None

    @classmethod
    def _infer_family(cls, fields: dict) -> str:
        text = " ".join(filter(None, [
            cls._value(fields, "task_definition"),
            cls._value(fields, "model_components"),
            cls._value(fields, "datasets"),
        ])).lower()
        if any(term in text for term in ("transformer", "language model", "token", "lora")):
            return "pytorch_text_model"
        if any(term in text for term in ("image", "vision", "imagenet", "cifar")):
            return "pytorch_vision_model"
        return "pytorch_supervised_model"

    @classmethod
    def _modules(cls, fields: dict) -> list[dict]:
        return [
            {
                "path": "src/data.py",
                "responsibility": "Load the selected dataset and transform each record into the input/target contract.",
                "evidence_fields": ["datasets", "preprocessing", "inputs", "outputs"],
            },
            {
                "path": "src/model.py",
                "responsibility": "Implement the proposed model components and forward pass.",
                "evidence_fields": ["model_components", "inputs", "outputs"],
            },
            {
                "path": "src/train.py",
                "responsibility": "Create the model, optimize the documented objective, and save checkpoints.",
                "evidence_fields": ["objective", "training_setup", "model_components"],
            },
            {
                "path": "src/evaluate.py",
                "responsibility": "Evaluate checkpoints using paper-aligned metrics and emit a result artifact.",
                "evidence_fields": ["metrics", "reported_results", "datasets"],
            },
        ]

    @classmethod
    def _data_contracts(cls, fields: dict) -> list[dict]:
        return [
            {
                "name": "DatasetItem",
                "producer": "src/data.py",
                "consumer": "src/model.py",
                "contract": {
                    "inputs": cls._value(fields, "inputs"),
                    "targets": cls._value(fields, "outputs"),
                },
                "evidence_fields": ["inputs", "outputs", "preprocessing"],
            },
            {
                "name": "ModelOutput",
                "producer": "src/model.py",
                "consumer": "src/train.py, src/evaluate.py",
                "contract": {"prediction": cls._value(fields, "outputs")},
                "evidence_fields": ["outputs", "objective", "metrics"],
            },
        ]

    @classmethod
    def _training_plan(cls, fields: dict) -> list[dict]:
        return [
            {"step": "prepare_data", "detail": cls._value(fields, "preprocessing"), "evidence_fields": ["datasets", "preprocessing"]},
            {"step": "initialize_model", "detail": cls._value(fields, "model_components"), "evidence_fields": ["model_components"]},
            {"step": "optimize", "detail": cls._value(fields, "objective"), "evidence_fields": ["objective", "training_setup"]},
            {"step": "evaluate", "detail": cls._value(fields, "metrics"), "evidence_fields": ["metrics", "reported_results"]},
        ]

    @classmethod
    def _configuration_schema(cls, fields: dict) -> dict:
        return {
            "dataset": {"type": "string", "required": True, "paper_value": cls._value(fields, "datasets")},
            "model": {"type": "object", "required": True, "paper_value": cls._value(fields, "model_components")},
            "optimizer": {"type": "object", "required": True, "paper_value": cls._value(fields, "training_setup")},
            "objective": {"type": "string", "required": True, "paper_value": cls._value(fields, "objective")},
            "metrics": {"type": "list[string]", "required": True, "paper_value": cls._value(fields, "metrics")},
            "seed": {"type": "integer", "required": True, "paper_value": None, "assumption_required": True},
        }

    @classmethod
    def _evidence_map(cls, fields: dict) -> dict:
        return {
            name: {
                "citations": field.get("citations", ""),
                "evidence": field.get("evidence", []),
                "confidence": field.get("confidence", 0.0),
            }
            for name, field in fields.items()
        }

    @classmethod
    def _assumptions(cls, fields: dict, missing: list[str], family: str) -> list[dict]:
        assumptions = [
            {
                "id": f"missing_{field}",
                "category": "missing_paper_detail",
                "description": f"{field} is not supported by sufficient paper evidence and must be specified before code generation.",
                "status": "open",
            }
            for field in missing
        ]
        assumptions.append({
            "id": "runtime_scope",
            "category": "baseline_scope",
            "description": f"Generate a single-machine {family} baseline with a configurable random seed.",
            "status": "open",
        })
        return assumptions
