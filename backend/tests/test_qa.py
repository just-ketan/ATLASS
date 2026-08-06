"""Tests for QA pipeline with evidence validation."""

from tests.conftest import make_sample_document

from atlasse_v2.core.types import SectionType
from atlasse_v2.memory.research_memory import ResearchMemory
from atlasse_v2.qa.qa_pipeline import MISSING_RESPONSE, QAPipeline
from atlasse_v2.retrieval.evidence_ranker import EvidenceRanker


def _qa_pipeline() -> QAPipeline:
    doc = make_sample_document()
    memory = ResearchMemory(doc.paper_id).build_from_document(doc)
    ranker = EvidenceRanker(memory, use_cross_encoder=False)
    return QAPipeline(ranker, score_threshold=0.5)


def test_dataset_question_returns_experiment_evidence():
    qa = _qa_pipeline()
    result = qa.ask("what datasets are used in this paper", "lora_sample")
    assert result["answer"] != MISSING_RESPONSE
    assert result["intent"] == "dataset"
    assert result["citation_verified"]
    assert result["provenance"][0]["section"] in (
        SectionType.EXPERIMENTS.value,
        SectionType.DATASETS.value,
        SectionType.APPENDIX.value,
    )


def test_low_confidence_returns_missing():
    doc = make_sample_document()
    memory = ResearchMemory(doc.paper_id).build_from_document(doc)
    ranker = EvidenceRanker(memory, use_cross_encoder=False)
    qa = QAPipeline(ranker, score_threshold=999.0)
    result = qa.ask("what datasets are used", "lora_sample")
    assert result["answer"] == MISSING_RESPONSE
    assert result["missing_reason"] == "low_confidence"
