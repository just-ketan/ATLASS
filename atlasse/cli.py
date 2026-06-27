"""Unified CLI for ATLASS."""

import argparse
import json
import sys

from atlasse.knowledge_engine.agent.research_agent import ResearchAgent
from atlasse.knowledge_engine.corpus.corpus_memory import CorpusMemory
from atlasse.knowledge_engine.observability.eval_harness import EvalHarness
from atlasse.knowledge_engine.paper_ingestion.paper_loader import PaperLoader
from atlasse.knowledge_engine.paper_understanding.paper_understanding_engine import PaperUnderstandingEngine
from atlasse.knowledge_engine.paper_understanding.structured_extractor import StructuredExtractor


def cmd_ingest(args):
    from scripts.ingest_paper import ingest
    path = ingest(args.paper_id)
    print(f"Ingested: {path}")


def cmd_ask(args):
    loader = PaperLoader()
    json_path = loader.load(args.paper_id)
    engine = PaperUnderstandingEngine(json_path, paper_id=args.paper_id)
    if args.query:
        result = engine.ask_with_provenance(args.query)
        print(json.dumps(result, indent=2) if args.json else result["answer"])
    else:
        while True:
            try:
                q = input("Ask ATLASS: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not q:
                continue
            result = engine.ask_with_provenance(q)
            print(f"\n{result['answer']}\n")
            if result.get("citations"):
                print(result["citations"])


def cmd_extract(args):
    loader = PaperLoader()
    json_path = loader.load(args.paper_id)
    extractor = StructuredExtractor(json_path, paper_id=args.paper_id)
    result = extractor.extract()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for k, v in result["fields"].items():
            prov = result["provenance"][k]
            print(f"{k.upper()} (confidence: {prov['confidence']:.2f}):")
            print(f"{v}\n")


def cmd_eval(args):
    loader = PaperLoader()
    json_path = loader.load(args.paper_id)
    from atlasse.knowledge_engine.paper_embeddings.memory_builder import PaperMemory
    memory = PaperMemory(paper_id=args.paper_id)
    memory.build(json_path, force_rebuild=args.rebuild)
    report = EvalHarness(memory).run(args.paper_id)
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["failed"] == 0 else 1)


def cmd_corpus(args):
    corpus = CorpusMemory.from_processed_dir(force_rebuild=args.rebuild)
    print(f"Papers in corpus: {corpus.list_papers()}")
    if args.query:
        results = corpus.query(args.query, paper_ids=args.papers)
        print(json.dumps(results, indent=2))


def cmd_agent(args):
    loader = PaperLoader()
    if args.mode == "explore":
        if args.papers and len(args.papers) > 1:
            corpus = CorpusMemory.from_processed_dir()
            for pid in args.papers:
                if pid not in corpus.papers:
                    corpus.add_paper(loader.load(pid), paper_id=pid)
            agent = ResearchAgent(corpus=corpus)
            print(json.dumps(agent.explore(args.query or "method comparison"), indent=2))
        else:
            pid = args.paper_id or (args.papers[0] if args.papers else "2106.09685")
            json_path = loader.load(pid)
            agent = ResearchAgent(json_path=json_path, paper_id=pid)
            print(json.dumps(agent.explore(args.query or "what method is proposed"), indent=2))
    elif args.mode == "compare":
        corpus = CorpusMemory.from_processed_dir()
        for pid in args.papers:
            if pid not in corpus.papers:
                corpus.add_paper(loader.load(pid), paper_id=pid)
        agent = ResearchAgent(corpus=corpus)
        print(json.dumps(agent.compare_papers(args.papers, args.aspect), indent=2))
    elif args.mode == "gaps":
        json_path = loader.load(args.paper_id)
        agent = ResearchAgent(json_path=json_path, paper_id=args.paper_id)
        print(json.dumps(agent.identify_gaps(), indent=2))
    elif args.mode == "experiments":
        json_path = loader.load(args.paper_id)
        agent = ResearchAgent(json_path=json_path, paper_id=args.paper_id)
        print(json.dumps(agent.suggest_experiments(), indent=2))
    else:
        json_path = loader.load(args.paper_id)
        agent = ResearchAgent(json_path=json_path, paper_id=args.paper_id)
        print(json.dumps(agent.run_research_loop([args.paper_id]), indent=2))


def main():
    parser = argparse.ArgumentParser(prog="atlass", description="ATLASS research cognition engine")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    sub = parser.add_subparsers(dest="command")

    p_ingest = sub.add_parser("ingest", help="Ingest a paper from arXiv")
    p_ingest.add_argument("paper_id", help="arXiv paper ID")
    p_ingest.set_defaults(func=cmd_ingest)

    p_ask = sub.add_parser("ask", help="Ask a question about a paper")
    p_ask.add_argument("paper_id", nargs="?", default="2106.09685")
    p_ask.add_argument("-q", "--query", help="Question (interactive if omitted)")
    p_ask.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="Output JSON")
    p_ask.set_defaults(func=cmd_ask)

    p_extract = sub.add_parser("extract", help="Structured field extraction")
    p_extract.add_argument("paper_id", nargs="?", default="2106.09685")
    p_extract.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="Output JSON")
    p_extract.set_defaults(func=cmd_extract)

    p_eval = sub.add_parser("eval", help="Run retrieval evaluation harness")
    p_eval.add_argument("paper_id", nargs="?", default="2106.09685")
    p_eval.add_argument("--rebuild", action="store_true")
    p_eval.set_defaults(func=cmd_eval)

    p_corpus = sub.add_parser("corpus", help="Multi-paper corpus operations")
    p_corpus.add_argument("-q", "--query", help="Cross-paper query")
    p_corpus.add_argument("--papers", nargs="*", help="Limit to specific papers")
    p_corpus.add_argument("--rebuild", action="store_true")
    p_corpus.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="Output JSON")
    p_corpus.set_defaults(func=cmd_corpus)

    p_agent = sub.add_parser("agent", help="Autonomous research agent")
    p_agent.add_argument("--mode", choices=["loop", "explore", "compare", "gaps", "experiments"], default="loop")
    p_agent.add_argument("--paper-id", default="2106.09685")
    p_agent.add_argument("--papers", nargs="*", default=["2106.09685"])
    p_agent.add_argument("-q", "--query")
    p_agent.add_argument("--aspect", default="method")
    p_agent.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="Output JSON")
    p_agent.set_defaults(func=cmd_agent)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
