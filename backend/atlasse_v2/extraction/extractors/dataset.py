"""DatasetExtractor — extracts datasets from experiments/datasets sections only."""

from atlasse_v2.core.models import EvidenceSpan, ExtractedField, Provenance, ResearchChunk
from atlasse_v2.core.types import EntityType, SectionType
from atlasse_v2.extraction.base_extractor import BaseExtractor


class DatasetExtractor(BaseExtractor):
    field_name = "dataset"
    entity_type = EntityType.DATASET
    target_sections = [SectionType.DATASETS, SectionType.EXPERIMENTS, SectionType.APPENDIX]
    evidence_query = "what datasets or benchmarks are used in experiments"

    def _extract_from_evidence(self, evidence: list[ResearchChunk]) -> ExtractedField:
        if not evidence:
            return self._missing_field()
        combined = "; ".join(c.text[:200] for c in evidence[:3])
        return ExtractedField(
            value=combined,
            supporting_spans=[
                EvidenceSpan(text=c.text, provenance=Provenance(page=c.page, section=c.section))
                for c in evidence[:3]
            ],
            confidence=0.75,
        )
