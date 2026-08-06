"""Optional dense embedding scorer for evidence ranking."""

from __future__ import annotations

import os
import sys

import numpy as np


class DenseScorer:
    """Cosine similarity via SentenceTransformer with deterministic fallback."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", dim: int = 384):
        self.model_name = model_name
        self.dim = dim
        self._model = None
        self._load_failed = False

    def _load(self):
        if self._model is not None or self._load_failed:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer

            allow = os.environ.get("ATLASS_ALLOW_MODEL_DOWNLOAD") == "1"
            self._model = SentenceTransformer(self.model_name, local_files_only=not allow)
            model_dim = self._model.get_embedding_dimension()
            if model_dim:
                self.dim = model_dim
        except Exception as exc:
            self._load_failed = True
            print(f"[atlasse_v2] Dense scorer fallback active: {exc}", file=sys.stderr)
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        model = self._load()
        if model is not None:
            return np.array(model.encode(texts, normalize_embeddings=True), dtype="float32")
        dim = self.dim
        vecs = np.zeros((len(texts), dim), dtype="float32")
        for i, text in enumerate(texts):
            vecs[i] = self._fallback_vector(text, dim)
        return vecs

    @staticmethod
    def _fallback_vector(text: str, dim: int) -> np.ndarray:
        import hashlib
        h = hashlib.sha256(text.encode()).digest()
        raw = np.frombuffer(h, dtype=np.uint8).astype("float32")
        tiled = np.resize(raw, dim)
        norm = np.linalg.norm(tiled)
        return tiled / norm if norm > 0 else tiled

    def score(self, query: str, text: str) -> float:
        model = self._load()
        if model is not None:
            qv = model.encode(query, normalize_embeddings=True)
            tv = model.encode(text, normalize_embeddings=True)
            return float(np.dot(qv, tv))
        return self._fallback_score(query, text)

    @staticmethod
    def _fallback_score(query: str, text: str) -> float:
        q_tokens = set(query.lower().split())
        t_tokens = set(text.lower().split())
        if not q_tokens:
            return 0.0
        return len(q_tokens & t_tokens) / len(q_tokens)
