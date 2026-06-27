# main driver code for paper understanding

from atlasse.knowledge_engine.paper_embeddings.memory_builder import PaperMemory
from .llm_engine import LLMEngine

_STOPWORDS = {
    "what", "is", "an", "a", "the", "in", "on", "of", "for", "to", "with",
    "by", "at", "from", "this", "that", "it", "or", "and", "are", "does",
    "do", "did", "was", "were", "been", "has", "have", "had", "which",
    "paper", "mentioned", "does", "this", "are", "used", "does",
}


class PaperUnderstandingEngine:
    def __init__(self, json_path):
        self.memory = PaperMemory()
        self.memory.build(json_path)
        self.llm = LLMEngine()

    @staticmethod
    def _is_not_found(answer):
        lower = answer.lower()
        return any(p in lower for p in [
            "not found", "not clearly present", "cannot answer",
            "no answer", "does not contain",
        ])

    @staticmethod
    def _format_retrieved_answer(sentences):
        if not sentences:
            return "Answer not found in paper."
        combined = " ".join(sentences)
        if not combined.endswith("."):
            combined += "."
        return combined.strip()

    def ask(self, question):
        results = self.memory.query(question)
        if not results:
            return "Answer not found in paper."

        trace = getattr(self.memory, "last_trace", {})
        confidence = trace.get("confidence_score", 1.0)
        top_score = results[0][1] if results else 0.0

        if confidence < 0.05 and top_score < 0.5:
            return "This question does not seem related to the paper."

        best_sentences = [s for s, _ in results]
        context = " ".join(best_sentences)

        if top_score < 0.65:
            query_words = [w for w in question.lower().split() if w not in _STOPWORDS]
            if query_words and not any(word in context.lower() for word in query_words):
                return "Answer not found in paper."

        ranked = trace.get("ranked_sentences", [])
        top_ranked = ranked[0] if ranked else None
        is_definition_query = any(
            w in question.lower() for w in ["what is", "define", "meaning", "definition"]
        )

        if top_ranked and top_ranked.get("score", 0) >= 0.70:
            if is_definition_query and top_ranked.get("is_def"):
                return self._format_retrieved_answer([top_ranked["text"]])
            if top_score >= 0.75:
                return self._format_retrieved_answer(best_sentences)

        prompt = (
            f"question: {question}\n"
            f"context: {context}\n"
            f"answer:"
        )
        answer = self.llm.generate(prompt).strip()

        if not answer or self._is_not_found(answer) or len(answer) < 15:
            return self._format_retrieved_answer(best_sentences)

        return answer
