from atlasse.knowledge_engine.orchestration.query_orchestrator import QueryOrchestrator
from atlasse.knowledge_engine.paper_embeddings.memory_builder import PaperMemory
from atlasse.knowledge_engine.paper_understanding.llm_engine import LLMEngine

_STOPWORDS = {
    "what", "is", "an", "a", "the", "in", "on", "of", "for", "to", "with",
    "by", "at", "from", "this", "that", "it", "or", "and", "are", "does",
    "do", "did", "was", "were", "been", "has", "have", "had", "which",
    "paper", "mentioned", "used",
}


class PaperUnderstandingEngine:

    def __init__(self, json_path, paper_id=None, force_rebuild=False):
        self.paper_id = paper_id
        self.memory = PaperMemory(paper_id=paper_id)
        self.memory.build(json_path, paper_id=paper_id, force_rebuild=force_rebuild)
        self.orchestrator = QueryOrchestrator(self.memory)
        self.llm = LLMEngine()

    @staticmethod
    def _is_not_found(answer):
        lower = answer.lower()
        return any(p in lower for p in ["not found", "not clearly present", "cannot answer", "no answer"])

    def ask_with_provenance(self, question):
        result = self.orchestrator.ask_with_provenance(question)
        trace = self.memory.last_trace
        confidence = trace.get("confidence_score", result["confidence"])
        top_score = result["confidence"]

        if confidence < 0.05 and top_score < 0.5:
            return {**result, "answer": "This question does not seem related to the paper.", "rejected": True}

        if top_score >= 0.70:
            return result

        prompt = f"question: {question}\ncontext: {result['answer']}\nanswer:"
        llm_answer = self.llm.generate(prompt).strip()
        if not llm_answer or self._is_not_found(llm_answer) or len(llm_answer) < 15:
            return result

        return {**result, "answer": llm_answer, "llm_synthesized": True}

    def ask(self, question):
        return self.ask_with_provenance(question)["answer"]
