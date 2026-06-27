"""Evidence merging and provenance for multi-query orchestration."""

from dataclasses import dataclass, field


@dataclass
class Evidence:
    text: str
    score: float
    chunk_id: int
    paper_id: str
    section: str
    source_query: str = ""


@dataclass
class MergedEvidence:
    items: list[Evidence] = field(default_factory=list)
    provenance: list[dict] = field(default_factory=list)

    def add_from_trace(self, trace: dict, source_query: str = ""):
        for sent in trace.get("ranked_sentences", []):
            ev = Evidence(
                text=sent["text"],
                score=sent["score"],
                chunk_id=sent.get("chunk_id", -1),
                paper_id=trace.get("paper_id", "unknown"),
                section=sent.get("section", ""),
                source_query=source_query or trace.get("original_query", ""),
            )
            self.items.append(ev)
            self.provenance.append({
                "chunk_id": ev.chunk_id,
                "paper_id": ev.paper_id,
                "section": ev.section,
                "score": ev.score,
                "source_query": ev.source_query,
            })

    def merge(self) -> list[Evidence]:
        seen = set()
        merged = []
        for ev in sorted(self.items, key=lambda x: x.score, reverse=True):
            key = ev.text.lower().strip()
            if key in seen:
                continue
            seen.add(key)
            merged.append(ev)
        return merged

    def format_citations(self, max_items=3) -> str:
        lines = []
        for i, ev in enumerate(self.merge()[:max_items], 1):
            lines.append(f"[{i}] ({ev.paper_id} § {ev.section}, chunk {ev.chunk_id})")
        return "\n".join(lines)

    def format_answer(self, max_items=2) -> str:
        texts = [ev.text for ev in self.merge()[:max_items]]
        answer = " ".join(texts)
        if answer and not answer.endswith("."):
            answer += "."
        return answer

    def merged_provenance(self, max_items=None) -> list[dict]:
        evidence = self.merge()
        if max_items is not None:
            evidence = evidence[:max_items]
        return [
            {
                "chunk_id": ev.chunk_id,
                "paper_id": ev.paper_id,
                "section": ev.section,
                "score": ev.score,
                "source_query": ev.source_query,
            }
            for ev in evidence
        ]
