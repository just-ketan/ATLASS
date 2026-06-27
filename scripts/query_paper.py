import argparse

from atlasse.knowledge_engine.paper_ingestion.paper_loader import PaperLoader
from atlasse.knowledge_engine.paper_understanding.paper_understanding_engine import PaperUnderstandingEngine


def run(paper_id="2106.09685"):
    loader = PaperLoader()
    json_path = loader.load(paper_id)
    engine = PaperUnderstandingEngine(json_path, paper_id=paper_id)

    while True:
        try:
            query = input("Ask ATLASS: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not query:
            continue
        result = engine.ask_with_provenance(query)
        print(f"\nAnswer:\n{result['answer']}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("paper_id", nargs="?", default="2106.09685")
    args = parser.parse_args()
    run(args.paper_id)
