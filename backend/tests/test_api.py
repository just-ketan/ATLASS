"""API tests for blueprint, baseline, and spec quality endpoints."""

import json

from tests.conftest import make_sample_document

from atlasse_v2.graph.semantic_graph import SemanticPaperGraph
from atlasse_v2.memory.research_memory import ResearchMemory
from atlasse_v2.parsing.document_store import DocumentStore
from atlasse_v2.pipeline import PaperPipeline
from atlasse_v2.blueprint.blueprint_generator import BlueprintGenerator
from atlasse_v2.baseline.baseline_generator import BaselineGenerator
from atlasse_v2.specification.spec_builder import SpecBuilder
from atlasse_v2.retrieval.evidence_ranker import EvidenceRanker


def _seed_artifacts(tmp_path, paper_id="lora_sample"):
    doc = make_sample_document()
    DocumentStore.save(doc, base_dir=str(tmp_path / "parsed"))
    memory = ResearchMemory(paper_id).build_from_document(doc)
    memory.save(base_dir=str(tmp_path / "memory_indices"))
    ranker = EvidenceRanker(memory, use_cross_encoder=False)
    spec = SpecBuilder(ranker).build(paper_id)
    SpecBuilder(ranker).save(spec, base_dir=str(tmp_path / "specifications"))
    graph = SemanticPaperGraph(paper_id)
    graph.build_from_document(doc)
    BlueprintGenerator(graph, spec=spec).save(
        BlueprintGenerator(graph, spec=spec).generate(paper_id),
        base_dir=str(tmp_path / "blueprints"),
    )
    BaselineGenerator(graph, spec=spec).save(
        BaselineGenerator(graph, spec=spec).generate(paper_id),
        base_dir=str(tmp_path / "baselines"),
    )


def test_api_blueprint_and_baseline(tmp_path):
    from fastapi.testclient import TestClient
    from atlasse_v2.api.app import create_app

    _seed_artifacts(tmp_path)
    client = TestClient(create_app(data_dir=str(tmp_path)))

    bp = client.get("/v2/papers/lora_sample/blueprint")
    assert bp.status_code == 200
    assert bp.json()["paper_id"] == "lora_sample"

    bl = client.get("/v2/papers/lora_sample/baseline")
    assert bl.status_code == 200
    assert "family" in bl.json()

    heatmap = client.get("/v2/papers/lora_sample/confidence-heatmap")
    assert heatmap.status_code == 200
    assert "dataset" in heatmap.json()["fields"]

    missing = client.get("/v2/papers/lora_sample/missing-fields")
    assert missing.status_code == 200
    assert "missing_fields" in missing.json()


def test_spec_fields_distinct(tmp_path):
    doc = make_sample_document()
    memory = ResearchMemory(doc.paper_id).build_from_document(doc)
    ranker = EvidenceRanker(memory, use_cross_encoder=False)
    spec = SpecBuilder(ranker).build(doc.paper_id)
    assert spec["fields"]["dataset"]["value"] != spec["fields"]["problem"]["value"]
