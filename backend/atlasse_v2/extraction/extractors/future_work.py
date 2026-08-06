"""FutureWorkExtractor — extracts future work from conclusion/future work sections."""

from atlasse_v2.core.models import EvidenceSpan, ExtractedField, Provenance, ResearchChunk
from atlasse_v2.core.types import EntityType, SectionType
from atlasse_v2.extraction.base_extractor import BaseExtractor


class FutureWorkExtractor(BaseExtractor):
    field_name = "future_work"
    entity_type = EntityType.FUTURE_WORK
    target_sections = [SectionType.FUTURE_WORK, SectionType.DISCUSSION]
    evidence_query = "what future work or open problems are mentioned"

    def _extract_from_evidence(self, evidence: list[ResearchChunk]) -> ExtractedField:
        if not evidence:
            return self._missing_field()
        best = evidence[0]
        return ExtractedField(
            value=best.text[:600],
            supporting_spans=[EvidenceSpan(text=best.text, provenance=Provenance(page=best.page, section=best.section))],
            confidence=0.65,
        )
