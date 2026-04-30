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
        paragraphs = text.split("\n\n")
        # chunks = []
        # curr = ""
        
        # for para in paragraphs:
        #     if len(curr) + len(para) < self.chunk_size:
        #         curr += para + "\n\n"
        #     else:
        #         chunks.append(curr.strip())
        #         curr = para
        # if curr:
        #     chunks.append(curr.strip())
        # return chunks

        words = text.split()
        chunks = []
        for i in range(0, len(words), self.chunk_size - self.overlap):
            chunk = " ".join(words[i:i+self.chunk_size])
            chunks.append(chunk)
        
        return chunks