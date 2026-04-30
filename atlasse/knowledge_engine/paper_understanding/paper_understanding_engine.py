# main driver code for paper understanding

from atlasse.knowledge_engine.paper_embeddings.memory_builder import PaperMemory
from .llm_engine import LLMEngine

class PaperUnderstandingEngine:
	def __init__(self, json_path):
		self.memory = PaperMemory()
		self.memory.build(json_path)
		self.llm =  LLMEngine()
	
	def ask(self, question):
		results = self.memory.query(question)
		if not results:
			return "Answer not found in paper."
		# use top score instead of word overlap
		top_score = results[0][1] if len(results[0]) > 1 else 0
		# threshold (tune slightly if needed)
		if top_score < 0.5:
			return "This question does not seem related to the paper."

		# Check relevance (lower distance = better match)
		avg_distance = sum([d for _, d in results]) / len(results)

		best_sentences = [s for s, _ in results]
		context = " ".join(best_sentences)

		# Basic sanity check
		if not any(word in context.lower() for word in question.lower().split()):
			return "Answer not found in paper."

		prompt = f"""
Write a clean 2-sentence explanation.

Rules:
- Use only the given text
- Do NOT include numbers or experiments
- Focus only on definition

Text:
{context}

Answer:
"""
		answer = self.llm.generate(prompt)
		answer = answer.replace("We propose", "").strip()
		return answer
