"""Tests for reproduction classification and smoke validation."""

from atlasse_v2.core.types import ReproductionLevel
from atlasse_v2.reproduction.reproduction_engine import ReproductionEngine


def test_reproduction_level_partial_when_training_missing():
    engine = ReproductionEngine()
    baseline = {
        "paper_id": "p1",
        "supported": True,
        "family": "lora",
        "confidence": 0.8,
        "files": [{"path": "src/train.py"}],
        "assumptions": [],
    }
    spec = {
        "fields": {
            "dataset": {"value": "GLUE", "missing": False},
            "training": {"missing": True},
            "metric": {"value": "accuracy", "missing": False},
        },
    }
    level = engine.classify_level(baseline, spec)
    assert level == ReproductionLevel.PARTIAL


def test_never_comparable_when_dataset_missing():
    engine = ReproductionEngine()
    baseline = {"paper_id": "p1", "supported": True, "family": "lora", "assumptions": []}
    spec = {"fields": {"dataset": {"missing": True}, "metric": {"value": "acc"}}}
    report = engine.classify(baseline, spec)
    assert not report["metric_comparable"]
    assert report["comparability_verdict"]["status"] == "not_comparable"


def test_smoke_validate_compiles_lora_project(tmp_path):
    from atlasse_v2.baseline.baseline_generator import BaselineGenerator
    from atlasse_v2.core.models import EvidenceSpan, ExtractedField, Provenance
    from atlasse_v2.core.types import SectionType
    from atlasse_v2.graph.semantic_graph import SemanticPaperGraph

    graph = SemanticPaperGraph("smoke_p")
    graph.build_from_extracted({
        "method": ExtractedField(
            value="LoRA adaptation",
            supporting_spans=[EvidenceSpan(text="LoRA", provenance=Provenance(section=SectionType.METHOD))],
            confidence=0.8,
        ),
    })
    spec = {"fields": {"method": {"value": "LoRA"}, "dataset": {"value": "GLUE", "missing": False}}}
    gen = BaselineGenerator(graph, spec=spec)
    baseline = gen.generate("smoke_p")
    gen.save(baseline, base_dir=str(tmp_path / "baselines"))

    engine = ReproductionEngine()
    report = engine.run_smoke(baseline, spec, data_dir=str(tmp_path))
    assert report["smoke_validation"]["passed"]
    assert report["smoke_validation"]["files_checked"] >= 3
