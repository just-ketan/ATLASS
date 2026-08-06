"""Phase 8: Derive blueprint from architecture graph — never from GPT imagination."""

from __future__ import annotations

import json
from pathlib import Path

from atlasse_v2.core.types import EntityType
from atlasse_v2.graph.semantic_graph import SemanticPaperGraph


class BlueprintGenerator:
    BLUEPRINT_DIR = "data/v2/blueprints"

    MODULE_MAP = {
        "encoder": "src/model/encoder.py",
        "decoder": "src/model/decoder.py",
        "attention": "src/model/attention.py",
        "tokenizer": "src/data/tokenizer.py",
        "transformer": "src/model/transformer.py",
        "lora": "src/model/lora.py",
        "loss": "src/training/loss.py",
        "optimizer": "src/training/optimizer.py",
        "dataset": "src/data/dataset.py",
        "train": "src/train.py",
        "evaluate": "src/evaluate.py",
    }

    def __init__(self, graph: SemanticPaperGraph):
        self.graph = graph

    def generate(self, paper_id: str) -> dict:
        modules = []
        architecture_entities = self.graph.get_entities_by_type(EntityType.MODEL)
        architecture_entities += self.graph.get_entities_by_type(EntityType.MODULE)
        architecture_entities += self.graph.get_entities_by_type(EntityType.METHOD)

        for entity in architecture_entities:
            name_lower = entity.normalized_name.lower()
            for keyword, filepath in self.MODULE_MAP.items():
                if keyword in name_lower or keyword in entity.text.lower():
                    modules.append({
                        "module": entity.normalized_name,
                        "file": filepath,
                        "evidence_entity_id": entity.entity_id,
                        "confidence": entity.confidence,
                        "provenance": {
                            "page": entity.provenance.page,
                            "section": str(entity.provenance.section),
                        },
                    })

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
            "data_flow": [],
            "training_flow": [],
            "evaluation_flow": [],
            "dependencies": [],
        }

    def save(self, blueprint: dict, base_dir: str | None = None) -> str:
        paper_id = blueprint["paper_id"]
        base = Path(base_dir or self.BLUEPRINT_DIR) / paper_id
        base.mkdir(parents=True, exist_ok=True)
        path = base / "blueprint.json"
        path.write_text(json.dumps(blueprint, indent=2))
        return str(path)
