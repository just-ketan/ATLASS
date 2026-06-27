# Embedding model

import hashlib
import os
import sys

import numpy as np


class Embedder:
    """SentenceTransformer wrapper with a deterministic offline fallback."""

    def __init__(self, model_name="all-mpnet-base-v2", fallback_dim=768):
        self.model_name = model_name
        self.dim = fallback_dim
        self.model = None
        self._load_failed = False

    def _load_model(self):
        if self.model is not None or self._load_failed:
            return self.model
        try:
            from sentence_transformers import SentenceTransformer

            allow_download = os.environ.get("ATLASS_ALLOW_MODEL_DOWNLOAD") == "1"
            self.model = SentenceTransformer(self.model_name, local_files_only=not allow_download)
            dim = self.model.get_embedding_dimension()
            if dim:
                self.dim = dim
        except Exception as exc:
            self._load_failed = True
            print(
                f"[ATLASS] Embedding model unavailable; using deterministic fallback ({exc}).",
                file=sys.stderr,
            )
        return self.model

    def _fallback_encode(self, texts):
        vectors = np.zeros((len(texts), self.dim), dtype="float32")
        for row, text in enumerate(texts):
            for token in text.lower().split():
                digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
                bucket = int.from_bytes(digest[:4], "little") % self.dim
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                vectors[row, bucket] += sign
            norm = np.linalg.norm(vectors[row])
            if norm > 0:
                vectors[row] /= norm
        return vectors

    def encode(self, texts):
        model = self._load_model()
        if model is None:
            return self._fallback_encode(texts)
        return model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
