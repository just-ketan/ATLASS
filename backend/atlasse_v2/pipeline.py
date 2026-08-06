"""End-to-end v2 paper processing pipeline."""

from __future__ import annotations

from pathlib import Path

from atlasse_v2.extraction.registry import EXTRACTORS
from atlasse_v2.graph.semantic_graph import SemanticPaperGraph
from atlasse_v2.memory.research_memory import ResearchMemory
from atlasse_v2.parsing.document_parser import DocumentParser
from atlasse_v2.parsing.document_store import DocumentStore
from atlasse_v2.retrieval.evidence_ranker import EvidenceRanker
from atlasse_v2.blueprint.blueprint_generator import BlueprintGenerator
from atlasse_v2.baseline.baseline_generator import BaselineGenerator
from atlasse_v2.reproduction.reproduction_engine import ReproductionEngine
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

        extracted = {}
        for name, extractor_cls in EXTRACTORS.items():
            extractor = extractor_cls(retriever=ranker)
            extracted[name] = extractor.extract(paper_id)

        graph = SemanticPaperGraph(paper_id).build_from_extracted(extracted)
        graph.save(base_dir=f"{self.data_dir}/knowledge_graphs")

        memory.tag_from_graph(graph)
        memory.save(base_dir=f"{self.data_dir}/memory_indices")
        ranker = EvidenceRanker(memory)

        spec_builder = SpecBuilder(ranker)
        spec = spec_builder.build(paper_id)
        spec_builder.save(spec, base_dir=f"{self.data_dir}/specifications")

        blueprint_gen = BlueprintGenerator(graph, spec=spec)
        blueprint = blueprint_gen.generate(paper_id)
        blueprint_gen.save(blueprint, base_dir=f"{self.data_dir}/blueprints")

        baseline_gen = BaselineGenerator(graph, spec=spec)
        baseline = baseline_gen.generate(paper_id)
        baseline_gen.save(baseline, base_dir=f"{self.data_dir}/baselines")

        repro = ReproductionEngine()
        repro_report = repro.build_report(baseline, spec, data_dir=self.data_dir)
        repro.save(repro_report, base_dir=f"{self.data_dir}/reproduction_reports")

        return {
            "paper_id": paper_id,
            "title": document.title,
            "section_count": len(document.section_tree),
            "paragraph_count": len(document.paragraphs),
            "chunk_count": len(memory.chunks),
            "entity_count": len(graph.entities),
            "edge_count": len(graph.edges),
            "blueprint_modules": len(blueprint.get("modules", [])),
            "baseline_family": baseline.get("family"),
            "baseline_supported": baseline.get("supported"),
            "reproduction_level": repro_report.get("level"),
            "metric_comparable": repro_report.get("metric_comparable"),
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
        blueprint_path = Path(f"{self.data_dir}/blueprints") / paper_id / "blueprint.json"
        baseline_path = Path(f"{self.data_dir}/baselines") / paper_id / "baseline.json"
        repro_path = Path(f"{self.data_dir}/reproduction_reports") / paper_id / "reproduction_report.json"
        return {
            "paper_id": paper_id,
            "parsed": parsed is not None,
            "memory_chunks": len(memory.chunks),
            "graph_entities": len(graph.entities),
            "graph_edges": len(graph.edges),
            "has_spec": spec_path.exists(),
            "has_blueprint": blueprint_path.exists(),
            "has_baseline": baseline_path.exists(),
            "has_reproduction_report": repro_path.exists(),
        }

    def get_spec(self, paper_id: str) -> dict | None:
        spec_path = Path(f"{self.data_dir}/specifications") / paper_id / "system_spec.json"
        if not spec_path.exists():
            return None
        import json
        return json.loads(spec_path.read_text())

    def get_graph(self, paper_id: str) -> SemanticPaperGraph:
        return SemanticPaperGraph.load(paper_id, base_dir=f"{self.data_dir}/knowledge_graphs")

    def get_blueprint(self, paper_id: str) -> dict | None:
        path = Path(f"{self.data_dir}/blueprints") / paper_id / "blueprint.json"
        if not path.exists():
            return None
        import json
        return json.loads(path.read_text())

    def get_baseline(self, paper_id: str) -> dict | None:
        path = Path(f"{self.data_dir}/baselines") / paper_id / "baseline.json"
        if not path.exists():
            return None
        import json
        return json.loads(path.read_text())

    def get_blueprint_diff(self, paper_id: str) -> dict | None:
        from atlasse_v2.blueprint.blueprint_diff import diff_blueprints
        from atlasse_v2.blueprint.blueprint_generator import BlueprintGenerator

        current_path = Path(f"{self.data_dir}/blueprints") / paper_id / "blueprint.json"
        if not current_path.exists():
            return None
        import json
        current = json.loads(current_path.read_text())
        previous = BlueprintGenerator.load_prev(paper_id, base_dir=f"{self.data_dir}/blueprints")
        if previous is None:
            return {"paper_id": paper_id, "has_previous": False, "current_version": current.get("version")}
        return {"paper_id": paper_id, "has_previous": True, "diff": diff_blueprints(previous, current)}

    def get_missing_fields(self, paper_id: str) -> dict | None:
        spec = self.get_spec(paper_id)
        if spec is None:
            return None
        missing = []
        for name, field in spec.get("fields", {}).items():
            if field.get("missing") or not field.get("value"):
                missing.append({
                    "field": name,
                    "confidence": field.get("confidence", 0.0),
                    "assumptions": field.get("assumptions", []),
                })
        return {"paper_id": paper_id, "missing_fields": missing, "count": len(missing)}

    def get_confidence_heatmap(self, paper_id: str) -> dict | None:
        spec = self.get_spec(paper_id)
        if spec is None:
            return None
        heatmap = {}
        for name, field in spec.get("fields", {}).items():
            heatmap[name] = {
                "confidence": field.get("confidence", 0.0),
                "missing": field.get("missing", False),
                "has_value": bool(field.get("value")),
            }
        return {"paper_id": paper_id, "fields": heatmap}

    def get_reproduction_report(self, paper_id: str) -> dict | None:
        return ReproductionEngine.load(
            paper_id,
            base_dir=f"{self.data_dir}/reproduction_reports",
        )
