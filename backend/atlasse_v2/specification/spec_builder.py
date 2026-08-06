"""Phase 7: Compose all extractors into a versioned system_spec.json.

Each field has independent evidence. No field reuses another field's answer.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from atlasse_v2.core.models import ExtractedField
from atlasse_v2.extraction.registry import EXTRACTORS
from atlasse_v2.retrieval.evidence_ranker import EvidenceRanker


SPEC_FIELDS = [
    "problem", "contribution", "task", "method", "architecture",
    "loss", "training", "evaluation", "dataset", "metric",
    "baseline", "limitation", "future_work",
]


class SpecBuilder:
    SPEC_DIR = "data/v2/specifications"

    def __init__(self, ranker: EvidenceRanker):
        self.ranker = ranker

    def build(self, paper_id: str) -> dict:
        fields: dict[str, dict] = {}
        for name in SPEC_FIELDS:
            extractor_cls = EXTRACTORS.get(name)
            if extractor_cls is None:
                continue
            extractor = extractor_cls(retriever=self.ranker)
            result: ExtractedField = extractor.extract(paper_id)
            fields[name] = {
                "value": result.value,
                "confidence": result.confidence,
                "missing": result.missing,
                "citations": result.citations,
                "assumptions": result.assumptions,
                "source_chunks": [
                    s.provenance.chunk_id for s in result.supporting_spans
                    if s.provenance.chunk_id
                ],
            }
        self._validate_no_reuse(fields)
        spec = {"paper_id": paper_id, "version": 1, "fields": fields}
        return spec

    @staticmethod
    def _validate_no_reuse(fields: dict[str, dict]) -> None:
        seen_values: dict[str, str] = {}
        for name, field in fields.items():
            value = field.get("value")
            if not value or field.get("missing"):
                continue
            normalized = value.strip()[:200]
            if normalized in seen_values:
                field["confidence"] = min(field.get("confidence", 0.0), 0.3)
                field["assumptions"] = field.get("assumptions", []) + [
                    f"Possible reuse detected with field '{seen_values[normalized]}'"
                ]
            else:
                seen_values[normalized] = name

    def save(self, spec: dict, base_dir: str | None = None) -> str:
        paper_id = spec["paper_id"]
        base = Path(base_dir or self.SPEC_DIR) / paper_id
        base.mkdir(parents=True, exist_ok=True)
        path = base / "system_spec.json"
        path.write_text(json.dumps(spec, indent=2))
        return str(path)
