"""Phase 12: Full agent orchestration with inspectable traces."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from atlasse_v2.agents.base import AgentTrace
from atlasse_v2.agents.specialized import (
    BaselineAgent,
    BlueprintAgent,
    DocumentAgent,
    EvidenceAgent,
    EvaluationAgent,
    ResearchAgent,
    RetrievalAgent,
    SpecificationAgent,
)
from atlasse_v2.agents.trace_store import AgentTraceStore
from atlasse_v2.graph.semantic_graph import SemanticPaperGraph
from atlasse_v2.memory.research_memory import ResearchMemory
from atlasse_v2.parsing.document_store import DocumentStore
from atlasse_v2.pipeline import PaperPipeline
from atlasse_v2.retrieval.evidence_ranker import EvidenceRanker
from atlasse_v2.specification.spec_builder import SpecBuilder


class AgentOrchestrator:
    """Coordinates agents through typed object handoffs with full trace logging."""

    def __init__(self, data_dir: str = "data/v2"):
        self.data_dir = data_dir
        self.pipeline = PaperPipeline(data_dir=data_dir)
        self.trace_store = AgentTraceStore()

    def process_paper(self, pdf_path: str, paper_id: str | None = None) -> dict:
        result, _ = self.process_with_trace(pdf_path, paper_id=paper_id)
        return result

    def process_with_trace(self, pdf_path: str, paper_id: str | None = None) -> tuple[dict, dict]:
        pdf_path = Path(pdf_path)
        paper_id = paper_id or pdf_path.stem
        trace = AgentTrace(
            paper_id=paper_id,
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        doc_agent = DocumentAgent()
        doc_result = doc_agent.run(str(pdf_path), paper_id, self.data_dir)
        trace.add(doc_result)
        if not doc_result.success:
            return self._finalize(trace, {"error": doc_result.error}), trace.to_dict()

        document = DocumentStore.load(paper_id, base_dir=f"{self.data_dir}/parsed")
        ret_agent = RetrievalAgent()
        ret_result = ret_agent.run(document, self.data_dir)
        trace.add(ret_result)

        memory = ResearchMemory.load(paper_id, base_dir=f"{self.data_dir}/memory_indices")
        ranker = EvidenceRanker(memory)

        research_result = ResearchAgent().run(paper_id, ranker, self.data_dir)
        trace.add(research_result)
        evidence_result = EvidenceAgent().run(paper_id, self.data_dir)
        trace.add(evidence_result)

        ranker = EvidenceRanker(
            ResearchMemory.load(paper_id, base_dir=f"{self.data_dir}/memory_indices")
        )
        spec_result = SpecificationAgent().run(paper_id, ranker, self.data_dir)
        trace.add(spec_result)

        graph = SemanticPaperGraph.load(paper_id, base_dir=f"{self.data_dir}/knowledge_graphs")
        spec = SpecBuilder(ranker).build(paper_id)

        bp_result = BlueprintAgent().run(paper_id, graph, spec, self.data_dir)
        trace.add(bp_result)
        bl_result = BaselineAgent().run(paper_id, graph, spec, self.data_dir)
        trace.add(bl_result)

        baseline = self.pipeline.get_baseline(paper_id) or {}
        eval_result = EvaluationAgent().run(paper_id, baseline, spec, self.data_dir)
        trace.add(eval_result)

        summary = {
            "paper_id": paper_id,
            "section_count": doc_result.payload.get("section_count"),
            "chunk_count": ret_result.payload.get("chunk_count"),
            "entity_count": research_result.payload.get("entity_count"),
            "edge_count": research_result.payload.get("edge_count"),
            "blueprint_modules": bp_result.payload.get("module_count"),
            "baseline_family": bl_result.payload.get("family"),
            "baseline_supported": bl_result.payload.get("supported"),
            "reproduction_level": eval_result.payload.get("level"),
            "metric_comparable": eval_result.payload.get("metric_comparable"),
        }
        return self._finalize(trace, summary), trace.to_dict()

    def _finalize(self, trace: AgentTrace, summary: dict) -> dict:
        trace.completed_at = datetime.now(timezone.utc).isoformat()
        trace.success = "error" not in summary
        self.trace_store.save(trace, base_dir=f"{self.data_dir}/agent_traces")
        summary["agent_trace_saved"] = True
        return summary

    def get_trace(self, paper_id: str) -> dict | None:
        return self.trace_store.load(paper_id, base_dir=f"{self.data_dir}/agent_traces")

    def get_status(self, paper_id: str) -> dict:
        status = self.pipeline.get_status(paper_id)
        status["has_agent_trace"] = self.get_trace(paper_id) is not None
        return status
