"""LimitationExtractor — extracts limitations from limitations/discussion sections."""

from atlasse_v2.core.models import EvidenceSpan, ExtractedField, Provenance, ResearchChunk
from atlasse_v2.core.types import EntityType, SectionType
from atlasse_v2.extraction.base_extractor import BaseExtractor


class LimitationExtractor(BaseExtractor):
    field_name = "limitation"
    entity_type = EntityType.LIMITATION
    target_sections = [SectionType.LIMITATIONS, SectionType.DISCUSSION]
    evidence_query = "what limitations or drawbacks does the paper acknowledge"

    def _extract_from_evidence(self, evidence: list[ResearchChunk]) -> ExtractedField:
        if not evidence:
            return self._missing_field()
        best = evidence[0]
        return ExtractedField(
            value=best.text[:600],
            supporting_spans=[EvidenceSpan(text=best.text, provenance=Provenance(page=best.page, section=best.section))],
            confidence=0.7,
        )
