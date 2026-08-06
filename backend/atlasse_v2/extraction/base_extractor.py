"""Base class for dedicated field extractors.

Each extractor:
- retrieves only relevant evidence
- asks a focused prompt
- returns value, supporting spans, confidence, citations, missing fields
- does NOT answer outside retrieved evidence
"""

from __future__ import annotations

from abc import ABC

import re

from atlasse_v2.core.models import ExtractedField, ResearchChunk
from atlasse_v2.core.types import EntityType, SectionType
from atlasse_v2.extraction.evidence_gate import extract_span_bound_sentences


class BaseExtractor(ABC):
    field_name: str = ""
    entity_type: EntityType | None = None
    target_sections: list[SectionType] = []
    evidence_query: str = ""

    def __init__(self, retriever, llm_client=None):
        self.retriever = retriever
        self.llm = llm_client

    def extract(self, paper_id: str) -> ExtractedField:
        if hasattr(self.retriever, "retrieve_with_trace"):
            evidence, trace = self.retriever.retrieve_with_trace(
                query=self.evidence_query or self.field_name,
                paper_id=paper_id,
                sections=self.target_sections,
                top_k=5,
            )
        else:
            evidence = self.retriever.retrieve(
                query=self.evidence_query or self.field_name,
                paper_id=paper_id,
                sections=self.target_sections,
                top_k=5,
            )
            trace = None

        if not evidence:
            return self._missing_field()

        result = self._extract_from_evidence(evidence)
        if trace and trace.get("ranked"):
            top_score = trace["ranked"][0]["score"]
            result.confidence = min(result.confidence, min(top_score / 5.0, 1.0))
            if top_score < 0.5:
                result.missing = True
                result.value = None
        return result

    def _extract_from_evidence(self, evidence: list[ResearchChunk]) -> ExtractedField:
        terms = self._evidence_terms()
        return extract_span_bound_sentences(evidence, query_terms=terms, max_sentences=3)

    def _evidence_terms(self) -> list[str]:
        raw = (self.evidence_query or self.field_name or "").lower()
        return [t for t in re.findall(r"[a-z0-9]+", raw) if len(t) > 2]

    def _missing_field(self) -> ExtractedField:
        return ExtractedField(
            value=None,
            missing=True,
            confidence=0.0,
            citations=[],
        )
