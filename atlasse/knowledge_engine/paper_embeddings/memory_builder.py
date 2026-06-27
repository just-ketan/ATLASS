import json
import os
import re
from collections import defaultdict

from rank_bm25 import BM25Okapi

from atlasse.knowledge_engine.retrieval.section_router import (
    detect_intent,
    expand_query,
    get_section_categories,
    section_matches_intent,
    target_categories_for_query,
)
from .chunker import TextChunker
from .embedder import Embedder
from .vector_store import VectorStore


class PaperMemory:

    INDEX_DIR = "data/memory_indices"

    def __init__(self, paper_id=None):
        self.paper_id = paper_id
        self.chunker = TextChunker()
        self.embedder = Embedder()
        self.vector_store = None
        self.texts = []
        self.bm25 = None
        self.chunk_metadata = {}
        self.section_chunks = []
        self.last_trace = {}
        self._section_index = defaultdict(list)

    @staticmethod
    def split_sentences(text):
        return re.split(r'(?<=[.!?])\s+', text)

    @staticmethod
    def is_useful_chunk(text):
        if len(text.strip()) < 50:
            return False
        num_digits = sum(c.isdigit() for c in text)
        if num_digits > len(text) * 0.15:
            return False
        special = sum(not c.isalnum() and not c.isspace() for c in text)
        if special > len(text) * 0.2:
            return False
        return True

    @staticmethod
    def is_noise_sentence(s):
        return len(s.lower().strip()) < 15

    @staticmethod
    def is_bad_sentence(s):
        s = s.lower()
        if s.count("|") > 2:
            return True
        num_digits = sum(c.isdigit() for c in s)
        return num_digits > len(s) * 0.4

    @staticmethod
    def is_definition_sentence(s):
        s_l = s.lower()
        keywords = ["is a", "is an", "refers to", "is called", "we propose", "we introduce", "named", "known as"]
        return any(k in s_l for k in keywords)

    def _should_skip_section(self, title):
        return "reference" in title and "related" not in title

    def _position_boost(self, section_title, chunk_index):
        title = section_title.lower()
        if "abstract" in title or "introduction" in title:
            return 3 if chunk_index < 3 else 1
        if "appendix" in title or "annex" in title:
            return 2 if chunk_index < 2 else 1
        return 2 if chunk_index < 2 else 1

    def _index_path(self):
        if not self.paper_id:
            return None
        return os.path.join(self.INDEX_DIR, self.paper_id)

    def build(self, json_path, paper_id=None, force_rebuild=False):
        if paper_id:
            self.paper_id = paper_id
        elif not self.paper_id:
            self.paper_id = os.path.splitext(os.path.basename(json_path))[0]

        index_path = self._index_path()
        meta_path = os.path.join(index_path, "chunks.json") if index_path else None

        if not force_rebuild and index_path and os.path.exists(meta_path):
            self._load_from_disk(index_path)
            return

        with open(json_path) as f:
            data = json.load(f)

        self.chunk_metadata = {}
        self.section_chunks = []
        self._section_index = defaultdict(list)
        chunk_id = 0

        for section in data["sections"]:
            title = section["title"].lower()
            if self._should_skip_section(title):
                continue

            is_appendix = "appendix" in title or "annex" in title
            chunks = self.chunker.chunk(section["text"])

            for i, chunk in enumerate(chunks):
                if not self.is_useful_chunk(chunk):
                    continue
                entry = {
                    "id": chunk_id,
                    "paper_id": self.paper_id,
                    "section": title,
                    "text": chunk,
                    "level": section.get("level", 1),
                    "position_boost": self._position_boost(title, i),
                    "is_appendix": is_appendix,
                }
                self.section_chunks.append(entry)
                self.chunk_metadata[chunk_id] = entry
                self._section_index[title].append(chunk_id)
                chunk_id += 1

        self.texts = [x["text"] for x in self.section_chunks]
        tokenized_corpus = [t.lower().split() for t in self.texts]
        self.bm25 = BM25Okapi(tokenized_corpus)

        embeddings = self.embedder.encode(self.texts)
        dim = embeddings.shape[1]
        self.vector_store = VectorStore(dim)
        ids = [entry["id"] for entry in self.section_chunks]
        self.vector_store.add(embeddings, ids)

        if index_path:
            self._save_to_disk(index_path)

    def _save_to_disk(self, index_path):
        os.makedirs(index_path, exist_ok=True)
        self.vector_store.save(index_path)
        with open(os.path.join(index_path, "chunks.json"), "w") as f:
            json.dump(self.section_chunks, f)

    def _load_from_disk(self, index_path):
        self.vector_store = VectorStore.load(index_path)
        self.embedder.dim = self.vector_store.dim
        with open(os.path.join(index_path, "chunks.json")) as f:
            self.section_chunks = json.load(f)
        self.chunk_metadata = {c["id"]: c for c in self.section_chunks}
        self._section_index = defaultdict(list)
        for entry in self.section_chunks:
            self._section_index[entry["section"]].append(entry["id"])
        self.texts = [x["text"] for x in self.section_chunks]
        self.bm25 = BM25Okapi([t.lower().split() for t in self.texts])

    def _filtered_chunk_ids(self, target_categories):
        if not target_categories or target_categories == ["general"]:
            return None
        matched = []
        for chunk_id, item in self.chunk_metadata.items():
            if section_matches_intent(item["section"], target_categories):
                matched.append(chunk_id)
        return matched or None

    def _score_candidates(self, candidates):
        if not candidates:
            return []

        cosines = [c["cosine_sim"] for c in candidates]
        bm25s = [c["bm25_score"] for c in candidates]
        min_cosine, max_cosine = min(cosines), max(cosines)
        min_bm25, max_bm25 = min(bm25s), max(bm25s)
        cosine_range = max_cosine - min_cosine
        bm25_range = max_bm25 - min_bm25

        for c in candidates:
            norm_cosine = (c["cosine_sim"] - min_cosine) / cosine_range if cosine_range > 0 else 1.0
            norm_bm25 = (c["bm25_score"] - min_bm25) / bm25_range if bm25_range > 0 else 1.0
            c["score"] = (
                0.30 * norm_cosine
                + 0.30 * norm_bm25
                + 0.25 * c["section_boost"]
                + 0.15 * c["position_boost"]
            )

        return sorted(candidates, key=lambda x: x["score"], reverse=True)

    def _bm25_candidate_ids(self, scores, k=20, filter_ids=None):
        filter_set = set(filter_ids) if filter_ids else None
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        ids = []
        for chunk_id, score in ranked:
            if score <= 0:
                break
            if filter_set is not None and chunk_id not in filter_set:
                continue
            ids.append(chunk_id)
            if len(ids) >= k:
                break
        return ids

    def _prioritize_by_intent(self, candidate_list, intents):
        if "future_work" in intents or "limitations" in intents:
            preferred = [
                c for c in candidate_list
                if any(k in c["section"] for k in ["conclusion", "discussion", "future", "limit"])
            ]
            if preferred:
                return preferred + [c for c in candidate_list if c not in preferred]
        if "dataset" in intents:
            preferred = [
                c for c in candidate_list
                if any(k in c["section"] for k in ["experiment", "appendix", "evaluation", "setup", "empirical"])
            ]
            if preferred:
                return preferred + [c for c in candidate_list if c not in preferred]
        return candidate_list

    def query(self, text, k=3, trace_id=None):
        decomposed_queries = expand_query(text)
        target_categories = target_categories_for_query(text)
        intents = detect_intent(text)
        filter_ids = self._filtered_chunk_ids(target_categories)

        candidates = {}

        for sub_q in decomposed_queries:
            sub_q_categories = target_categories_for_query(sub_q)
            combined_categories = list(set(target_categories + sub_q_categories))
            sub_filter = self._filtered_chunk_ids(combined_categories) or filter_ids

            query_embed = self.embedder.encode([sub_q])
            vec_results = self.vector_store.search(query_embed, k=20, filter_ids=sub_filter)
            bm25_scores = self.bm25.get_scores(sub_q.lower().split())
            result_ids = {chunk_id: dist for chunk_id, dist in vec_results}
            for chunk_id in self._bm25_candidate_ids(bm25_scores, k=20, filter_ids=sub_filter):
                result_ids.setdefault(chunk_id, 2.0)

            for chunk_id, dist in result_ids.items():
                item = self.chunk_metadata.get(chunk_id)
                if item is None:
                    continue

                cosine_sim = 1.0 - (dist / 2.0)
                sec_cats = get_section_categories(item["section"])
                overlap = set(sec_cats).intersection(combined_categories)
                section_boost = 1.0 if overlap else 0.0
                position_boost = item.get("position_boost", 1) / 3.0

                if chunk_id not in candidates:
                    candidates[chunk_id] = {
                        "chunk_id": chunk_id,
                        "paper_id": item.get("paper_id", self.paper_id),
                        "text": item["text"],
                        "section": item["section"],
                        "cosine_sim": cosine_sim,
                        "bm25_score": bm25_scores[chunk_id],
                        "section_boost": section_boost,
                        "position_boost": position_boost,
                    }
                else:
                    c = candidates[chunk_id]
                    c["cosine_sim"] = max(c["cosine_sim"], cosine_sim)
                    c["bm25_score"] = max(c["bm25_score"], bm25_scores[chunk_id])
                    c["section_boost"] = max(c["section_boost"], section_boost)
                    c["position_boost"] = max(c["position_boost"], position_boost)

        if not candidates:
            for sub_q in decomposed_queries:
                query_embed = self.embedder.encode([sub_q])
                vec_results = self.vector_store.search(query_embed, k=20)
                bm25_scores = self.bm25.get_scores(sub_q.lower().split())
                result_ids = {chunk_id: dist for chunk_id, dist in vec_results}
                for chunk_id in self._bm25_candidate_ids(bm25_scores, k=20):
                    result_ids.setdefault(chunk_id, 2.0)
                for chunk_id, dist in result_ids.items():
                    item = self.chunk_metadata.get(chunk_id)
                    if item is None or chunk_id in candidates:
                        continue
                    candidates[chunk_id] = {
                        "chunk_id": chunk_id,
                        "paper_id": item.get("paper_id", self.paper_id),
                        "text": item["text"],
                        "section": item["section"],
                        "cosine_sim": 1.0 - (dist / 2.0),
                        "bm25_score": bm25_scores[chunk_id],
                        "section_boost": 0.0,
                        "position_boost": item.get("position_boost", 1) / 3.0,
                    }

        if not candidates:
            self.last_trace = {
                "trace_id": trace_id,
                "paper_id": self.paper_id,
                "original_query": text,
                "decomposed_queries": decomposed_queries,
                "intents": intents,
                "target_categories": target_categories,
                "confidence_score": 0.0,
                "message": "No candidates found",
            }
            return []

        candidate_list = self._score_candidates(list(candidates.values()))
        candidate_list = self._prioritize_by_intent(candidate_list, intents)
        top_chunks = candidate_list[:k]

        sentences = []
        for chunk_item in top_chunks:
            for s in self.split_sentences(chunk_item["text"]):
                sentences.append({
                    "text": s.strip(),
                    "chunk_id": chunk_item["chunk_id"],
                    "paper_id": chunk_item.get("paper_id", self.paper_id),
                    "section": chunk_item["section"],
                })

        seen = set()
        cleaned = []
        for s in sentences:
            if not s["text"] or len(s["text"]) <= 40:
                continue
            key = s["text"].lower()
            if key in seen or self.is_noise_sentence(s["text"]) or self.is_bad_sentence(s["text"]):
                continue
            seen.add(key)
            cleaned.append(s)

        if not cleaned:
            self.last_trace = {
                "trace_id": trace_id,
                "paper_id": self.paper_id,
                "original_query": text,
                "confidence_score": 0.0,
                "message": "No sentences survived filtering",
            }
            return []

        bm25_sent = BM25Okapi([s["text"].lower().split() for s in cleaned])
        sent_scores = bm25_sent.get_scores(text.lower().split())
        min_s, max_s = min(sent_scores), max(sent_scores)
        s_range = max_s - min_s

        ranked = []
        for idx, s in enumerate(cleaned):
            norm_bm25 = (sent_scores[idx] - min_s) / s_range if s_range > 0 else 1.0
            parent = candidates[s["chunk_id"]]
            sentence_score = 0.5 * norm_bm25 + 0.5 * parent["score"]

            is_def = self.is_definition_sentence(s["text"])
            if is_def and any(w in text.lower() for w in ["what is", "define", "meaning", "definition"]):
                sentence_score += 0.3
            if is_def and any(w in text.lower() for w in ["method", "proposed", "how does", "architecture"]):
                sentence_score += 0.25
            if "limit" in text.lower() and any(w in s["text"].lower() for w in ["limit", "drawback", "weakness", "fail", "unclear"]):
                sentence_score += 0.2
            if "future" in text.lower() and any(w in s["text"].lower() for w in ["future", "open", "extend", "investigate"]):
                sentence_score += 0.2
            sentence_score = max(0.0, min(1.0, sentence_score))

            ranked.append({
                "text": s["text"],
                "score": sentence_score,
                "is_def": is_def,
                "section": s["section"],
                "chunk_id": s["chunk_id"],
                "paper_id": s.get("paper_id", self.paper_id),
            })

        ranked.sort(key=lambda x: x["score"], reverse=True)
        max_cosine = max(c["cosine_sim"] for c in candidate_list)

        query_tokens = [w for w in text.lower().split() if len(w) > 3 and w not in {
            "what", "does", "this", "that", "with", "from", "have", "paper", "mentioned",
        }]
        retrieved_text = " ".join(r["text"].lower() for r in ranked[:3])
        token_overlap = any(t in retrieved_text for t in query_tokens) if query_tokens else True

        confidence = float(max(
            max(0.0, min(1.0, (max_cosine - 0.2) / 0.6)),
            ranked[0]["score"] if ranked else 0.0,
        ))
        confidence = max(0.0, min(1.0, confidence))
        if query_tokens and not token_overlap and not detect_intent(text):
            confidence = min(confidence, 0.05)

        self.last_trace = {
            "trace_id": trace_id,
            "paper_id": self.paper_id,
            "original_query": text,
            "decomposed_queries": decomposed_queries,
            "intents": intents,
            "target_categories": target_categories,
            "filter_applied": filter_ids is not None,
            "top_candidates": [
                {
                    "chunk_id": c["chunk_id"],
                    "paper_id": c.get("paper_id", self.paper_id),
                    "section": c["section"],
                    "cosine_sim": float(c["cosine_sim"]),
                    "bm25_score": float(c["bm25_score"]),
                    "section_boost": float(c["section_boost"]),
                    "score": float(c["score"]),
                    "text_preview": c["text"][:100] + "...",
                }
                for c in candidate_list[:5]
            ],
            "ranked_sentences": ranked[:5],
            "confidence_score": confidence,
            "token_overlap": token_overlap,
        }

        return [(r["text"], r["score"], r) for r in ranked[:k]]
