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
        s = s.lower().strip()
        if len(s) < 15:
            return True
        return False

    @staticmethod
    def is_bad_sentence(s):
        s = s.lower()
        if s.count("|") > 2:
            return True
        num_digits = sum(c.isdigit() for c in s)
        if num_digits > len(s) * 0.4:
            return True
        return False
        
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
        chunk_id = 0

        for section in data["sections"]:
            title = section["title"].lower()
            if "reference" in title or "appendix" in title:
                continue
            chunks = self.chunker.chunk(section["text"])
            for i, chunk in enumerate(chunks):
                if not self.is_useful_chunk(chunk):
                    continue
                entry = {
                    "id": chunk_id,
                    "section": title,
                    "text": chunk,
                    "level": section.get("level", 1),
                    "position_boost": 3 if i < 3 else 1,
                }
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
        ids = [entry["id"] for entry in self.section_chunks]
        self.vector_store.add(embeddings, ids)

    def decompose_query(self, query):
        q = query.lower()
        sub_queries = [query]
        
        # Add expansions based on keywords
        if "limit" in q or "drawback" in q or "weakness" in q:
            sub_queries.extend([
                "limitations of the method",
                "drawbacks and disadvantages",
                "weaknesses or negative results"
            ])
        if "method" in q or "how does" in q or "architecture" in q or "proposed" in q or "lora" in q:
            sub_queries.extend([
                "proposed method architecture",
                "how does the model work",
                "design and implementation details"
            ])
        if "dataset" in q or "benchmark" in q or "experiment" in q or "evaluation" in q:
            sub_queries.extend([
                "datasets and benchmarks used in experiments",
                "evaluation setup and baseline models",
                "experimental results and task performance"
            ])
        if "problem" in q or "address" in q or "motivation" in q:
            sub_queries.extend([
                "problem statement and motivation",
                "challenges addressed by the paper",
                "background and introduction to the problem"
            ])
        if "future" in q or "open problem" in q:
            sub_queries.extend([
                "future work and open questions",
                "conclusion and future research directions"
            ])
        
        return list(dict.fromkeys(sub_queries))

    def get_section_categories(self, title):
        title = title.lower()
        categories = []
        if "abstract" in title:
            categories.append("abstract")
        if "introduction" in title or "background" in title or "motivation" in title or "preliminar" in title:
            categories.append("introduction")
        if "problem" in title or "statement" in title:
            categories.append("introduction")
            categories.append("method")
        if "method" in title or "approach" in title or "architecture" in title or "framework" in title or "design" in title:
            categories.append("method")
        if "experiment" in title or "evaluation" in title or "result" in title or "analysis" in title or "ablation" in title or "setup" in title:
            categories.append("experiment")
        if "related work" in title or "related-work" in title or "literature review" in title:
            categories.append("related_work")
        elif "related" in title and "work" in title:
            categories.append("related_work")
        if "conclusion" in title or "discussion" in title or "limit" in title or "future" in title:
            categories.append("conclusion")
        if "appendix" in title or "annex" in title or title.strip() == "f" or "empirical experiments" in title:
            categories.append("appendix")
            categories.append("experiment")
        
        if not categories:
            categories.append("general")
        return categories

    def get_query_categories(self, query):
        q = query.lower()
        categories = []
        
        if any(w in q for w in ["definition", "what is", "define", "meaning of"]):
            categories.extend(["abstract", "introduction"])
        if any(w in q for w in ["problem", "address", "motivation", "challenge", "goal", "objective"]):
            categories.extend(["abstract", "introduction", "method"])
        if any(w in q for w in ["method", "how does", "architecture", "framework", "design", "propose", "proposed"]):
            categories.extend(["method", "abstract"])
        if any(w in q for w in ["dataset", "benchmark", "experiment", "evaluation", "result", "test", "metric", "accuracy"]):
            categories.extend(["experiment", "appendix"])
        if any(w in q for w in ["limit", "drawback", "weakness", "con", "disadvantage", "fail"]):
            categories.extend(["conclusion", "introduction", "method"])
        if any(w in q for w in ["future", "open problem", "next step", "extension", "conclusion"]):
            categories.extend(["conclusion"])
            
        return list(set(categories))

    def query(self, text, k=3):
        decomposed_queries = self.decompose_query(text)
        target_categories = self.get_query_categories(text)
        
        candidates = {}
        
        for sub_q in decomposed_queries:
            sub_q_categories = self.get_query_categories(sub_q)
            combined_categories = list(set(target_categories + sub_q_categories))
            
            query_embed = self.embedder.encode([sub_q])
            vec_results = self.vector_store.search(query_embed, k=15)
            
            sub_q_tokens = sub_q.lower().split()
            bm25_scores = self.bm25.get_scores(sub_q_tokens)
            
            for chunk_id, dist in vec_results:
                item = self.chunk_metadata.get(chunk_id)
                if item is None:
                    continue
                
                cosine_sim = 1.0 - (dist / 2.0)
                bm25_score = bm25_scores[chunk_id]

                sec_cats = self.get_section_categories(item["section"])
                overlap = set(sec_cats).intersection(combined_categories)
                section_boost = 1.0 if overlap else 0.0
                position_boost = item.get("position_boost", 1) / 3.0

                if chunk_id not in candidates:
                    candidates[chunk_id] = {
                        "chunk_id": chunk_id,
                        "text": item["text"],
                        "section": item["section"],
                        "cosine_sim": cosine_sim,
                        "bm25_score": bm25_score,
                        "section_boost": section_boost,
                        "position_boost": position_boost,
                    }
                else:
                    candidates[chunk_id]["cosine_sim"] = max(candidates[chunk_id]["cosine_sim"], cosine_sim)
                    candidates[chunk_id]["bm25_score"] = max(candidates[chunk_id]["bm25_score"], bm25_score)
                    candidates[chunk_id]["section_boost"] = max(candidates[chunk_id]["section_boost"], section_boost)
                    candidates[chunk_id]["position_boost"] = max(candidates[chunk_id]["position_boost"], position_boost)

        if not candidates:
            self.last_trace = {
                "original_query": text,
                "decomposed_queries": decomposed_queries,
                "confidence_score": 0.0,
                "message": "No candidates found"
            }
            return []

        candidate_list = list(candidates.values())
        
        cosines = [c["cosine_sim"] for c in candidate_list]
        bm25s = [c["bm25_score"] for c in candidate_list]
        
        min_cosine, max_cosine = min(cosines), max(cosines)
        min_bm25, max_bm25 = min(bm25s), max(bm25s)
        
        cosine_range = max_cosine - min_cosine
        bm25_range = max_bm25 - min_bm25
        
        for c in candidate_list:
            norm_cosine = (c["cosine_sim"] - min_cosine) / cosine_range if cosine_range > 0 else 1.0
            norm_bm25 = (c["bm25_score"] - min_bm25) / bm25_range if bm25_range > 0 else 1.0
            
            c["score"] = (
                0.35 * norm_cosine
                + 0.35 * norm_bm25
                + 0.15 * c["section_boost"]
                + 0.15 * c["position_boost"]
            )

        candidate_list = sorted(candidate_list, key=lambda x: x["score"], reverse=True)

        if target_categories == ["conclusion"] or (
            "conclusion" in target_categories and len(target_categories) <= 2
        ):
            conclusion_chunks = [
                c for c in candidate_list
                if "conclusion" in c["section"] or "future" in c["section"]
            ]
            if conclusion_chunks:
                candidate_list = conclusion_chunks + [
                    c for c in candidate_list if c not in conclusion_chunks
                ]

        top_chunks = candidate_list[:3]
        
        sentences = []
        for chunk_item in top_chunks:
            chunk_sentences = self.split_sentences(chunk_item["text"])
            for s in chunk_sentences:
                sentences.append({
                    "text": s.strip(),
                    "chunk_id": chunk_item["chunk_id"],
                    "section": chunk_item["section"]
                })
        
        seen_sentences = set()
        cleaned_sentences = []
        for s in sentences:
            s_text = s["text"]
            if not s_text or len(s_text) <= 40:
                continue
            if s_text.lower() in seen_sentences:
                continue
            if self.is_noise_sentence(s_text) or self.is_bad_sentence(s_text):
                continue
            seen_sentences.add(s_text.lower())
            cleaned_sentences.append(s)

        if not cleaned_sentences:
            self.last_trace = {
                "original_query": text,
                "decomposed_queries": decomposed_queries,
                "confidence_score": 0.0,
                "message": "No sentences survived filtering"
            }
            return []

        tokenized_sentences = [s["text"].lower().split() for s in cleaned_sentences]
        bm25_sent = BM25Okapi(tokenized_sentences)
        original_query_tokens = text.lower().split()
        sent_bm25_scores = bm25_sent.get_scores(original_query_tokens)
        
        min_s_bm25, max_s_bm25 = min(sent_bm25_scores), max(sent_bm25_scores)
        s_bm25_range = max_s_bm25 - min_s_bm25
        
        ranked_sentences = []
        for idx, s in enumerate(cleaned_sentences):
            raw_bm25 = sent_bm25_scores[idx]
            norm_bm25 = (raw_bm25 - min_s_bm25) / s_bm25_range if s_bm25_range > 0 else 1.0
            
            parent_chunk = candidates[s["chunk_id"]]
            sentence_score = 0.5 * norm_bm25 + 0.5 * parent_chunk["score"]
            
            is_def = self.is_definition_sentence(s["text"])
            if is_def and any(w in text.lower() for w in ["what is", "define", "meaning", "definition"]):
                sentence_score += 0.3
            if is_def and any(w in text.lower() for w in ["method", "proposed", "how does", "architecture", "lora"]):
                sentence_score += 0.25
                
            ranked_sentences.append((s["text"], sentence_score, is_def, s["section"]))

        ranked_sentences = sorted(ranked_sentences, key=lambda x: x[1], reverse=True)

        top_cosine = max_cosine
        cosine_confidence = float(max(0.0, min(1.0, (top_cosine - 0.2) / 0.6)))
        top_sentence_score = ranked_sentences[0][1] if ranked_sentences else 0.0
        confidence_score = float(max(cosine_confidence, min(1.0, top_sentence_score)))
        
        self.last_trace = {
            "original_query": text,
            "decomposed_queries": decomposed_queries,
            "target_categories": target_categories,
            "top_candidates": [
                {
                    "chunk_id": c["chunk_id"],
                    "section": c["section"],
                    "cosine_sim": float(c["cosine_sim"]),
                    "bm25_score": float(c["bm25_score"]),
                    "section_boost": float(c["section_boost"]),
                    "position_boost": float(c["position_boost"]),
                    "score": float(c["score"]),
                    "text_preview": c["text"][:100] + "..."
                } for c in candidate_list[:5]
            ],
            "ranked_sentences": [
                {
                    "text": s[0],
                    "score": float(s[1]),
                    "is_def": s[2],
                    "section": s[3]
                } for s in ranked_sentences[:5]
            ],
            "confidence_score": confidence_score
        }
        
        return [(s[0], s[1]) for s in ranked_sentences[:2]]