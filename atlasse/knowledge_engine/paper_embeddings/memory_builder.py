import json

from .chunker import TextChunker
from .embedder import Embedder
from .vector_store import VectorStore

class PaperMemory:
    def __init__(self):
        self.chunker = TextChunker()
        self.embedder = Embedder()
        self.vector_store = None

    def build(self, json_path):
        with open(json_path, "r") as f:
            data = json.load(f)

        all_chunks = []
        for section in data["sections"]:
            chunks = self.chunker.chunk(section["text"])
            all_chunks.extend(chunks)
        
        embeddings = self.embedder.encode(all_chunks)
        dim = embeddings.shape[1]

        self.vector_store = VectorStore(dim)
        self.vector_store.add(embeddings, all_chunks)

    def query(self, text):
        query_embedding = self.embedder.encode([text])
        res = self.vector_store.search(query_embedding)
        return res
