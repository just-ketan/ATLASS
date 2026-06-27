import os

from atlasse.knowledge_engine.paper_embeddings.memory_builder import PaperMemory


class CorpusMemory:
    """Phase 8: multi-paper semantic memory with cross-paper retrieval."""

    def __init__(self):
        self.papers = {}
        self.chunk_metadata = {}
        self.global_chunk_map = {}
        self._next_global_id = 0

    def add_paper(self, json_path, paper_id=None, force_rebuild=False):
        memory = PaperMemory(paper_id=paper_id)
        memory.build(json_path, paper_id=paper_id, force_rebuild=force_rebuild)
        pid = memory.paper_id
        self.papers[pid] = memory

        for local_id, meta in memory.chunk_metadata.items():
            global_id = self._next_global_id
            self._next_global_id += 1
            entry = dict(meta)
            entry["global_id"] = global_id
            entry["local_id"] = local_id
            entry["paper_id"] = pid
            self.chunk_metadata[global_id] = entry
            self.global_chunk_map[(pid, local_id)] = global_id

        return pid

    def list_papers(self):
        return list(self.papers.keys())

    def query(self, text, paper_ids=None, k=3):
        """Cross-paper retrieval: query all or selected papers, merge by score."""
        targets = paper_ids or list(self.papers.keys())
        all_results = []

        for pid in targets:
            memory = self.papers.get(pid)
            if not memory:
                continue
            results = memory.query(text, k=k)
            for item in results:
                if len(item) == 3:
                    sent_text, score, meta = item
                else:
                    sent_text, score = item
                    meta = {}
                all_results.append({
                    "text": sent_text,
                    "score": score,
                    "paper_id": pid,
                    "chunk_id": meta.get("chunk_id", -1),
                    "section": meta.get("section", ""),
                })

        all_results.sort(key=lambda x: x["score"], reverse=True)
        self.last_trace = {
            "original_query": text,
            "papers_searched": targets,
            "results": all_results[:5],
            "confidence_score": all_results[0]["score"] if all_results else 0.0,
        }
        return all_results[:k]

    def query_paper(self, paper_id, text, k=3):
        return self.query(text, paper_ids=[paper_id], k=k)

    @classmethod
    def from_processed_dir(cls, processed_dir="data/processed_papers", force_rebuild=False):
        corpus = cls()
        if not os.path.isdir(processed_dir):
            return corpus
        for fname in sorted(os.listdir(processed_dir)):
            if fname.endswith(".json"):
                corpus.add_paper(
                    os.path.join(processed_dir, fname),
                    paper_id=fname.replace(".json", ""),
                    force_rebuild=force_rebuild,
                )
        return corpus
