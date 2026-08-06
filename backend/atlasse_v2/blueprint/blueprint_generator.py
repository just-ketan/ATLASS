"""Phase 8: Derive blueprint from architecture graph — never from GPT imagination."""

from __future__ import annotations

import json
from pathlib import Path

from atlasse_v2.blueprint.flow_derivation import derive_flows
from atlasse_v2.core.types import EntityType
from atlasse_v2.graph.semantic_graph import SemanticPaperGraph


class BlueprintGenerator:
    BLUEPRINT_DIR = "data/v2/blueprints"

    MODULE_KEYWORDS = {
        "encoder": "src/model/encoder.py",
        "decoder": "src/model/decoder.py",
        "attention": "src/model/attention.py",
        "tokenizer": "src/data/tokenizer.py",
        "transformer": "src/model/transformer.py",
        "lora": "src/model/lora.py",
        "loss": "src/training/loss.py",
        "optimizer": "src/training/optimizer.py",
        "dataset": "src/data/dataset.py",
        "convolution": "src/model/cnn.py",
        "resnet": "src/model/cnn.py",
        "cnn": "src/model/cnn.py",
        "diffusion": "src/model/diffusion.py",
        "denoising": "src/model/diffusion.py",
        "unet": "src/model/unet.py",
        "vit": "src/model/vit.py",
        "vision transformer": "src/model/vit.py",
    }

    RUNTIME_MODULES = {
        "train": "src/train.py",
        "evaluate": "src/evaluate.py",
    }

    def __init__(self, graph: SemanticPaperGraph, spec: dict | None = None):
        self.graph = graph
        self.spec = spec or {}

    def generate(self, paper_id: str) -> dict:
        modules = self._decompose_modules()
        flows = derive_flows(self.graph, self.spec)

        if not modules:
            modules.append({
                "module": "unsupported",
                "file": None,
                "evidence_entity_id": None,
                "confidence": 0.0,
                "note": "No architecture entities found in graph — blueprint cannot be generated from evidence.",
            })

        return {
            "paper_id": paper_id,
            "version": 1,
            "modules": modules,
            **flows,
        }

    def _decompose_modules(self) -> list[dict]:
        seen_files: set[str] = set()
        modules: list[dict] = []

        arch_types = (EntityType.MODEL, EntityType.MODULE, EntityType.METHOD)
        for entity_type in arch_types:
            for entity in self.graph.get_entities_by_type(entity_type):
                matched = self._match_module(entity.normalized_name, entity.text)
                for entry in matched:
                    if entry["file"] in seen_files:
                        continue
                    seen_files.add(entry["file"])
                    modules.append(entry)

        if modules and self.graph.get_entities_by_type(EntityType.METHOD):
            for key, path in self.RUNTIME_MODULES.items():
                if path not in seen_files:
                    seen_files.add(path)
                    modules.append({
                        "module": key,
                        "file": path,
                        "evidence_entity_id": self.graph.get_entities_by_type(EntityType.METHOD)[0].entity_id,
                        "confidence": 0.6,
                        "provenance": {"source": "method_entity_required"},
                    })

        return modules

    def _match_module(self, name: str, text: str) -> list[dict]:
        combined = f"{name} {text}".lower()
        results = []
        for keyword, filepath in self.MODULE_KEYWORDS.items():
            if keyword in combined:
                entity = self._find_entity_for_keyword(keyword)
                if entity is None:
                    continue
                results.append({
                    "module": name or keyword,
                    "file": filepath,
                    "evidence_entity_id": entity.entity_id,
                    "confidence": entity.confidence,
                    "provenance": {
                        "page": entity.provenance.page,
                        "section": str(entity.provenance.section),
                    },
                })
        return results

    def _find_entity_for_keyword(self, keyword: str) -> object | None:
        for entity in self.graph.entities.values():
            blob = f"{entity.normalized_name} {entity.text}".lower()
            if keyword in blob:
                return entity
        return None

    def save(self, blueprint: dict, base_dir: str | None = None) -> str:
        paper_id = blueprint["paper_id"]
        base = Path(base_dir or self.BLUEPRINT_DIR) / paper_id
        base.mkdir(parents=True, exist_ok=True)
        path = base / "blueprint.json"
        prev_path = base / "blueprint_prev.json"
        if path.exists():
            path.replace(prev_path)
        path.write_text(json.dumps(blueprint, indent=2))
        return str(path)

    @classmethod
    def load_prev(cls, paper_id: str, base_dir: str | None = None) -> dict | None:
        path = Path(base_dir or cls.BLUEPRINT_DIR) / paper_id / "blueprint_prev.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())
