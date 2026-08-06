"""MethodExtractor — extracts proposed method from method/architecture sections."""

from atlasse_v2.core.models import EvidenceSpan, ExtractedField, Provenance, ResearchChunk
from atlasse_v2.core.types import EntityType, SectionType
from atlasse_v2.extraction.base_extractor import BaseExtractor


class MethodExtractor(BaseExtractor):
    field_name = "method"
    entity_type = EntityType.METHOD
    target_sections = [SectionType.METHOD, SectionType.ARCHITECTURE]
    evidence_query = "what method or approach is proposed"

    def _extract_from_evidence(self, evidence: list[ResearchChunk]) -> ExtractedField:
        best = evidence[0]
        return ExtractedField(
            value=best.text[:1200],
            supporting_spans=[EvidenceSpan(text=best.text, provenance=Provenance(page=best.page, section=best.section))],
            confidence=0.75,
        )
