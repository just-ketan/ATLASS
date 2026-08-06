"""ATLASS v2 CLI — ingest, ask, status."""

from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="atlasse_v2", description="ATLASS v2 Research Cognition Engine")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Ingest a PDF through the v2 pipeline")
    ingest.add_argument("pdf_path", help="Path to PDF file")
    ingest.add_argument("--paper-id", help="Override paper ID")
    ingest.add_argument("--data-dir", default="data/v2")

    status = sub.add_parser("status", help="Get processing status for a paper")
    status.add_argument("paper_id")
    status.add_argument("--data-dir", default="data/v2")

    ask = sub.add_parser("ask", help="Ask a grounded question about a paper")
    ask.add_argument("paper_id")
    ask.add_argument("-q", "--question", required=True)
    ask.add_argument("--data-dir", default="data/v2")

    spec = sub.add_parser("spec", help="Show system specification for a paper")
    spec.add_argument("paper_id")
    spec.add_argument("--data-dir", default="data/v2")

    benchmark = sub.add_parser("benchmark", help="Run benchmark smoke regression")
    benchmark.add_argument("--data-dir", default="data/v2")

    repro = sub.add_parser("reproduction", help="Show reproduction report for a paper")
    repro.add_argument("paper_id")
    repro.add_argument("--data-dir", default="data/v2")

    accept = sub.add_parser("accept", help="Run golden paper acceptance suite")
    accept.add_argument("--data-dir", default="data/v2")
    accept.add_argument("--work-dir", default="data/v2/golden_pdfs")

    trace = sub.add_parser("agent-trace", help="Show agent orchestration trace for a paper")
    trace.add_argument("paper_id")
    trace.add_argument("--data-dir", default="data/v2")

    args = parser.parse_args(argv)

    if args.command == "ingest":
        from atlasse_v2.pipeline import PaperPipeline
        pipeline = PaperPipeline(data_dir=args.data_dir)
        result = pipeline.ingest(args.pdf_path, paper_id=args.paper_id)
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "status":
        from atlasse_v2.pipeline import PaperPipeline
        pipeline = PaperPipeline(data_dir=args.data_dir)
        print(json.dumps(pipeline.get_status(args.paper_id), indent=2))
        return 0

    if args.command == "ask":
        from atlasse_v2.memory.research_memory import ResearchMemory
        from atlasse_v2.qa.qa_pipeline import QAPipeline
        from atlasse_v2.retrieval.evidence_ranker import EvidenceRanker
        memory = ResearchMemory.load(args.paper_id, base_dir=f"{args.data_dir}/memory_indices")
        if not memory.chunks:
            print("Paper memory not found — run ingest first.", file=sys.stderr)
            return 1
        ranker = EvidenceRanker(memory)
        qa = QAPipeline(ranker)
        print(json.dumps(qa.ask(args.question, args.paper_id), indent=2))
        return 0

    if args.command == "spec":
        from atlasse_v2.pipeline import PaperPipeline
        pipeline = PaperPipeline(data_dir=args.data_dir)
        result = pipeline.get_spec(args.paper_id)
        if result is None:
            print("Specification not found — run ingest first.", file=sys.stderr)
            return 1
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "benchmark":
        from atlasse_v2.evaluation.benchmark import BenchmarkSuite
        from atlasse_v2.evaluation.fixtures import make_lora_sample_document
        from atlasse_v2.evaluation.score_store import ScoreStore
        suite = BenchmarkSuite(
            score_store=ScoreStore(path=f"{args.data_dir}/benchmark/scores.json")
        )
        print(json.dumps(suite.run_smoke_regression(make_lora_sample_document), indent=2))
        return 0

    if args.command == "reproduction":
        from atlasse_v2.pipeline import PaperPipeline
        pipeline = PaperPipeline(data_dir=args.data_dir)
        result = pipeline.get_reproduction_report(args.paper_id)
        if result is None:
            print("Reproduction report not found — run ingest first.", file=sys.stderr)
            return 1
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "accept":
        from pathlib import Path
        from atlasse_v2.evaluation.golden_acceptance import run_all_acceptance
        result = run_all_acceptance(args.data_dir, Path(args.work_dir))
        print(json.dumps(result, indent=2))
        return 0 if result["all_passed"] else 1

    if args.command == "agent-trace":
        from atlasse_v2.agents.orchestrator import AgentOrchestrator
        orch = AgentOrchestrator(data_dir=args.data_dir)
        result = orch.get_trace(args.paper_id)
        if result is None:
            print("Agent trace not found — run ingest first.", file=sys.stderr)
            return 1
        print(json.dumps(result, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
