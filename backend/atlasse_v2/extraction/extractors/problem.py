"""ProblemExtractor — extracts the research problem from introduction/abstract evidence."""

from atlasse_v2.core.models import EvidenceSpan, ExtractedField, Provenance, ResearchChunk
from atlasse_v2.core.types import EntityType, SectionType
from atlasse_v2.extraction.base_extractor import BaseExtractor


class ProblemExtractor(BaseExtractor):
    field_name = "problem"
    entity_type = EntityType.TASK
    target_sections = [SectionType.ABSTRACT, SectionType.INTRODUCTION]
    evidence_query = "what problem or research gap does this paper address"

    def _extract_from_evidence(self, evidence: list[ResearchChunk]) -> ExtractedField:
        best = evidence[0]
        return ExtractedField(
            value=best.text[:1000],
            supporting_spans=[
                EvidenceSpan(
                    text=best.text,
                    provenance=Provenance(
                        page=best.page,
                        section=best.section,
                        paragraph_id=best.paragraph_id,
                        chunk_id=best.chunk_id,
                    ),
                    score=1.0,
                )
            ],
            confidence=0.7,
            citations=best.citations,
        )
