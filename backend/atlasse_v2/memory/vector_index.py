"""FAISS vector index for research memory chunks."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from atlasse_v2.core.models import ResearchChunk
from atlasse_v2.retrieval.dense_scorer import DenseScorer


class MemoryVectorIndex:
    """Persisted dense index over chunk texts."""

    def __init__(self, paper_id: str, scorer: DenseScorer | None = None):
        self.paper_id = paper_id
        self.scorer = scorer or DenseScorer()
        self._chunk_ids: list[str] = []
        self._vectors: np.ndarray | None = None
        self._index = None

    def build(self, chunks: dict[str, ResearchChunk]) -> MemoryVectorIndex:
        self._chunk_ids = list(chunks.keys())
        texts = [chunks[cid].text for cid in self._chunk_ids]
        self._vectors = self.scorer.encode(texts)
        self._build_faiss()
        return self

    def _build_faiss(self) -> None:
        if self._vectors is None or len(self._chunk_ids) == 0:
            return
        try:
            import faiss
            dim = self._vectors.shape[1]
            self._index = faiss.IndexFlatIP(dim)
            self._index.add(self._vectors)
        except ImportError:
            self._index = None

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        if not self._chunk_ids or self._vectors is None:
            return []
        qv = self.scorer.encode([query])[0]
        if self._index is not None:
            import faiss
            scores, indices = self._index.search(qv.reshape(1, -1), min(top_k, len(self._chunk_ids)))
            return [
                (self._chunk_ids[i], float(scores[0][j]))
                for j, i in enumerate(indices[0])
                if i >= 0
            ]
        dots = self._vectors @ qv
        order = np.argsort(-dots)[:top_k]
        return [(self._chunk_ids[i], float(dots[i])) for i in order]

    def save(self, base_dir: str) -> str:
        base = Path(base_dir) / self.paper_id
        base.mkdir(parents=True, exist_ok=True)
        meta_path = base / "vector_meta.json"
        meta_path.write_text(json.dumps({"chunk_ids": self._chunk_ids, "dim": self.scorer.dim}))
        if self._vectors is not None:
            np.save(base / "vectors.npy", self._vectors)
        if self._index is not None:
            try:
                import faiss
                faiss.write_index(self._index, str(base / "faiss.index"))
            except Exception:
                pass
        return str(base)

    @classmethod
    def load(cls, paper_id: str, base_dir: str) -> MemoryVectorIndex:
        base = Path(base_dir) / paper_id
        idx = cls(paper_id)
        meta_path = base / "vector_meta.json"
        if not meta_path.exists():
            return idx
        meta = json.loads(meta_path.read_text())
        idx._chunk_ids = meta.get("chunk_ids", [])
        vec_path = base / "vectors.npy"
        if vec_path.exists():
            idx._vectors = np.load(vec_path)
        faiss_path = base / "faiss.index"
        if faiss_path.exists():
            try:
                import faiss
                idx._index = faiss.read_index(str(faiss_path))
            except Exception:
                idx._index = None
        return idx
