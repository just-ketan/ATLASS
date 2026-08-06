"""Specialized agents — each returns structured AgentResult payloads."""

from __future__ import annotations

import time
from pathlib import Path

from atlasse_v2.agents.base import AgentResult
from atlasse_v2.baseline.baseline_generator import BaselineGenerator
from atlasse_v2.blueprint.blueprint_generator import BlueprintGenerator
from atlasse_v2.evaluation.benchmark import BenchmarkSuite
from atlasse_v2.extraction.registry import EXTRACTORS
from atlasse_v2.graph.semantic_graph import SemanticPaperGraph
from atlasse_v2.memory.research_memory import ResearchMemory
from atlasse_v2.parsing.document_parser import DocumentParser
from atlasse_v2.parsing.document_store import DocumentStore
from atlasse_v2.reproduction.reproduction_engine import ReproductionEngine
from atlasse_v2.retrieval.evidence_ranker import EvidenceRanker
from atlasse_v2.specification.spec_builder import SpecBuilder


class DocumentAgent:
    name = "document_agent"

    def run(self, pdf_path: str, paper_id: str, data_dir: str) -> AgentResult:
        start = time.monotonic()
        parser = DocumentParser()
        document = parser.parse(pdf_path, paper_id=paper_id)
        DocumentStore.save(document, base_dir=f"{data_dir}/parsed")
        return AgentResult(
            agent_name=self.name,
            success=True,
            output_type="ParsedDocument",
            payload={
                "paper_id": document.paper_id,
                "section_count": len(document.section_tree),
                "paragraph_count": len(document.paragraphs),
            },
            duration_ms=(time.monotonic() - start) * 1000,
        )


class RetrievalAgent:
    name = "retrieval_agent"

    def run(self, document, data_dir: str) -> AgentResult:
        start = time.monotonic()
        memory = ResearchMemory(document.paper_id).build_from_document(document)
        memory.save(base_dir=f"{data_dir}/memory_indices")
        ranker = EvidenceRanker(memory)
        return AgentResult(
            agent_name=self.name,
            success=True,
            output_type="EvidenceRanker",
            payload={"paper_id": document.paper_id, "chunk_count": len(memory.chunks)},
            duration_ms=(time.monotonic() - start) * 1000,
        )


class ResearchAgent:
    name = "research_agent"

    def run(self, paper_id: str, ranker: EvidenceRanker, data_dir: str) -> AgentResult:
        start = time.monotonic()
        extracted = {}
        for name, cls in EXTRACTORS.items():
            extracted[name] = cls(retriever=ranker).extract(paper_id)
        graph = SemanticPaperGraph(paper_id).build_from_extracted(extracted)
        graph.save(base_dir=f"{data_dir}/knowledge_graphs")
        memory = ResearchMemory.load(paper_id, base_dir=f"{data_dir}/memory_indices")
        memory.tag_from_graph(graph)
        memory.save(base_dir=f"{data_dir}/memory_indices")
        return AgentResult(
            agent_name=self.name,
            success=True,
            output_type="SemanticPaperGraph",
            payload={
                "paper_id": paper_id,
                "entity_count": len(graph.entities),
                "edge_count": len(graph.edges),
            },
            duration_ms=(time.monotonic() - start) * 1000,
        )


class EvidenceAgent:
    name = "evidence_agent"

    def run(self, paper_id: str, data_dir: str) -> AgentResult:
        start = time.monotonic()
        memory = ResearchMemory.load(paper_id, base_dir=f"{data_dir}/memory_indices")
        tagged = sum(1 for c in memory.chunks.values() if c.entities)
        return AgentResult(
            agent_name=self.name,
            success=True,
            output_type="ResearchMemory",
            payload={"paper_id": paper_id, "tagged_chunks": tagged},
            duration_ms=(time.monotonic() - start) * 1000,
        )


class SpecificationAgent:
    name = "specification_agent"

    def run(self, paper_id: str, ranker: EvidenceRanker, data_dir: str) -> AgentResult:
        start = time.monotonic()
        builder = SpecBuilder(ranker)
        spec = builder.build(paper_id)
        builder.save(spec, base_dir=f"{data_dir}/specifications")
        return AgentResult(
            agent_name=self.name,
            success=True,
            output_type="SystemSpec",
            payload={"paper_id": paper_id, "field_count": len(spec.get("fields", {}))},
            duration_ms=(time.monotonic() - start) * 1000,
        )


class BlueprintAgent:
    name = "blueprint_agent"

    def run(self, paper_id: str, graph: SemanticPaperGraph, spec: dict, data_dir: str) -> AgentResult:
        start = time.monotonic()
        gen = BlueprintGenerator(graph, spec=spec)
        blueprint = gen.generate(paper_id)
        gen.save(blueprint, base_dir=f"{data_dir}/blueprints")
        return AgentResult(
            agent_name=self.name,
            success=True,
            output_type="Blueprint",
            payload={"paper_id": paper_id, "module_count": len(blueprint.get("modules", []))},
            duration_ms=(time.monotonic() - start) * 1000,
        )


class BaselineAgent:
    name = "baseline_agent"

    def run(self, paper_id: str, graph: SemanticPaperGraph, spec: dict, data_dir: str) -> AgentResult:
        start = time.monotonic()
        gen = BaselineGenerator(graph, spec=spec)
        baseline = gen.generate(paper_id)
        gen.save(baseline, base_dir=f"{data_dir}/baselines")
        return AgentResult(
            agent_name=self.name,
            success=True,
            output_type="Baseline",
            payload={
                "paper_id": paper_id,
                "family": baseline.get("family"),
                "supported": baseline.get("supported"),
            },
            duration_ms=(time.monotonic() - start) * 1000,
        )


class EvaluationAgent:
    name = "evaluation_agent"

    def run(self, paper_id: str, baseline: dict, spec: dict, data_dir: str) -> AgentResult:
        start = time.monotonic()
        repro = ReproductionEngine()
        report = repro.build_report(baseline, spec, data_dir=data_dir)
        repro.save(report, base_dir=f"{data_dir}/reproduction_reports")
        return AgentResult(
            agent_name=self.name,
            success=True,
            output_type="ReproductionReport",
            payload={
                "paper_id": paper_id,
                "level": report.get("level"),
                "metric_comparable": report.get("metric_comparable"),
            },
            duration_ms=(time.monotonic() - start) * 1000,
        )
