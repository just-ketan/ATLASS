from atlasse.knowledge_engine.paper_embeddings.memory_builder import PaperMemory

def run():
    memory = PaperMemory()
    memory.build("data/processed_papers/2106.09685.json")
    while True:
        query = input("Ask ATLASS: ")
        res = memory.query(query)
        print("\n Top Results: \n")
        for r in res:
            print("-", r[:300], "\n")

if __name__ == "__main__":
    run()