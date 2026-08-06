"""ContributionExtractor — extracts paper contributions from abstract/introduction."""

from atlasse_v2.core.models import EvidenceSpan, ExtractedField, Provenance, ResearchChunk
from atlasse_v2.core.types import EntityType, SectionType
from atlasse_v2.extraction.base_extractor import BaseExtractor


class ContributionExtractor(BaseExtractor):
    field_name = "contribution"
    entity_type = EntityType.CONTRIBUTION
    target_sections = [SectionType.ABSTRACT, SectionType.INTRODUCTION]
    evidence_query = "what are the main contributions of this paper"

    def _extract_from_evidence(self, evidence: list[ResearchChunk]) -> ExtractedField:
        best = evidence[0]
        return ExtractedField(
            value=best.text[:1000],
            supporting_spans=[
                EvidenceSpan(
                    text=best.text,
                    provenance=Provenance(page=best.page, section=best.section, paragraph_id=best.paragraph_id),
                )
            ],
            confidence=0.7,
            citations=best.citations,
        )
