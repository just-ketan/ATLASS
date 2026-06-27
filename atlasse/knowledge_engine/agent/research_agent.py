"""Phase 10: autonomous research agent loop."""

from atlasse.knowledge_engine.corpus.corpus_memory import CorpusMemory
from atlasse.knowledge_engine.graph.knowledge_graph import KnowledgeGraph
from atlasse.knowledge_engine.orchestration.query_orchestrator import QueryOrchestrator
from atlasse.knowledge_engine.paper_embeddings.memory_builder import PaperMemory
from atlasse.knowledge_engine.paper_understanding.llm_engine import LLMEngine


RESEARCH_QUERIES = [
    "what problem does this paper address",
    "what method is proposed",
    "what are the main experimental results",
    "what are limitations of this method",
    "what future work is suggested",
]


class ResearchAgent:
    """Autonomous literature exploration and synthesis agent."""

    def __init__(self, corpus: CorpusMemory = None, paper_id: str = None, json_path: str = None):
        self.corpus = corpus
        self.paper_id = paper_id
        self.llm = LLMEngine()
        self.graphs = {}

        if corpus is None and json_path:
            self.memory = PaperMemory(paper_id=paper_id)
            self.memory.build(json_path, paper_id=paper_id)
            self.orchestrator = QueryOrchestrator(self.memory)
        elif corpus and paper_id:
            self.memory = corpus.papers.get(paper_id)
            self.orchestrator = QueryOrchestrator(self.memory) if self.memory else None
        else:
            self.memory = None
            self.orchestrator = None

    def _build_graph(self, paper_id):
        memory = self.corpus.papers[paper_id] if self.corpus else self.memory
        if not memory:
            return None
        graph = KnowledgeGraph(paper_id=paper_id)
        graph.build_from_chunks(memory.chunk_metadata)
        graph.save()
        self.graphs[paper_id] = graph
        return graph

    def understand_paper(self, paper_id: str = None) -> dict:
        pid = paper_id or self.paper_id
        memory = self.corpus.papers[pid] if self.corpus else self.memory
        if not memory:
            return {"error": f"Paper {pid} not found"}

        orch = QueryOrchestrator(memory)
        understanding = {}
        for key, query in zip(
            ["problem", "method", "results", "limitations", "future_work"],
            RESEARCH_QUERIES,
        ):
            result = orch.ask_with_provenance(query)
            understanding[key] = result

        graph = self._build_graph(pid)
        understanding["graph_summary"] = graph.summary() if graph else {}
        understanding["paper_id"] = pid
        return understanding

    def compare_papers(self, paper_ids: list[str], aspect: str = "method") -> dict:
        if not self.corpus:
            return {"error": "Corpus required for comparison"}

        query_map = {
            "method": "what method is proposed",
            "problem": "what problem does this paper address",
            "limitations": "what are limitations",
            "results": "what are the main experimental results",
        }
        query = query_map.get(aspect, aspect)
        comparisons = {}

        for pid in paper_ids:
            memory = self.corpus.papers.get(pid)
            if not memory:
                continue
            orch = QueryOrchestrator(memory)
            comparisons[pid] = orch.ask_with_provenance(query)

        synthesis = self._synthesize_comparison(comparisons, aspect)
        return {
            "aspect": aspect,
            "papers": paper_ids,
            "comparisons": comparisons,
            "synthesis": synthesis,
        }

    def _synthesize_comparison(self, comparisons: dict, aspect: str) -> str:
        parts = []
        for pid, data in comparisons.items():
            parts.append(f"Paper {pid}: {data.get('answer', 'N/A')}")
        context = "\n".join(parts)
        prompt = f"Compare these papers on {aspect}:\n{context}\nComparison:"
        return self.llm.generate(prompt).strip()

    def identify_gaps(self, paper_id: str = None) -> dict:
        understanding = self.understand_paper(paper_id)
        limitations = understanding.get("limitations", {}).get("answer", "")
        future = understanding.get("future_work", {}).get("answer", "")

        prompt = (
            f"Based on these research notes, identify open research gaps:\n"
            f"Limitations: {limitations}\n"
            f"Future work: {future}\n"
            f"Research gaps:"
        )
        gaps = self.llm.generate(prompt).strip()

        return {
            "paper_id": paper_id or self.paper_id,
            "limitations": limitations,
            "future_work": future,
            "gaps": gaps,
        }

    def suggest_experiments(self, paper_id: str = None) -> dict:
        gaps = self.identify_gaps(paper_id)
        prompt = (
            f"Given these research gaps:\n{gaps['gaps']}\n"
            f"Suggest 3 concrete ML experiments to address them:\n"
        )
        experiments = self.llm.generate(prompt).strip()
        return {**gaps, "suggested_experiments": experiments}

    def explore(self, topic: str) -> dict:
        """Cross-paper exploration on a topic."""
        if not self.corpus:
            result = self.orchestrator.ask_with_provenance(topic) if self.orchestrator else {}
            return {"topic": topic, "single_paper": result}

        results = self.corpus.query(topic, k=5)
        papers_hit = list({r["paper_id"] for r in results})

        return {
            "topic": topic,
            "papers_found": papers_hit,
            "evidence": results,
            "cross_paper": len(papers_hit) > 1,
        }

    def run_research_loop(self, paper_ids: list[str] = None) -> dict:
        """Full autonomous research loop."""
        paper_ids = paper_ids or (list(self.corpus.papers.keys()) if self.corpus else [self.paper_id])
        report = {"papers": {}, "comparisons": {}, "gaps": {}, "experiments": {}}

        for pid in paper_ids:
            self.paper_id = pid
            if self.corpus:
                self.memory = self.corpus.papers[pid]
                self.orchestrator = QueryOrchestrator(self.memory)
            report["papers"][pid] = self.understand_paper(pid)

        if len(paper_ids) > 1:
            for aspect in ["method", "limitations"]:
                report["comparisons"][aspect] = self.compare_papers(paper_ids, aspect)

        primary = paper_ids[0]
        report["gaps"] = self.identify_gaps(primary)
        report["experiments"] = self.suggest_experiments(primary)
        return report
