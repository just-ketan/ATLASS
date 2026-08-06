"""Optional cross-encoder reranking for top evidence candidates."""

from __future__ import annotations

import os
import sys

from atlasse_v2.core.models import ResearchChunk


class CrossEncoderReranker:
    """Rerank top candidates with cross-encoder; lexical fallback when unavailable."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None
        self._load_failed = False

    def _load(self):
        if self._model is not None or self._load_failed:
            return self._model
        try:
            from sentence_transformers import CrossEncoder

            allow = os.environ.get("ATLASS_ALLOW_MODEL_DOWNLOAD") == "1"
            self._model = CrossEncoder(self.model_name)
            if not allow:
                pass
        except Exception as exc:
            self._load_failed = True
            print(f"[atlasse_v2] Cross-encoder fallback active: {exc}", file=sys.stderr)
        return self._model

    def rerank(
        self,
        query: str,
        chunks: list[ResearchChunk],
        top_k: int = 5,
    ) -> tuple[list[ResearchChunk], list[float]]:
        if not chunks:
            return [], []
        model = self._load()
        if model is not None:
            pairs = [[query, c.text[:512]] for c in chunks]
            scores = model.predict(pairs)
            ranked = sorted(zip(scores, chunks), key=lambda x: float(x[0]), reverse=True)
            return [c for _, c in ranked[:top_k]], [float(s) for s, _ in ranked[:top_k]]
        scores = [_lexical_overlap(query, c.text) for c in chunks]
        ranked = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
        return [c for _, c in ranked[:top_k]], [s for s, _ in ranked[:top_k]]


def _lexical_overlap(query: str, text: str) -> float:
    q = set(query.lower().split())
    t = set(text.lower().split())
    if not q:
        return 0.0
    return len(q & t) / len(q)
