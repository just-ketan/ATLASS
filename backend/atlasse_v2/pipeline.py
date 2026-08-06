"""End-to-end v2 paper processing pipeline."""

from __future__ import annotations

from pathlib import Path

from atlasse_v2.extraction.registry import EXTRACTORS
from atlasse_v2.graph.semantic_graph import SemanticPaperGraph
from atlasse_v2.memory.research_memory import ResearchMemory
from atlasse_v2.parsing.document_parser import DocumentParser
from atlasse_v2.parsing.document_store import DocumentStore
from atlasse_v2.retrieval.evidence_ranker import EvidenceRanker
from atlasse_v2.specification.spec_builder import SpecBuilder


class PaperPipeline:
    """Orchestrates Phase 1 → 5 → 4 → 3 → 2 for a single paper."""

    def __init__(self, data_dir: str = "data/v2"):
        self.data_dir = data_dir
        self.parser = DocumentParser()

    def ingest(self, pdf_path: str | Path, paper_id: str | None = None) -> dict:
        pdf_path = Path(pdf_path)
        paper_id = paper_id or pdf_path.stem

        document = self.parser.parse(pdf_path, paper_id=paper_id)
        DocumentStore.save(document, base_dir=f"{self.data_dir}/parsed")

        memory = ResearchMemory(paper_id).build_from_document(document)
        memory.save(base_dir=f"{self.data_dir}/memory_indices")

        ranker = EvidenceRanker(memory)
        graph = SemanticPaperGraph(paper_id).build_from_document(document)

        extracted = {}
        for name, extractor_cls in EXTRACTORS.items():
            extractor = extractor_cls(retriever=ranker)
            extracted[name] = extractor.extract(paper_id)

        from atlasse_v2.core.models import Provenance
        from atlasse_v2.core.types import EntityType

        for field_name, field in extracted.items():
            for entity_type in ("dataset", "method", "metric", "contribution", "limitation"):
                if field_name == entity_type and field.value and not field.missing:
                    provenance = (
                        field.supporting_spans[0].provenance
                        if field.supporting_spans
                        else Provenance()
                    )
                    graph.add_entity(
                        EntityType(entity_type),
                        text=field.value[:500],
                        normalized_name=field_name,
                        provenance=provenance,
                        confidence=field.confidence,
                    )

        graph.save(base_dir=f"{self.data_dir}/knowledge_graphs")

        spec_builder = SpecBuilder(ranker)
        spec = spec_builder.build(paper_id)
        spec_builder.save(spec, base_dir=f"{self.data_dir}/specifications")

        return {
            "paper_id": paper_id,
            "title": document.title,
            "section_count": len(document.section_tree),
            "paragraph_count": len(document.paragraphs),
            "chunk_count": len(memory.chunks),
            "entity_count": len(graph.entities),
            "parser_backend": document.metadata.get("parser_backend"),
            "extracted_fields": {
                name: {
                    "value": f.value[:200] if f.value else None,
                    "confidence": f.confidence,
                    "missing": f.missing,
                }
                for name, f in extracted.items()
            },
        }

    def get_status(self, paper_id: str) -> dict:
        parsed = DocumentStore.load(paper_id, base_dir=f"{self.data_dir}/parsed")
        memory = ResearchMemory.load(paper_id, base_dir=f"{self.data_dir}/memory_indices")
        graph = SemanticPaperGraph.load(paper_id, base_dir=f"{self.data_dir}/knowledge_graphs")
        spec_path = Path(f"{self.data_dir}/specifications") / paper_id / "system_spec.json"
        return {
            "paper_id": paper_id,
            "parsed": parsed is not None,
            "memory_chunks": len(memory.chunks),
            "graph_entities": len(graph.entities),
            "has_spec": spec_path.exists(),
        }

    def get_spec(self, paper_id: str) -> dict | None:
        spec_path = Path(f"{self.data_dir}/specifications") / paper_id / "system_spec.json"
        if not spec_path.exists():
            return None
        import json
        return json.loads(spec_path.read_text())

    def get_graph(self, paper_id: str) -> SemanticPaperGraph:
        return SemanticPaperGraph.load(paper_id, base_dir=f"{self.data_dir}/knowledge_graphs")
