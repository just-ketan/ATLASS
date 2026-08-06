"""Span-bound evidence gate — extractors may only return text from retrieved spans."""

from __future__ import annotations

import re

from atlasse_v2.core.models import EvidenceSpan, ExtractedField, ResearchChunk


def spans_from_chunks(chunks: list[ResearchChunk]) -> list[EvidenceSpan]:
    return [
        EvidenceSpan(
            text=chunk.text,
            provenance=_chunk_provenance(chunk),
            score=1.0,
        )
        for chunk in chunks
    ]


def _chunk_provenance(chunk: ResearchChunk):
    from atlasse_v2.core.models import Provenance
    return Provenance(
        page=chunk.page,
        section=chunk.section,
        paragraph_id=chunk.paragraph_id,
        chunk_id=chunk.chunk_id,
    )


def extract_span_bound_sentences(
    chunks: list[ResearchChunk],
    query_terms: list[str] | None = None,
    max_sentences: int = 3,
) -> ExtractedField:
    """Return only sentences that exist in evidence chunks — no synthesis."""
    if not chunks:
        return ExtractedField(value=None, missing=True, confidence=0.0)

    terms = [t.lower() for t in (query_terms or [])]
    selected: list[str] = []
    spans: list[EvidenceSpan] = []

    for chunk in chunks:
        for sentence in _split_sentences(chunk.text):
            sentence = sentence.strip()
            if len(sentence) < 15:
                continue
            if terms and not any(t in sentence.lower() for t in terms):
                continue
            if sentence not in selected:
                selected.append(sentence)
                spans.append(
                    EvidenceSpan(text=sentence, provenance=_chunk_provenance(chunk))
                )
            if len(selected) >= max_sentences:
                break
        if len(selected) >= max_sentences:
            break

    if not selected and chunks:
        first = _split_sentences(chunks[0].text)[0].strip()
        if first:
            selected.append(first[:500])
            spans.append(
                EvidenceSpan(text=first, provenance=_chunk_provenance(chunks[0]))
            )

    if not selected:
        return ExtractedField(value=None, missing=True, confidence=0.0)

    value = " ".join(selected)
    return ExtractedField(
        value=value[:1200],
        supporting_spans=spans,
        confidence=min(0.5 + 0.1 * len(selected), 0.85),
        citations=list(dict.fromkeys(c for ch in chunks for c in ch.citations)),
    )


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p for p in parts if p.strip()]
