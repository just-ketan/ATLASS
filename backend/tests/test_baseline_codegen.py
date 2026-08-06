"""Tests for baseline template file generation."""

from atlasse_v2.core.models import EvidenceSpan, ExtractedField, Provenance
from atlasse_v2.core.types import SectionType
from atlasse_v2.graph.semantic_graph import SemanticPaperGraph
from atlasse_v2.baseline.baseline_generator import BaselineGenerator
from atlasse_v2.core.types import ModelFamily


def _lora_graph_and_spec():
    graph = SemanticPaperGraph("lora_codegen")
    graph.build_from_extracted({
        "method": ExtractedField(
            value="LoRA low-rank adaptation with RoBERTa base model",
            supporting_spans=[EvidenceSpan(text="LoRA", provenance=Provenance(section=SectionType.METHOD))],
            confidence=0.85,
        ),
        "dataset": ExtractedField(
            value="GLUE benchmark",
            supporting_spans=[EvidenceSpan(text="GLUE", provenance=Provenance(section=SectionType.EXPERIMENTS))],
            confidence=0.8,
        ),
    })
    spec = {
        "version": 1,
        "fields": {
            "method": {"value": "LoRA low-rank adaptation"},
            "dataset": {"value": "GLUE benchmark"},
            "training": {"value": "Adam", "missing": False},
        },
    }
    return graph, spec


def test_lora_baseline_writes_project_files(tmp_path):
    graph, spec = _lora_graph_and_spec()
    gen = BaselineGenerator(graph, spec=spec)
    baseline = gen.generate("lora_codegen")
    assert baseline["supported"]
    assert baseline["family"] == ModelFamily.LORA.value
    assert baseline["family"] != ModelFamily.MLP.value
    gen.save(baseline, base_dir=str(tmp_path))

    project = tmp_path / "lora_codegen" / "project"
    assert (project / "src/model/lora.py").exists()
    assert (project / "src/model/base_model.py").exists()
    assert (project / "manifest.json").exists()
    lora_src = (project / "src/model/lora.py").read_text()
    assert "LoRALayer" in lora_src
    manifest = __import__("json").loads((project / "manifest.json").read_text())
    assert manifest[0]["evidence_entity_ids"]
    assert manifest[0]["spec_fields"]
