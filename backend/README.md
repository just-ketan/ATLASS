# ATLASS v2 Backend — Research Cognition Engine

ATLASS v2 is a **research cognition engine**, not a PDF chatbot or RAG system.

Every downstream artifact consumes **structured research objects** with full provenance — never raw paragraphs.

## Pipeline

```text
Paper
  → Structural parsing          (Phase 1)
  → Evidence extraction         (Phase 3)
  → Typed knowledge graph       (Phase 2)
  → Research memory             (Phase 5)
  → Specification generation    (Phase 7)
  → Blueprint generation        (Phase 8)
  → Baseline synthesis          (Phase 9)
  → Reproduction planning       (Phase 10)
```

## Package Layout

| Module | Phase | Purpose |
|--------|-------|---------|
| `atlasse_v2/parsing/` | 1 | Robust document parsing with provenance |
| `atlasse_v2/graph/` | 2 | Typed semantic paper graph |
| `atlasse_v2/extraction/` | 3 | Dedicated field extractors |
| `atlasse_v2/retrieval/` | 4 | BM25 + dense + cross-encoder reranking |
| `atlasse_v2/memory/` | 5 | Paragraph-level research memory |
| `atlasse_v2/qa/` | 6 | Evidence-validated question answering |
| `atlasse_v2/specification/` | 7 | Per-field system specification |
| `atlasse_v2/blueprint/` | 8 | Evidence-derived implementation blueprint |
| `atlasse_v2/baseline/` | 9 | Model-family template baseline generator |
| `atlasse_v2/reproduction/` | 10 | Reproduction classification engine |
| `atlasse_v2/evaluation/` | 11 | Benchmark suite and regression harness |
| `atlasse_v2/agents/` | 12 | Agentic pipeline with structured objects |
| `atlasse_v2/api/` | 13 | Rich backend API for UI |
| `atlasse_v2/infra/` | 14 | Production infrastructure |

## Running

```bash
# From repo root
export PYTHONPATH=$(pwd)/backend
python -m uvicorn atlasse_v2.api.app:app --host 0.0.0.0 --port 8001 --reload
```

## Design Principles

1. **Graph objects only** — downstream stages never consume raw paragraphs
2. **Dedicated extractors** — one focused module per research field, not one giant prompt
3. **Evidence ranking** — BM25 + dense + cross-encoder + section priors before LLM
4. **Explicit uncertainty** — missing information reported, never hallucinated
5. **Provenance everywhere** — page, section, paragraph ID, confidence, citations on every artifact

## Documentation

- [plan_v2.md](../plan_v2.md) — phase-wise development track
- [tracker_v2.md](../tracker_v2.md) — implementation progress
- [tasks_v2.md](../tasks_v2.md) — detailed task breakdown
