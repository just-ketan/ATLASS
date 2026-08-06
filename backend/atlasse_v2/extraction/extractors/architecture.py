"""ArchitectureExtractor — extracts model architecture from architecture/method sections."""

from atlasse_v2.core.models import EvidenceSpan, ExtractedField, Provenance, ResearchChunk
from atlasse_v2.core.types import EntityType, SectionType
from atlasse_v2.extraction.base_extractor import BaseExtractor


class ArchitectureExtractor(BaseExtractor):
    field_name = "architecture"
    entity_type = EntityType.MODEL
    target_sections = [SectionType.ARCHITECTURE, SectionType.METHOD]
    evidence_query = "describe the model architecture components and data flow"

    def _extract_from_evidence(self, evidence: list[ResearchChunk]) -> ExtractedField:
        best = evidence[0]
        return ExtractedField(
            value=best.text[:1500],
            supporting_spans=[EvidenceSpan(text=best.text, provenance=Provenance(page=best.page, section=best.section))],
            confidence=0.7,
        )
