import argparse

from atlasse.knowledge_engine.paper_ingestion.paper_loader import PaperLoader
from atlasse.knowledge_engine.paper_understanding.structured_extractor import StructuredExtractor


def run(paper_id="2106.09685"):
    loader = PaperLoader()
    json_path = loader.load(paper_id)
    extractor = StructuredExtractor(json_path, paper_id=paper_id)
    result = extractor.extract()

    print(f"\nPaper: {result['paper_id']}\n")
    for k, v in result["fields"].items():
        prov = result["provenance"][k]
        print(f"{k.upper()} (confidence: {prov['confidence']:.2f}):")
        print(v)
        if prov.get("citations"):
            print(prov["citations"])
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("paper_id", nargs="?", default="2106.09685")
    args = parser.parse_args()
    run(args.paper_id)
