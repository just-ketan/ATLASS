# Embedding model

from sentence_transformers import SentenceTransformer

class Embedder:
    def __init__(self):
        self.model = SentenceTransformer('all-mpnet-base-v2')

    def encode(self, texts):
        return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    