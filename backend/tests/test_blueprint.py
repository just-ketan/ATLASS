"""Tests for evidence-derived blueprint generation."""

from atlasse_v2.core.models import EvidenceSpan, ExtractedField, Provenance
from atlasse_v2.core.types import EntityType, SectionType
from atlasse_v2.graph.semantic_graph import SemanticPaperGraph
from atlasse_v2.blueprint.blueprint_generator import BlueprintGenerator
from atlasse_v2.blueprint.blueprint_diff import diff_blueprints


def _graph_and_spec():
    graph = SemanticPaperGraph("lora_bp")
    extracted = {
        "method": ExtractedField(
            value="LoRA injects low-rank adaptation matrices into attention layers.",
            supporting_spans=[EvidenceSpan(text="LoRA", provenance=Provenance(section=SectionType.METHOD))],
            confidence=0.8,
        ),
        "dataset": ExtractedField(
            value="GLUE benchmark evaluation",
            supporting_spans=[EvidenceSpan(text="GLUE", provenance=Provenance(section=SectionType.EXPERIMENTS))],
            confidence=0.75,
        ),
        "loss": ExtractedField(
            value="cross-entropy loss",
            supporting_spans=[EvidenceSpan(text="loss", provenance=Provenance(section=SectionType.METHOD))],
            confidence=0.7,
        ),
    }
    graph.build_from_extracted(extracted)
    spec = {
        "paper_id": "lora_bp",
        "version": 1,
        "fields": {
            "method": {"value": extracted["method"].value},
            "dataset": {"value": extracted["dataset"].value},
            "metric": {"value": "accuracy and F1"},
            "training": {"value": "Adam optimizer"},
        },
    }
    return graph, spec


def test_blueprint_modules_from_graph_evidence():
    graph, spec = _graph_and_spec()
    bp = BlueprintGenerator(graph, spec=spec).generate("lora_bp")
    files = [m["file"] for m in bp["modules"] if m.get("file")]
    assert "src/model/lora.py" in files
    assert bp["data_flow"]
    assert bp["training_flow"]
    assert "torch" in bp["dependencies"]


def test_blueprint_diff_detects_changes():
    old = {"paper_id": "p", "version": 1, "modules": [{"file": "src/train.py"}], "data_flow": []}
    new = {"paper_id": "p", "version": 2, "modules": [{"file": "src/train.py"}, {"file": "src/model/lora.py"}], "data_flow": ["x"]}
    diff = diff_blueprints(old, new)
    assert len(diff["modules_added"]) == 1
    assert diff["flows_changed"]["data_flow"]
