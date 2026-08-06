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
    graph.save(base_dir=str(tmp_path / "knowledge_graphs"))
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


def test_api_rich_surfaces(tmp_path):
    from datetime import datetime, timezone
    from fastapi.testclient import TestClient
    from atlasse_v2.agents.base import AgentTrace
    from atlasse_v2.agents.trace_store import AgentTraceStore
    from atlasse_v2.api.app import create_app

    _seed_artifacts(tmp_path)
    trace = AgentTrace(
        paper_id="lora_sample",
        started_at=datetime.now(timezone.utc).isoformat(),
        completed_at=datetime.now(timezone.utc).isoformat(),
        success=True,
    )
    AgentTraceStore().save(trace, base_dir=str(tmp_path / "agent_traces"))

    client = TestClient(create_app(data_dir=str(tmp_path)))

    sections = client.get("/v2/papers/lora_sample/sections")
    assert sections.status_code == 200
    assert sections.json()["sections"]

    evidence = client.get("/v2/papers/lora_sample/evidence")
    assert evidence.status_code == 200
    assert evidence.json()["chunk_count"] > 0

    entities = client.get("/v2/papers/lora_sample/entities")
    assert entities.status_code == 200
    assert entities.json()["entity_count"] >= 0

    dag = client.get("/v2/papers/lora_sample/architecture-dag")
    assert dag.status_code == 200
    assert "nodes" in dag.json()

    assumptions = client.get("/v2/papers/lora_sample/assumptions")
    assert assumptions.status_code == 200
    assert "assumptions" in assumptions.json()

    agent_trace = client.get("/v2/papers/lora_sample/agent-trace")
    assert agent_trace.status_code == 200
    assert agent_trace.json()["paper_id"] == "lora_sample"


def test_spec_fields_distinct(tmp_path):
    doc = make_sample_document()
    memory = ResearchMemory(doc.paper_id).build_from_document(doc)
    ranker = EvidenceRanker(memory, use_cross_encoder=False)
    spec = SpecBuilder(ranker).build(doc.paper_id)
    assert spec["fields"]["dataset"]["value"] != spec["fields"]["problem"]["value"]
