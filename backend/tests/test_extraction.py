"""Tests for dedicated field extractors and section-targeted evidence."""

from tests.conftest import make_sample_document

from atlasse_v2.core.types import SectionType
from atlasse_v2.extraction.extractors.dataset import DatasetExtractor
from atlasse_v2.extraction.extractors.problem import ProblemExtractor
from atlasse_v2.memory.research_memory import ResearchMemory
from atlasse_v2.retrieval.evidence_ranker import EvidenceRanker


def _ranker_from_sample() -> EvidenceRanker:
    doc = make_sample_document()
    memory = ResearchMemory("lora_sample").build_from_document(doc)
    return EvidenceRanker(memory)


def test_dataset_extractor_uses_experiments_section():
    ranker = _ranker_from_sample()
    extractor = DatasetExtractor(retriever=ranker)
    result = extractor.extract("lora_sample")
    assert not result.missing
    assert result.supporting_spans
    section = result.supporting_spans[0].provenance.section
    assert section in (SectionType.EXPERIMENTS, SectionType.DATASETS, SectionType.APPENDIX)
    assert "GLUE" in (result.value or "")


def test_problem_extractor_uses_introduction_section():
    ranker = _ranker_from_sample()
    extractor = ProblemExtractor(retriever=ranker)
    result = extractor.extract("lora_sample")
    assert not result.missing
    assert result.supporting_spans
    section = result.supporting_spans[0].provenance.section
    assert section in (SectionType.ABSTRACT, SectionType.INTRODUCTION)
    assert "problem" in (result.value or "").lower() or "fine-tune" in (result.value or "").lower()


def test_missing_evidence_returns_missing_field():
    ranker = _ranker_from_sample()

    class EmptyRetriever:
        def retrieve_with_trace(self, **kwargs):
            return [], {"ranked": []}

    extractor = DatasetExtractor(retriever=EmptyRetriever())
    result = extractor.extract("lora_sample")
    assert result.missing
    assert result.value is None
