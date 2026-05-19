import json
import re
from collections import defaultdict
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

        # text = data["full_text"]
        # raw_chunks = self.chunker.chunk(text)

        self.chunk_metadata = {}
        self.section_chunks = []
        for section in data["sections"]:
            title = section["title"].lower()
            if "reference" in title or "appendix" in title:
                continue
            text = section["text"]
            chunks = self.chunker.chunk(text)
            chunk_id=0
            for i,chunk in enumerate(chunks):
                if not self.is_useful_chunk(chunk):
                    continue
                
                # boost intro/abstract
                boost = 3 if ("abstract" in title or "introduction" in  title) and i<3 else 1

                for _ in range(boost):
                    entry = {"section":title, "text":chunk}
                    self.section_chunks.append(entry)
                    self.chunk_metadata[chunk_id] = entry
                    chunk_id += 1

        #final text corpus
        self.texts = [x["text"] for x in self.section_chunks]

        # FAST index map (fixes .index issue)
        self.text_to_idx = defaultdict(list)
        for i, t in enumerate(self.texts):
            self.text_to_idx[t].append(i)

        # BM25
        tokenized_corpus = [t.lower().split() for t in self.texts]
        self.bm25 = BM25Okapi(tokenized_corpus)

        # Embeddings
        embeddings = self.embedder.encode(self.texts)
        dim = embeddings.shape[1]

        self.vector_store = VectorStore(dim)
        self.vector_store.add(embeddings, self.texts)

    def get_target_sections(self, query):
        q = query.lower()
        mapping = {
            "definition": ["abstract", "introduction"],
            "what": ["abstract", "introduction"],
            "method": ["method", "approach"],
            "how": ["method", "approach"],
            "dataset": ["experiment"],
            "benchmark": ["experiment"],
            "evaluation": ["experiment"],
            "limitation": ["discussion", "conclusion"],
            "future": ["conclusion"],
        }
        targets = []
        for key, vals in mapping.items():
            if key in q:
                targets.extend(vals)
        return list(set(targets))

    def query(self, text, k=3):

        query = text
        if "what is" in text.lower():
            query += " definition explanation"
        target_sections = self.get_target_sections(query)

        # ========Semantic===============
        query_embed = self.embedder.encode([query])
        vec_results = self.vector_store.search(query_embed, k=10)

        filtered_results= []

        for chunk_id, dist in vec_results:
            item = self.chunk_metadata[chunk_id]
            chunk = item["text"]

            if item is None:
                continue
            
            # no filtering needed
            if not target_sections:
                filtered_results.append((chunk, dist))
            
            # section-aware filtering
            if any(sec in item["section"] for sec in target_sections):
                filtered_results.append((chunk, dist))

        vec_results = filtered_results[:10]

        # ============BM25===============
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)

        combined = []

        for chunk_id, dist in vec_results:
            item = self.chunk_metadata[chunk_id]
            chunk = item["text"]
            idxs = self.text_to_idx.get(chunk, [])
            bm25_score = max((bm25_scores[i] for i in idxs), default = 0)
            score = -dist + bm25_score
            combined.append((chunk, score))
        
        combined = sorted(combined, key=lambda x : x [1], reverse=True)

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