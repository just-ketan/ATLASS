"""Base class for dedicated field extractors.

Each extractor:
- retrieves only relevant evidence
- asks a focused prompt
- returns value, supporting spans, confidence, citations, missing fields
- does NOT answer outside retrieved evidence
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from atlasse_v2.core.models import ExtractedField, ResearchChunk
from atlasse_v2.core.types import EntityType, SectionType


class BaseExtractor(ABC):
    field_name: str = ""
    entity_type: EntityType | None = None
    target_sections: list[SectionType] = []
    evidence_query: str = ""

    def __init__(self, retriever, llm_client=None):
        self.retriever = retriever
        self.llm = llm_client

    def extract(self, paper_id: str) -> ExtractedField:
        evidence = self.retriever.retrieve(
            query=self.evidence_query or self.field_name,
            paper_id=paper_id,
            sections=self.target_sections,
            top_k=5,
        )
        if not evidence:
            return ExtractedField(value=None, missing=True, confidence=0.0)

        return self._extract_from_evidence(evidence)

    @abstractmethod
    def _extract_from_evidence(self, evidence: list[ResearchChunk]) -> ExtractedField:
        """Extract field value strictly from provided evidence spans."""

    def _missing_field(self) -> ExtractedField:
        return ExtractedField(
            value=None,
            missing=True,
            confidence=0.0,
            citations=[],
        )
