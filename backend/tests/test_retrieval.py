"""Tests for ATLASS v2 evidence ranking."""

from atlasse_v2.core.models import ParsedDocument, SectionNode
from atlasse_v2.core.types import SectionType
from atlasse_v2.memory.research_memory import ResearchMemory
from atlasse_v2.retrieval.evidence_ranker import EvidenceRanker


def _make_document() -> ParsedDocument:
    intro = SectionNode(
        section_id="sec_0",
        title="Introduction",
        section_type=SectionType.INTRODUCTION,
        level=1,
        page_start=1,
        page_end=1,
        text="We address the problem of fine-tuning large language models efficiently.",
        paragraph_ids=["p_intro"],
    )
    exp = SectionNode(
        section_id="sec_1",
        title="Experiments",
        section_type=SectionType.EXPERIMENTS,
        level=1,
        page_start=5,
        page_end=6,
        text="We evaluate on GLUE benchmark with RoBERTa base model.",
        paragraph_ids=["p_exp"],
    )
    return ParsedDocument(
        paper_id="test_paper",
        title="Test Paper",
        section_tree=[intro, exp],
        paragraphs={
            "p_intro": "We address the problem of fine-tuning large language models efficiently.",
            "p_exp": "We evaluate on GLUE benchmark with RoBERTa base model.",
        },
    )


def test_dataset_query_prefers_experiments_section():
    doc = _make_document()
    memory = ResearchMemory("test_paper").build_from_document(doc)
    ranker = EvidenceRanker(memory)
    results = ranker.retrieve(
        query="what datasets are used in experiments",
        sections=[SectionType.EXPERIMENTS, SectionType.DATASETS],
        top_k=1,
    )
    assert len(results) == 1
    assert results[0].paragraph_id == "p_exp"


def test_problem_query_from_introduction():
    doc = _make_document()
    memory = ResearchMemory("test_paper").build_from_document(doc)
    ranker = EvidenceRanker(memory)
    results = ranker.retrieve(
        query="what problem does this paper address",
        sections=[SectionType.ABSTRACT, SectionType.INTRODUCTION],
        top_k=1,
    )
    assert len(results) == 1
    assert results[0].paragraph_id == "p_intro"


def test_retrieval_trace_captures_scores():
    doc = _make_document()
    memory = ResearchMemory("test_paper").build_from_document(doc)
    ranker = EvidenceRanker(memory)
    _, trace = ranker.retrieve_with_trace(
        query="what datasets are used",
        sections=[SectionType.EXPERIMENTS],
        top_k=2,
    )
    assert trace["query"]
    assert trace["candidate_count"] >= 1
    assert len(trace["ranked"]) <= 2
    assert "score" in trace["ranked"][0]
    assert "components" in trace["ranked"][0]

