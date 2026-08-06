"""Tests for graph entity tagging on memory chunks."""

from tests.conftest import make_sample_document

from atlasse_v2.core.models import EvidenceSpan, ExtractedField, Provenance
from atlasse_v2.core.types import SectionType
from atlasse_v2.graph.semantic_graph import SemanticPaperGraph
from atlasse_v2.memory.research_memory import ResearchMemory


def test_tag_from_graph_adds_entity_names():
    doc = make_sample_document()
    memory = ResearchMemory(doc.paper_id).build_from_document(doc)
    graph = SemanticPaperGraph(doc.paper_id)
    extracted = {
        "method": ExtractedField(
            value="LoRA adaptation",
            supporting_spans=[
                EvidenceSpan(text="LoRA", provenance=Provenance(section=SectionType.METHOD))
            ],
            confidence=0.8,
        ),
    }
    graph.build_from_extracted(extracted)
    memory.tag_from_graph(graph)
    tagged = [c for c in memory.chunks.values() if c.entities]
    assert tagged
