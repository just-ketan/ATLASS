"""Tests for graph edge inference from extractors."""

from tests.conftest import make_sample_document

from atlasse_v2.core.models import EvidenceSpan, ExtractedField, Provenance
from atlasse_v2.core.types import EdgeType, EntityType, SectionType
from atlasse_v2.graph.semantic_graph import SemanticPaperGraph


def test_build_from_extracted_creates_edges():
    graph = SemanticPaperGraph("test")
    extracted = {
        "method": ExtractedField(
            value="LoRA adaptation",
            supporting_spans=[
                EvidenceSpan(text="LoRA", provenance=Provenance(section=SectionType.METHOD))
            ],
            confidence=0.8,
        ),
        "dataset": ExtractedField(
            value="GLUE benchmark",
            supporting_spans=[
                EvidenceSpan(text="GLUE", provenance=Provenance(section=SectionType.EXPERIMENTS))
            ],
            confidence=0.75,
        ),
        "metric": ExtractedField(
            value="accuracy and F1",
            supporting_spans=[
                EvidenceSpan(text="F1", provenance=Provenance(section=SectionType.EXPERIMENTS))
            ],
            confidence=0.7,
        ),
    }
    graph.build_from_extracted(extracted)
    assert len(graph.entities) == 3
    assert len(graph.edges) >= 2
    edge_types = {e.edge_type for e in graph.edges}
    assert EdgeType.USES_DATASET in edge_types
    assert EdgeType.REPORTS in edge_types
    assert graph.get_entities_by_type(EntityType.DATASET)
