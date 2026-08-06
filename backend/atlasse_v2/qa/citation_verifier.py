"""Verify QA answers are grounded in cited evidence spans."""

from __future__ import annotations

from atlasse_v2.core.models import ResearchChunk


def verify_citations(answer: str, evidence: list[ResearchChunk]) -> dict:
    if not answer or not evidence:
        return {"verified": False, "matched_chunks": [], "reason": "empty_answer_or_evidence"}

    answer_lower = answer.lower()
    matched = []
    for chunk in evidence:
        snippet = chunk.text[:200].lower()
        if snippet and snippet[:40] in answer_lower or answer_lower[:40] in snippet:
            matched.append(chunk.chunk_id)
        elif any(w in answer_lower for w in snippet.split()[:8] if len(w) > 4):
            matched.append(chunk.chunk_id)

    verified = len(matched) > 0
    return {
        "verified": verified,
        "matched_chunks": matched,
        "reason": "ok" if verified else "answer_not_in_evidence",
    }
