"""Phase 6: Question → intent → retrieve → validate → answer → verify citations."""

from __future__ import annotations

from atlasse_v2.retrieval.evidence_ranker import EvidenceRanker

MISSING_RESPONSE = "The paper does not specify."


class QAPipeline:
    INTENT_QUERIES = {
        "definition": "what is defined or introduced",
        "problem": "what problem does this paper address",
        "method": "what method is proposed",
        "dataset": "what datasets are used",
        "metric": "what metrics are reported",
        "limitation": "what limitations are mentioned",
        "future_work": "what future work is proposed",
    }

    def __init__(self, ranker: EvidenceRanker):
        self.ranker = ranker

    def ask(self, question: str, paper_id: str) -> dict:
        intent = self._classify_intent(question)
        sections = EvidenceRanker.INTENT_SECTIONS.get(intent)
        evidence = self.ranker.retrieve(
            query=question,
            paper_id=paper_id,
            sections=sections,
            top_k=5,
        )
        if not evidence:
            return {
                "answer": MISSING_RESPONSE,
                "confidence": 0.0,
                "citations": [],
                "provenance": [],
                "intent": intent,
            }

        best = evidence[0]
        return {
            "answer": best.text[:1500],
            "confidence": 0.7,
            "citations": best.citations,
            "provenance": [{
                "chunk_id": best.chunk_id,
                "page": best.page,
                "section": best.section.value if hasattr(best.section, "value") else best.section,
                "paragraph_id": best.paragraph_id,
            }],
            "intent": intent,
        }

    def _classify_intent(self, question: str) -> str:
        q = question.lower()
        for intent, _ in self.INTENT_QUERIES.items():
            if intent.replace("_", " ") in q or intent in q:
                return intent
        if "dataset" in q or "benchmark" in q:
            return "dataset"
        if "metric" in q or "accuracy" in q or "f1" in q:
            return "metric"
        if "limit" in q or "drawback" in q:
            return "limitation"
        if "future" in q or "open problem" in q:
            return "future_work"
        if "method" in q or "approach" in q or "architecture" in q:
            return "method"
        if "problem" in q or "motivation" in q:
            return "problem"
        return "definition"
