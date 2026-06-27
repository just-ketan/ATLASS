import faiss
import numpy as np

class VectorStore:

    def __init__(self, dim):
        self.index = faiss.IndexFlatL2(dim)
        self.ids = []

    def add(self, embeddings, ids):
        embeddings = np.array(embeddings).astype("float32")
        self.index.add(embeddings)
        self.ids.extend(ids)

    def search(self, query_embedding, k=5):
        query_embedding = np.array(query_embedding).astype("float32")
        distances, indices = self.index.search(query_embedding, k)
        results = []

        for idx, dist in zip(indices[0], distances[0]):
            if idx == -1:
                continue
            chunk_id = self.ids[idx]
            results.append((chunk_id, dist))
        return results