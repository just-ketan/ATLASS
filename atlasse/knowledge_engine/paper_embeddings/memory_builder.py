import json
import re

from .chunker import TextChunker
from .embedder import Embedder
from .vector_store import VectorStore
from rank_bm25 import BM25Okapi


class PaperMemory:

    def __init__(self):
        self.chunker = TextChunker()
        self.embedder = Embedder()
        self.vector_store = None
        self.texts = []
        self.bm25 = None
        self.text_to_idx = {}

    @staticmethod
    def split_sentences(text):
        return re.split(r'(?<=[.!?])\s+', text)

    @staticmethod
    def is_useful_chunk(text):
        num_digits = sum(c.isdigit() for c in text)
        if num_digits > len(text) * 0.15:
            return False

        if len(text.strip()) < 50:
            return False

        special = sum(not c.isalnum() and not c.isspace() for c in text)
        if special > len(text) * 0.2:
            return False

        return True

    @staticmethod
    def is_noise_sentence(s):
        s = s.lower()
        noise_words = ["accuracy", "table", "dataset", "results", "benchmark"]
        return any(w in s for w in noise_words)

    @staticmethod
    def is_bad_sentence(s):
        s = s.lower()
        bad_words = [
            "rank r", "we set", "figure", "table", "dataset",
            "accuracy", "benchmark", "hyperparameter", "training",
            "we train", "we evaluate"
        ]
        return any(w in s for w in bad_words)
        
    @staticmethod
    def is_definition_sentence(s):
        s_l = s.lower()
        keyword_hits = any(k in s_l for k in [
            "is a", "is an", "refers to", "is called",
            "we propose", "we introduce", "named", "known as"
        ])
        # Pattern: "<Term> (…)? is ..."
        pattern_hit = bool(re.search(r'\b[lL]o[rR]a\b.*\bis\b', s))
        return keyword_hits or pattern_hit

    def build(self, json_path):

        with open(json_path, "r") as f:
            data = json.load(f)

        text = data["full_text"]
        raw_chunks = self.chunker.chunk(text)

        all_chunks = []

        for i, chunk in enumerate(raw_chunks):

            if not self.is_useful_chunk(chunk):
                continue

            if i < 5:
                all_chunks.extend([chunk] * 3)
            else:
                all_chunks.append(chunk)

        self.texts = all_chunks

        # FAST index map (fixes .index issue)
        self.text_to_idx = {t: i for i, t in enumerate(self.texts)}

        # BM25
        tokenized_corpus = [t.lower().split() for t in self.texts]
        self.bm25 = BM25Okapi(tokenized_corpus)

        # Embeddings
        embeddings = self.embedder.encode(self.texts)
        dim = embeddings.shape[1]

        self.vector_store = VectorStore(dim)
        self.vector_store.add(embeddings, self.texts)

    def query(self, text, k=3):

        query = f"{text} definition meaning low rank adaptation transformer"

        # Semantic
        query_embed = self.embedder.encode([query])
        vec_results = self.vector_store.search(query_embed, k=10)

        # BM25
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)

        combined = []

        for chunk, dist in vec_results:
            idx = self.text_to_idx.get(chunk, -1)
            bm25_score = bm25_scores[idx] if idx != -1 else 0

            score = -dist + bm25_score
            combined.append((chunk, score))

        combined = sorted(combined, key=lambda x: x[1], reverse=True)

        # Sentence-level ranking
        top_chunks = combined[:3]
        sentences = []
        for chunk, _ in top_chunks:
            sentences.extend(self.split_sentences(chunk))

        # clean + dedupe
        sentences = [s.strip() for s in sentences if s.strip()]
        sentences = list(dict.fromkeys(sentences))

        # filters
        sentences = [s for s in sentences if not self.is_noise_sentence(s)]
        sentences = [s for s in sentences if not self.is_bad_sentence(s)]
        sentences = [s for s in sentences if len(s) > 40]

        if not sentences:
            return []

        tokenized_sentences = [s.lower().split() for s in sentences]
        bm25_sent = BM25Okapi(tokenized_sentences)
        scores = bm25_sent.get_scores(tokenized_query)

        ranked = sorted(zip(sentences, scores), key=lambda x: x[1], reverse=True)

        definition_sentences = [
            (s, sc) for s, sc in ranked if self.is_definition_sentence(s)
        ]

        if definition_sentences:
            return definition_sentences[:2]

        return ranked[:2]