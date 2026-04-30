# script to derive reasoning of paper context from LLM

from atlasse.knowledge_engine.paper_understanding.paper_understanding_engine import PaperUnderstandingEngine

from atlasse.knowledge_engine.paper_ingestion.paper_loader import PaperLoader

def run():
	loader = PaperLoader()
	json_path = loader.load("2106.09685")
	engine = PaperUnderstandingEngine(json_path)
	while True:
		q = input("Ask ATLASS (understanding): ")
		answer = engine.ask(q)
		print("\nAnswer:\n", answer, "\n")
if __name__ == "__main__":
	run()
