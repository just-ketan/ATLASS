"""Phase 11: Benchmark suite for extraction quality and regression testing."""

from __future__ import annotations

import time
from typing import Callable

from atlasse_v2.core.types import SectionType
from atlasse_v2.evaluation.score_store import ScoreStore
from atlasse_v2.extraction.extractors.dataset import DatasetExtractor
from atlasse_v2.extraction.extractors.problem import ProblemExtractor
from atlasse_v2.memory.research_memory import ResearchMemory
from atlasse_v2.retrieval.evidence_ranker import EvidenceRanker
from atlasse_v2.specification.spec_builder import SpecBuilder

GOLDEN_PAPERS = [
    {"id": "2106.09685", "name": "LoRA", "family": "lora"},
    {"id": "1512.03385", "name": "ResNet", "family": "cnn"},
    {"id": "1706.03762", "name": "Transformer", "family": "transformer"},
    {"id": "1810.04805", "name": "BERT", "family": "transformer"},
    {"id": "2103.00020", "name": "CLIP", "family": "transformer"},
    {"id": "2304.02643", "name": "SAM", "family": "cnn"},
    {"id": "2010.11929", "name": "ViT", "family": "vit"},
    {"id": "1506.02640", "name": "YOLO", "family": "cnn"},
    {"id": "2104.14294", "name": "DINO", "family": "vit"},
    {"id": "2112.10752", "name": "Stable Diffusion", "family": "diffusion"},
]

SMOKE_PAPER = GOLDEN_PAPERS[0]


class BenchmarkSuite:
    def __init__(self, score_store: ScoreStore | None = None):
        self.golden_papers = GOLDEN_PAPERS
        self.score_store = score_store or ScoreStore()

    def run_extraction_eval(self, document_factory: Callable) -> dict:
        """Evaluate extraction on a synthetic document factory (e.g. make_sample_document)."""
        doc = document_factory()
        memory = ResearchMemory(doc.paper_id).build_from_document(doc)
        ranker = EvidenceRanker(memory, use_cross_encoder=False)

        dataset = DatasetExtractor(retriever=ranker).extract(doc.paper_id)
        problem = ProblemExtractor(retriever=ranker).extract(doc.paper_id)
        spec = SpecBuilder(ranker).build(doc.paper_id)

        dataset_ok = (
            not dataset.missing
            and dataset.supporting_spans
            and dataset.supporting_spans[0].provenance.section in (
                SectionType.EXPERIMENTS,
                SectionType.DATASETS,
                SectionType.APPENDIX,
            )
        )
        problem_ok = (
            not problem.missing
            and problem.supporting_spans
            and problem.supporting_spans[0].provenance.section in (
                SectionType.ABSTRACT,
                SectionType.INTRODUCTION,
            )
        )
        fields_distinct = (
            spec["fields"].get("dataset", {}).get("value")
            != spec["fields"].get("problem", {}).get("value")
        )
        reuse_flags = sum(
            1 for f in spec["fields"].values()
            if any("possible reuse detected" in a.lower() for a in f.get("assumptions", []))
        )
        missing_count = sum(
            1 for f in spec["fields"].values() if f.get("missing") or not f.get("value")
        )
        total_fields = len(spec["fields"])

        explicit_reuse = reuse_flags / max(total_fields, 1)
        intro_field_bleed = 0.0 if fields_distinct else 1.0
        hallucination_rate = intro_field_bleed
        evidence_precision = (
            (1.0 if dataset_ok else 0.0) + (1.0 if problem_ok else 0.0)
        ) / 2.0

        return {
            "paper_id": doc.paper_id,
            "dataset_extraction_ok": dataset_ok,
            "problem_extraction_ok": problem_ok,
            "fields_distinct": fields_distinct,
            "missing_field_rate": missing_count / max(total_fields, 1),
            "hallucination_rate": hallucination_rate,
            "explicit_field_reuse_rate": round(explicit_reuse, 3),
            "evidence_precision": round(evidence_precision, 3),
            "citation_precision": round(
                sum(1 for f in spec["fields"].values() if f.get("source_chunks")) / max(total_fields, 1),
                3,
            ),
            "passed": dataset_ok and problem_ok and fields_distinct and hallucination_rate == 0.0,
        }

    def run_smoke_regression(self, document_factory: Callable) -> dict:
        start = time.monotonic()
        extraction = self.run_extraction_eval(document_factory)
        elapsed = time.monotonic() - start
        result = {
            "suite": "smoke",
            "golden_papers_total": len(self.golden_papers),
            "golden_papers_tested": 1,
            "smoke_paper": SMOKE_PAPER["name"],
            "extraction": extraction,
            "passed": extraction["passed"],
            "elapsed_seconds": round(elapsed, 2),
        }
        self.score_store.append(result)
        return result

    def run_regression(self, document_factory: Callable) -> dict:
        """Full local regression — smoke subset only until golden PDFs are wired."""
        return self.run_smoke_regression(document_factory)

    def get_scores(self) -> dict:
        return self.score_store.load()

    def get_latest(self) -> dict | None:
        return self.score_store.latest()
