'''
normal search -> keyword match
semantic match --> meaning match
processed json -> text chunking -> embeddings (Sentence Transformers) -> FAISS indexing -> [ query -> embeddings -> similar chunks]

THIS IS CHUNK ENGINE implementation class
'''

class TextChunker:
    def __init__(self, chunk_size=500, overlap=100):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, text):
        chunks = []
        start  = 0
        while start < len(text):
            end = start+self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += self.chunk_size - self.overlap
        return chunks