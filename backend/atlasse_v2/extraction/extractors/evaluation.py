"""EvaluationExtractor — extracts evaluation protocol from experiments/results."""

from atlasse_v2.core.models import EvidenceSpan, ExtractedField, Provenance, ResearchChunk
from atlasse_v2.core.types import EntityType, SectionType
from atlasse_v2.extraction.base_extractor import BaseExtractor


class EvaluationExtractor(BaseExtractor):
    field_name = "evaluation"
    entity_type = EntityType.EXPERIMENT
    target_sections = [SectionType.EXPERIMENTS, SectionType.RESULTS]
    evidence_query = "how is the model evaluated splits baselines comparison protocol"

    def _extract_from_evidence(self, evidence: list[ResearchChunk]) -> ExtractedField:
        best = evidence[0]
        return ExtractedField(
            value=best.text[:800],
            supporting_spans=[EvidenceSpan(text=best.text, provenance=Provenance(page=best.page, section=best.section))],
            confidence=0.65,
        )
