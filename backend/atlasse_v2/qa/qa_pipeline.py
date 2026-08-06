"""Phase 6: Question → intent → retrieve → validate → answer → verify citations."""

from __future__ import annotations

from atlasse_v2.core.types import SectionType
from atlasse_v2.qa.citation_verifier import verify_citations
from atlasse_v2.qa.evidence_validator import filter_valid_evidence, validate_evidence
from atlasse_v2.retrieval.evidence_ranker import EvidenceRanker

MISSING_RESPONSE = "The paper does not specify."
MIN_SCORE_THRESHOLD = 0.8


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

    INTENT_ENTITY_TYPES = {
        "problem": ["task", "contribution"],
        "dataset": ["dataset"],
        "metric": ["metric", "experiment"],
        "method": ["method", "model", "module"],
        "architecture": ["model", "module"],
        "limitation": ["limitation"],
        "future_work": ["future_work"],
        "definition": ["contribution", "task"],
    }

    def __init__(self, ranker: EvidenceRanker, score_threshold: float = MIN_SCORE_THRESHOLD):
        self.ranker = ranker
        self.score_threshold = score_threshold

    def ask(self, question: str, paper_id: str) -> dict:
        intent = self._classify_intent(question)
        sections = EvidenceRanker.INTENT_SECTIONS.get(intent)
        evidence, trace = self.ranker.retrieve_with_trace(
            query=question,
            paper_id=paper_id,
            sections=sections,
            top_k=5,
        )

        if not evidence:
            return self._missing_response(intent, trace, "no_retrieval")

        valid, reason = validate_evidence(intent, evidence)
        if not valid:
            return self._missing_response(intent, trace, reason)

        evidence = filter_valid_evidence(intent, evidence)
        top_score = trace.get("ranked", [{}])[0].get("score", 0.0) if trace else 0.0
        if top_score < self.score_threshold:
            return self._missing_response(intent, trace, "low_confidence", top_score)

        best = evidence[0]
        answer = best.text[:1500]
        citation_check = verify_citations(answer, evidence)
        if not citation_check["verified"]:
            return self._missing_response(intent, trace, citation_check["reason"], top_score)

        return {
            "answer": answer,
            "confidence": min(top_score / 5.0, 1.0),
            "citations": best.citations,
            "provenance": [{
                "chunk_id": best.chunk_id,
                "page": best.page,
                "section": best.section.value if isinstance(best.section, SectionType) else best.section,
                "paragraph_id": best.paragraph_id,
                "chunk_type": best.chunk_type,
            }],
            "intent": intent,
            "entity_types": self.INTENT_ENTITY_TYPES.get(intent, []),
            "retrieval_score": top_score,
            "citation_verified": True,
        }

    def _missing_response(
        self,
        intent: str,
        trace: dict | None,
        reason: str,
        score: float = 0.0,
    ) -> dict:
        return {
            "answer": MISSING_RESPONSE,
            "confidence": 0.0,
            "citations": [],
            "provenance": [],
            "intent": intent,
            "missing_reason": reason,
            "retrieval_score": score,
            "citation_verified": False,
            "trace_summary": {
                "candidate_count": trace.get("candidate_count") if trace else 0,
                "cross_encoder_scores": trace.get("cross_encoder_scores") if trace else [],
            },
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
