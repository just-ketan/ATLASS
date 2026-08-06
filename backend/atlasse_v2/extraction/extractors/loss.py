"""LossExtractor — extracts loss/objective function from method section."""

from atlasse_v2.core.models import EvidenceSpan, ExtractedField, Provenance, ResearchChunk
from atlasse_v2.core.types import EntityType, SectionType
from atlasse_v2.extraction.base_extractor import BaseExtractor


class LossExtractor(BaseExtractor):
    field_name = "loss"
    entity_type = EntityType.LOSS
    target_sections = [SectionType.METHOD, SectionType.EXPERIMENTS]
    evidence_query = "what loss function or objective is used for training"

    def _extract_from_evidence(self, evidence: list[ResearchChunk]) -> ExtractedField:
        if not evidence:
            return self._missing_field()
        best = evidence[0]
        return ExtractedField(
            value=best.text[:500],
            supporting_spans=[EvidenceSpan(text=best.text, provenance=Provenance(page=best.page, section=best.section))],
            confidence=0.65,
        )
