"""Tests for end-to-end v2 pipeline on synthetic document."""

from tests.conftest import make_sample_document

from atlasse_v2.memory.research_memory import ResearchMemory
from atlasse_v2.parsing.document_store import DocumentStore
from atlasse_v2.pipeline import PaperPipeline
from atlasse_v2.retrieval.evidence_ranker import EvidenceRanker
from atlasse_v2.specification.spec_builder import SpecBuilder


def test_pipeline_spec_has_distinct_fields(tmp_path):
    doc = make_sample_document()
    DocumentStore.save(doc, base_dir=str(tmp_path / "parsed"))

    memory = ResearchMemory(doc.paper_id).build_from_document(doc)
    memory.save(base_dir=str(tmp_path / "memory_indices"))

    ranker = EvidenceRanker(memory)
    spec = SpecBuilder(ranker).build(doc.paper_id)
    SpecBuilder(ranker).save(spec, base_dir=str(tmp_path / "specifications"))

    assert len(memory.chunks) >= 4
    assert len(spec["fields"]) >= 10
    assert spec["fields"]["dataset"]["value"]
    assert spec["fields"]["problem"]["value"]
    assert spec["fields"]["dataset"]["value"] != spec["fields"]["problem"]["value"]


def test_pipeline_status_reflects_artifacts(tmp_path):
    doc = make_sample_document()
    DocumentStore.save(doc, base_dir=str(tmp_path / "parsed"))
    ResearchMemory(doc.paper_id).build_from_document(doc).save(
        base_dir=str(tmp_path / "memory_indices")
    )

    pipeline = PaperPipeline(data_dir=str(tmp_path))
    status = pipeline.get_status(doc.paper_id)
    assert status["parsed"] is True
    assert status["memory_chunks"] >= 4
