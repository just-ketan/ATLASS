import uuid

from atlasse.knowledge_engine.observability.trace_store import TraceStore
from atlasse.knowledge_engine.retrieval.section_router import expand_query
from .evidence_merger import MergedEvidence


class QueryOrchestrator:
    """Phase 6: decompose queries, retrieve evidence, merge with provenance."""

    def __init__(self, memory, trace_store=None):
        self.memory = memory
        self.trace_store = trace_store or TraceStore()

    def retrieve(self, query: str) -> MergedEvidence:
        base_trace_id = str(uuid.uuid4())[:8]
        sub_queries = expand_query(query)
        merged = MergedEvidence()

        for idx, sub_q in enumerate(sub_queries, 1):
            trace_id = f"{base_trace_id}-{idx}"
            self.memory.query(sub_q, trace_id=trace_id)
            trace = dict(self.memory.last_trace)
            trace["trace_id"] = trace_id
            trace["parent_trace_id"] = base_trace_id
            self.trace_store.save(trace)
            merged.add_from_trace(trace, source_query=sub_q)

        return merged

    def ask_with_provenance(self, query: str) -> dict:
        merged = self.retrieve(query)
        evidence = merged.merge()
        return {
            "answer": merged.format_answer(),
            "citations": merged.format_citations(),
            "provenance": merged.merged_provenance(),
            "evidence_count": len(evidence),
            "confidence": max(0.0, min(1.0, max((e.score for e in evidence), default=0.0))),
        }
