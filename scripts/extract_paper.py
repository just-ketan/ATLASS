from atlasse.knowledge_engine.paper_understanding.structured_extractor import StructuredExtractor
from atlasse.knowledge_engine.paper_ingestion.paper_loader import PaperLoader

def run():
    loader = PaperLoader()
    json_path = loader.load("2106.09685")   #hard coded
    extractor = StructuredExtractor(json_path)
    res = extractor.extract()

    print("\n\nStructured Output: \n")
    for k, v in res.items():
        print(f"{k.upper()}:\n{v}\n")

if __name__ == "__main__":
    run()