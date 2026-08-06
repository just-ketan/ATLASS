"""Phase 4: Multi-signal evidence ranking.

Score = semantic + keyword + section_weight + entity_overlap + citation_overlap

Only top reranked evidence reaches the LLM.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from atlasse_v2.core.models import ResearchChunk
from atlasse_v2.core.types import SectionType
from atlasse_v2.memory.research_memory import ResearchMemory


class EvidenceRanker:
    """Retriever + reranker over research memory chunks."""

    SECTION_WEIGHTS: dict[str, float] = {
        SectionType.ABSTRACT.value: 0.6,
        SectionType.INTRODUCTION.value: 0.5,
        SectionType.METHOD.value: 0.9,
        SectionType.ARCHITECTURE.value: 0.95,
        SectionType.EXPERIMENTS.value: 0.95,
        SectionType.DATASETS.value: 1.0,
        SectionType.RESULTS.value: 0.9,
        SectionType.LIMITATIONS.value: 0.85,
        SectionType.FUTURE_WORK.value: 0.85,
        SectionType.APPENDIX.value: 0.7,
    }

    INTENT_SECTIONS: dict[str, list[SectionType]] = {
        "problem": [SectionType.ABSTRACT, SectionType.INTRODUCTION],
        "contribution": [SectionType.ABSTRACT, SectionType.INTRODUCTION],
        "task": [SectionType.INTRODUCTION, SectionType.METHOD],
        "dataset": [SectionType.DATASETS, SectionType.EXPERIMENTS, SectionType.APPENDIX],
        "metric": [SectionType.EXPERIMENTS, SectionType.RESULTS],
        "method": [SectionType.METHOD, SectionType.ARCHITECTURE],
        "architecture": [SectionType.ARCHITECTURE, SectionType.METHOD],
        "loss": [SectionType.METHOD, SectionType.EXPERIMENTS],
        "training": [SectionType.EXPERIMENTS, SectionType.IMPLEMENTATION],
        "evaluation": [SectionType.EXPERIMENTS, SectionType.RESULTS],
        "baseline": [SectionType.EXPERIMENTS, SectionType.RESULTS, SectionType.RELATED_WORK],
        "limitation": [SectionType.LIMITATIONS, SectionType.DISCUSSION],
        "future_work": [SectionType.FUTURE_WORK, SectionType.DISCUSSION],
    }

    def __init__(self, memory: ResearchMemory):
        self.memory = memory
        self._bm25_index: dict[str, Counter] = {}
        self._doc_lengths: dict[str, int] = {}
        self._avg_dl = 0.0
        self.last_trace: dict | None = None
        self._build_bm25()

    def _build_bm25(self) -> None:
        for cid, chunk in self.memory.chunks.items():
            tokens = self._tokenize(chunk.text)
            self._doc_lengths[cid] = len(tokens)
            self._bm25_index[cid] = Counter(tokens)
        if self._doc_lengths:
            self._avg_dl = sum(self._doc_lengths.values()) / len(self._doc_lengths)

    def retrieve(
        self,
        query: str,
        paper_id: str | None = None,
        sections: list[SectionType] | None = None,
        top_k: int = 5,
    ) -> list[ResearchChunk]:
        results, _ = self.retrieve_with_trace(query, paper_id=paper_id, sections=sections, top_k=top_k)
        return results

    def retrieve_with_trace(
        self,
        query: str,
        paper_id: str | None = None,
        sections: list[SectionType] | None = None,
        top_k: int = 5,
    ) -> tuple[list[ResearchChunk], dict]:
        candidates = list(self.memory.chunks.values())
        filtered_by_section = bool(sections)
        if sections:
            section_values = {s.value for s in sections}
            candidates = [
                c for c in candidates
                if (c.section.value if isinstance(c.section, SectionType) else c.section) in section_values
            ]
        if not candidates:
            candidates = list(self.memory.chunks.values())
            filtered_by_section = False

        scored = []
        query_tokens = self._tokenize(query)
        query_set = set(query_tokens)
        trace_entries = []
        for chunk in candidates:
            semantic = self._semantic_score(chunk.text, query)
            keyword = self._bm25_score(chunk.chunk_id, query_tokens)
            section = self._section_weight(chunk)
            entity = self._entity_overlap(chunk, query_set)
            citation = self._citation_overlap(chunk, query)
            total = semantic + keyword + section + entity + citation
            scored.append((total, chunk))
            trace_entries.append({
                "chunk_id": chunk.chunk_id,
                "paragraph_id": chunk.paragraph_id,
                "section": chunk.section.value if isinstance(chunk.section, SectionType) else chunk.section,
                "page": chunk.page,
                "score": round(total, 4),
                "components": {
                    "semantic": round(semantic, 4),
                    "keyword": round(keyword, 4),
                    "section": round(section, 4),
                    "entity": round(entity, 4),
                    "citation": round(citation, 4),
                },
            })

        scored.sort(key=lambda x: x[0], reverse=True)
        trace_entries.sort(key=lambda e: e["score"], reverse=True)
        self.last_trace = {
            "query": query,
            "paper_id": paper_id,
            "sections": [s.value for s in sections] if sections else [],
            "filtered_by_section": filtered_by_section,
            "candidate_count": len(candidates),
            "top_k": top_k,
            "ranked": trace_entries[:top_k],
        }
        return [chunk for _, chunk in scored[:top_k]], self.last_trace

    def _combined_score(
        self,
        chunk: ResearchChunk,
        query: str,
        query_tokens: list[str],
        query_set: set[str],
    ) -> float:
        semantic = self._semantic_score(chunk.text, query)
        keyword = self._bm25_score(chunk.chunk_id, query_tokens)
        section = self._section_weight(chunk)
        entity = self._entity_overlap(chunk, query_set)
        citation = self._citation_overlap(chunk, query)
        return semantic + keyword + section + entity + citation

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    def _bm25_score(self, chunk_id: str, query_tokens: list[str], k1: float = 1.5, b: float = 0.75) -> float:
        if chunk_id not in self._bm25_index:
            return 0.0
        dl = self._doc_lengths.get(chunk_id, 0)
        if dl == 0 or self._avg_dl == 0:
            return 0.0
        doc_tf = self._bm25_index[chunk_id]
        n_docs = len(self._bm25_index)
        score = 0.0
        for token in query_tokens:
            tf = doc_tf.get(token, 0)
            if tf == 0:
                continue
            df = sum(1 for c in self._bm25_index.values() if token in c)
            idf = math.log((n_docs - df + 0.5) / (df + 0.5) + 1)
            denom = tf + k1 * (1 - b + b * dl / self._avg_dl)
            score += idf * (tf * (k1 + 1)) / denom
        return score / max(len(query_tokens), 1)

    @staticmethod
    def _semantic_score(text: str, query: str) -> float:
        text_tokens = set(re.findall(r"[a-z0-9]+", text.lower()))
        query_tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
        if not query_tokens:
            return 0.0
        overlap = len(text_tokens & query_tokens)
        return overlap / len(query_tokens)

    def _section_weight(self, chunk: ResearchChunk) -> float:
        section = chunk.section.value if isinstance(chunk.section, SectionType) else chunk.section
        return self.SECTION_WEIGHTS.get(section, 0.3)

    @staticmethod
    def _entity_overlap(chunk: ResearchChunk, query_tokens: set[str]) -> float:
        keywords = {k.lower() for k in chunk.keywords}
        if not keywords:
            return 0.0
        overlap = len(keywords & query_tokens)
        return overlap / max(len(keywords), 1)

    @staticmethod
    def _citation_overlap(chunk: ResearchChunk, query: str) -> float:
        if not chunk.citations:
            return 0.0
        query_lower = query.lower()
        matches = sum(1 for c in chunk.citations if any(w in c.lower() for w in query_lower.split()))
        return matches / len(chunk.citations)
