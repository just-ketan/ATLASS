"""MetricExtractor — extracts evaluation metrics from experiments/results."""

from atlasse_v2.core.models import EvidenceSpan, ExtractedField, Provenance, ResearchChunk
from atlasse_v2.core.types import EntityType, SectionType
from atlasse_v2.extraction.base_extractor import BaseExtractor


class MetricExtractor(BaseExtractor):
    field_name = "metric"
    entity_type = EntityType.METRIC
    target_sections = [SectionType.EXPERIMENTS, SectionType.RESULTS]
    evidence_query = "what evaluation metrics are reported in this paper"

    def _extract_from_evidence(self, evidence: list[ResearchChunk]) -> ExtractedField:
        best = evidence[0]
        return ExtractedField(
            value=best.text[:600],
            supporting_spans=[EvidenceSpan(text=best.text, provenance=Provenance(page=best.page, section=best.section))],
            confidence=0.7,
        )
