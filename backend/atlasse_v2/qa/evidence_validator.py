"""Validate retrieved evidence matches intent-required sections."""

from __future__ import annotations

from atlasse_v2.core.models import ResearchChunk
from atlasse_v2.core.types import SectionType
from atlasse_v2.retrieval.evidence_ranker import EvidenceRanker


def section_value(section) -> str:
    return section.value if isinstance(section, SectionType) else str(section)


def validate_evidence(
    intent: str,
    chunks: list[ResearchChunk],
    min_chunks: int = 1,
) -> tuple[bool, str]:
    if len(chunks) < min_chunks:
        return False, "no_evidence"

    allowed = EvidenceRanker.INTENT_SECTIONS.get(intent)
    if not allowed:
        return True, "ok"

    allowed_values = {s.value for s in allowed}
    for chunk in chunks:
        if section_value(chunk.section) in allowed_values:
            return True, "ok"
    return False, "wrong_section"


def filter_valid_evidence(intent: str, chunks: list[ResearchChunk]) -> list[ResearchChunk]:
    allowed = EvidenceRanker.INTENT_SECTIONS.get(intent)
    if not allowed:
        return chunks
    allowed_values = {s.value for s in allowed}
    filtered = [c for c in chunks if section_value(c.section) in allowed_values]
    return filtered if filtered else chunks
