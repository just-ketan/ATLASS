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
        for i, idx in enumerate(indices[0]):
            results.append((self.texts[idx], distances[0][i]))

        return results
