"""TaskExtractor — extracts task definition from method/introduction."""

from atlasse_v2.core.models import EvidenceSpan, ExtractedField, Provenance, ResearchChunk
from atlasse_v2.core.types import EntityType, SectionType
from atlasse_v2.extraction.base_extractor import BaseExtractor


class TaskExtractor(BaseExtractor):
    field_name = "task"
    entity_type = EntityType.TASK
    target_sections = [SectionType.INTRODUCTION, SectionType.METHOD]
    evidence_query = "what task or learning problem is defined in this paper"

    def _extract_from_evidence(self, evidence: list[ResearchChunk]) -> ExtractedField:
        best = evidence[0]
        return ExtractedField(
            value=best.text[:800],
            supporting_spans=[EvidenceSpan(text=best.text, provenance=Provenance(page=best.page, section=best.section))],
            confidence=0.65,
        )
