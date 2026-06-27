import os
import sys
from atlasse.knowledge_engine.paper_understanding.structured_extractor import StructuredExtractor
from atlasse.knowledge_engine.paper_ingestion.paper_loader import PaperLoader

def run():
    loader = PaperLoader()
    json_path = loader.load("2106.09685")
    extractor = StructuredExtractor(json_path)
    
    fields = {
        "problem": "what problem does this paper address in machine learning or transformers",
        "method": "what method is proposed in this paper lora low rank adaptation",
        "dataset": "what datasets or benchmarks are used in this paper experiments",
        "limitations": "what are limitations or drawbacks of this method mentioned in paper",
        "future_work": "what future work or open problems are mentioned in conclusion"
    }
    
    for k, q in fields.items():
        ans = extractor.engine.ask(q)
        print(f"\n--- FIELD: {k.upper()} ---")
        print(f"Question: {q}")
        print(f"Answer: {ans}")
        trace = getattr(extractor.engine.memory, "last_trace", {})
        print("Confidence Score:", trace.get("confidence_score"))
        print("Message:", trace.get("message"))
        print("Top Candidates:")
        for cand in trace.get("top_candidates", [])[:3]:
            print(f"  Chunk ID: {cand.get('chunk_id')}, Section: {cand.get('section')}, Cosine: {cand.get('cosine_sim')}, BM25: {cand.get('bm25_score')}, Score: {cand.get('score')}")
            print(f"  Text preview: {cand.get('text_preview')}")
        print("Ranked Sentences:")
        for sent in trace.get("ranked_sentences", [])[:3]:
            print(f"  Text: {sent.get('text')[:100]}..., Score: {sent.get('score')}, Def: {sent.get('is_def')}")

if __name__ == "__main__":
    run()
