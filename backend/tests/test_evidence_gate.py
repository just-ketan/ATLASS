"""Tests for span-bound evidence gate."""

from atlasse_v2.core.models import ResearchChunk
from atlasse_v2.core.types import SectionType
from atlasse_v2.extraction.evidence_gate import extract_span_bound_sentences


def test_only_sentences_from_evidence():
    chunks = [
        ResearchChunk(
            chunk_id="c1",
            text="We evaluate on GLUE benchmark. Other unrelated sentence.",
            page=5,
            section=SectionType.EXPERIMENTS,
            paragraph_id="p1",
            chunk_type="paragraph",
        ),
    ]
    result = extract_span_bound_sentences(chunks, query_terms=["glue", "benchmark"], max_sentences=1)
    assert result.value
    assert "GLUE" in result.value
    assert "unrelated" not in result.value.lower()


def test_missing_when_no_chunks():
    result = extract_span_bound_sentences([], query_terms=["dataset"])
    assert result.missing
    assert result.value is None
