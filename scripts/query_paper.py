from atlasse.knowledge_engine.paper_embeddings.memory_builder import PaperMemory
from atlasse.knowledge_engine.paper_ingestion.paper_loader import PaperLoader
from atlasse.knowledge_engine.paper_understanding.paper_understanding_engine import PaperUnderstandingEngine

def run():
    loader = PaperLoader()
	json_path = loader.load("2106.09685")
	engine = PaperUnderstandingEngine(json_path)
    
    while True:
        query = input("Ask ATLASS: ")
        answer = engine.ask(query)
        print("\n Asnwer: \n", answer, "\n")

if __name__ == "__main__":
    run()