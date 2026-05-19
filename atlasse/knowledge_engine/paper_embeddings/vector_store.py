# vector store

import faiss
import numpy as np

class VectorStore:
    def __init__(self, dim):
        self.index = faiss.IndexFlatL2(dim)
        self.texts = []
    
    def add(self, embeddings, texts):
        self.index.add(np.array(embeddings))
        self.texts.extend(texts)
    
    def search(self, query_embedding, k=5):
        distances, indices = self.index.search(query_embedding, k)
        results = []
        for dist, idx in zip(distances[0],indices[0]):
            if idx == -1:
                continue
            results.append((self.texts[idx], float(dist)))
        return results
