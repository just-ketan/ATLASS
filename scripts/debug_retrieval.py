import argparse
import json
import sys

from atlasse.knowledge_engine.paper_ingestion.paper_loader import PaperLoader
from atlasse.knowledge_engine.paper_understanding.structured_extractor import StructuredExtractor


def run(paper_id="2106.09685", json_output=False):
    loader = PaperLoader()
    json_path = loader.load(paper_id)
    extractor = StructuredExtractor(json_path, paper_id=paper_id)

    fields = {
        "problem": "what problem does this paper address in machine learning or transformers",
        "method": "what method is proposed in this paper lora low rank adaptation",
        "dataset": "what datasets or benchmarks are used in this paper experiments",
        "limitations": "what are limitations or drawbacks of this method mentioned in paper",
        "future_work": "what future work or open problems are mentioned in conclusion",
    }

    for k, q in fields.items():
        ans = extractor.engine.ask(q)
        trace = getattr(extractor.engine.memory, "last_trace", {})
        block = {
            "field": k,
            "question": q,
            "answer": ans,
            "confidence": trace.get("confidence_score"),
            "intents": trace.get("intents"),
            "top_candidates": trace.get("top_candidates", [])[:3],
            "ranked_sentences": trace.get("ranked_sentences", [])[:3],
        }
        if json_output:
            print(json.dumps(block))
        else:
            print(f"\n--- FIELD: {k.upper()} ---")
            print(f"Question: {q}")
            print(f"Answer: {ans}")
            print(f"Confidence: {trace.get('confidence_score')}")
            print(f"Intents: {trace.get('intents')}")
            for cand in trace.get("top_candidates", [])[:3]:
                print(f"  [{cand.get('chunk_id')}] {cand.get('section')} score={cand.get('score'):.3f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("paper_id", nargs="?", default="2106.09685")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    run(args.paper_id, json_output=args.json)
