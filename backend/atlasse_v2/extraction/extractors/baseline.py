"""BaselineExtractor — extracts baselines compared against from experiments."""

from atlasse_v2.core.models import EvidenceSpan, ExtractedField, Provenance, ResearchChunk
from atlasse_v2.core.types import EntityType, SectionType
from atlasse_v2.extraction.base_extractor import BaseExtractor


class BaselineExtractor(BaseExtractor):
    field_name = "baseline"
    entity_type = EntityType.BASELINE
    target_sections = [SectionType.EXPERIMENTS, SectionType.RESULTS, SectionType.RELATED_WORK]
    evidence_query = "what baseline methods are compared against in experiments"

    def _extract_from_evidence(self, evidence: list[ResearchChunk]) -> ExtractedField:
        if not evidence:
            return self._missing_field()
        best = evidence[0]
        return ExtractedField(
            value=best.text[:600],
            supporting_spans=[EvidenceSpan(text=best.text, provenance=Provenance(page=best.page, section=best.section))],
            confidence=0.6,
        )
