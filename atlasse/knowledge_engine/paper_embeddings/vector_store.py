import json
import os

import faiss
import numpy as np


class VectorStore:

    def __init__(self, dim):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.ids = []

    def add(self, embeddings, ids):
        embeddings = np.array(embeddings).astype("float32")
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)
        self.index.add(embeddings)
        self.ids.extend(ids)

    def search(self, query_embedding, k=5, filter_ids=None):
        query_embedding = np.array(query_embedding).astype("float32")
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        if self.index.ntotal == 0:
            return []
        search_k = min(k * 4, max(self.index.ntotal, 1)) if filter_ids else k
        distances, indices = self.index.search(query_embedding, search_k)
        results = []
        filter_set = set(filter_ids) if filter_ids else None

        for idx, dist in zip(indices[0], distances[0]):
            if idx == -1:
                continue
            chunk_id = self.ids[idx]
            if filter_set is not None and chunk_id not in filter_set:
                continue
            results.append((chunk_id, dist))
            if len(results) >= k:
                break
        return results

    def save(self, directory):
        os.makedirs(directory, exist_ok=True)
        faiss.write_index(self.index, os.path.join(directory, "index.faiss"))
        with open(os.path.join(directory, "ids.json"), "w") as f:
            json.dump(self.ids, f)
        with open(os.path.join(directory, "meta.json"), "w") as f:
            json.dump({"dim": self.dim, "count": len(self.ids)}, f)

    @classmethod
    def load(cls, directory):
        with open(os.path.join(directory, "meta.json")) as f:
            meta = json.load(f)
        store = cls(meta["dim"])
        store.index = faiss.read_index(os.path.join(directory, "index.faiss"))
        with open(os.path.join(directory, "ids.json")) as f:
            store.ids = json.load(f)
        return store
