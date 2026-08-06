"""TrainingExtractor — extracts training setup from experiments/implementation."""

from atlasse_v2.core.models import EvidenceSpan, ExtractedField, Provenance, ResearchChunk
from atlasse_v2.core.types import EntityType, SectionType
from atlasse_v2.extraction.base_extractor import BaseExtractor


class TrainingExtractor(BaseExtractor):
    field_name = "training"
    entity_type = EntityType.HYPERPARAMETER
    target_sections = [SectionType.EXPERIMENTS, SectionType.IMPLEMENTATION]
    evidence_query = "what training hyperparameters optimizer learning rate batch size epochs"

    def _extract_from_evidence(self, evidence: list[ResearchChunk]) -> ExtractedField:
        if not evidence:
            return self._missing_field()
        best = evidence[0]
        return ExtractedField(
            value=best.text[:800],
            supporting_spans=[EvidenceSpan(text=best.text, provenance=Provenance(page=best.page, section=best.section))],
            confidence=0.6,
        )
