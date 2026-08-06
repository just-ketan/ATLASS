# ATLASS v2 Task Breakdown

Source: [upgrade_v2.md](upgrade_v2.md)  
Plan: [plan_v2.md](plan_v2.md)  
Tracker: [tracker_v2.md](tracker_v2.md)  
Implementation: [backend/](backend/)

Task IDs follow the pattern `P{phase}-T{number}`. Status values: `pending`, `in_progress`, `done`, `blocked`.

---

## Sprint 1 — Foundation (Phases 1, 5, 4)

Current sprint. Goal: parsed documents → fine-grained memory → ranked retrieval → wired extractors.

| ID | Task | Phase | Status | Module |
|----|------|-------|--------|--------|
| P1-T01 | Define core models: Provenance, ParsedDocument, SectionNode, ResearchChunk, GraphEntity | 1 | done | `backend/atlasse_v2/core/` |
| P1-T02 | Implement DocumentParser with backend chain interface | 1 | done | `backend/atlasse_v2/parsing/` |
| P1-T03 | Implement SectionTreeBuilder with paragraph IDs | 1 | done | `backend/atlasse_v2/parsing/` |
| P1-T04 | Implement PyMuPDF backend | 1 | done | `backend/atlasse_v2/parsing/backends/` |
| P1-T05 | Implement GROBID backend | 1 | pending | `backend/atlasse_v2/parsing/backends/` |
| P1-T06 | Implement Docling backend | 1 | pending | `backend/atlasse_v2/parsing/backends/` |
| P1-T07 | Implement pdfplumber backend | 1 | pending | `backend/atlasse_v2/parsing/backends/` |
| P1-T08 | Implement OCR fallback backend | 1 | pending | `backend/atlasse_v2/parsing/backends/` |
| P1-T09 | Persist ParsedDocument to `data/v2/parsed/{paper_id}/` | 1 | pending | `backend/atlasse_v2/parsing/` |
| P1-T10 | Unit tests: section classification accuracy | 1 | pending | `backend/tests/parsing/` |
| P1-T11 | Unit tests: paragraph ID uniqueness and coverage | 1 | pending | `backend/tests/parsing/` |
| P1-T12 | Integration test: parse LoRA paper (2106.09685) | 1 | pending | `backend/tests/parsing/` |
| P5-T01 | Implement ResearchMemory builder from ParsedDocument | 5 | pending | `backend/atlasse_v2/memory/` |
| P5-T02 | Split into chunk types: paragraph, table, caption, equation, algorithm | 5 | pending | `backend/atlasse_v2/memory/` |
| P5-T03 | Attach metadata: chunk_id, page, section, paragraph, entities, keywords, citations | 5 | pending | `backend/atlasse_v2/memory/` |
| P5-T04 | Generate embeddings and build FAISS index | 5 | pending | `backend/atlasse_v2/memory/` |
| P5-T05 | Persist memory index to `data/v2/memory_indices/{paper_id}/` | 5 | pending | `backend/atlasse_v2/memory/` |
| P5-T06 | Unit tests: chunk granularity and metadata completeness | 5 | pending | `backend/tests/memory/` |
| P4-T01 | Implement BM25 retriever over research memory | 4 | pending | `backend/atlasse_v2/retrieval/` |
| P4-T02 | Implement dense embedding retriever | 4 | pending | `backend/atlasse_v2/retrieval/` |
| P4-T03 | Implement CrossEncoder reranker | 4 | pending | `backend/atlasse_v2/retrieval/` |
| P4-T04 | Implement section prior weighting | 4 | pending | `backend/atlasse_v2/retrieval/` |
| P4-T05 | Implement entity overlap and citation overlap scoring | 4 | pending | `backend/atlasse_v2/retrieval/` |
| P4-T06 | Implement combined EvidenceRanker with score formula | 4 | pending | `backend/atlasse_v2/retrieval/` |
| P4-T07 | Top-k evidence gate (only reranked spans reach LLM) | 4 | pending | `backend/atlasse_v2/retrieval/` |
| P4-T08 | Retrieval debug trace output | 4 | pending | `backend/atlasse_v2/retrieval/` |
| P4-T09 | Unit tests: score composition and section filtering | 4 | pending | `backend/tests/retrieval/` |
| P3-T01 | Define BaseExtractor contract | 3 | done | `backend/atlasse_v2/extraction/` |
| P3-T02 | Implement 13 dedicated extractors (stub) | 3 | done | `backend/atlasse_v2/extraction/extractors/` |
| P3-T03 | Wire extractors to EvidenceRanker retriever | 3 | pending | `backend/atlasse_v2/extraction/` |
| P3-T04 | Add LLM evidence gate (extract only from provided spans) | 3 | pending | `backend/atlasse_v2/extraction/` |
| P3-T05 | Missing-field detection and explicit reporting | 3 | pending | `backend/atlasse_v2/extraction/` |
| P3-T06 | Integration test: DatasetExtractor uses experiment sections only | 3 | pending | `backend/tests/extraction/` |
| P3-T07 | Integration test: ProblemExtractor uses abstract/intro only | 3 | pending | `backend/tests/extraction/` |

---

## Sprint 2 — Graph and Specification (Phases 2, 7)

| ID | Task | Phase | Status | Module |
|----|------|-------|--------|--------|
| P2-T01 | Define 18 entity types and 9 edge types | 2 | done | `backend/atlasse_v2/core/types.py` |
| P2-T02 | Implement SemanticPaperGraph with save/load | 2 | done | `backend/atlasse_v2/graph/` |
| P2-T03 | Replace heuristic entity extraction with Phase 3 extractor output | 2 | pending | `backend/atlasse_v2/graph/` |
| P2-T04 | Implement edge inference (uses_dataset, compares_against, etc.) | 2 | pending | `backend/atlasse_v2/graph/` |
| P2-T05 | Graph query API: entities by type, neighbors, paths | 2 | pending | `backend/atlasse_v2/graph/` |
| P2-T06 | Unit tests: entity deduplication and edge integrity | 2 | pending | `backend/tests/graph/` |
| P2-T07 | Integration test: LoRA graph has Method, Dataset, Loss entities | 2 | pending | `backend/tests/graph/` |
| P7-T01 | Implement SpecBuilder composing all extractors | 7 | pending | `backend/atlasse_v2/specification/` |
| P7-T02 | 15 fields with independent evidence sets | 7 | pending | `backend/atlasse_v2/specification/` |
| P7-T03 | No-field-reuse validation | 7 | pending | `backend/atlasse_v2/specification/` |
| P7-T04 | Versioned system_spec.json artifact | 7 | pending | `backend/atlasse_v2/specification/` |
| P7-T05 | API: create, retrieve, review/correct | 7 | pending | `backend/atlasse_v2/api/` |
| P7-T06 | Persist to `data/v2/specifications/` | 7 | pending | `backend/atlasse_v2/specification/` |
| P7-T07 | Integration test: LoRA spec has distinct field values | 7 | pending | `backend/tests/specification/` |
| P7-T08 | Integration test: no intro text in dataset/metric fields | 7 | pending | `backend/tests/specification/` |

---

## Sprint 3 — QA and Blueprint (Phases 6, 8)

| ID | Task | Phase | Status | Module |
|----|------|-------|--------|--------|
| P6-T01 | Implement intent classifier | 6 | pending | `backend/atlasse_v2/qa/` |
| P6-T02 | Map intents to required entity types | 6 | pending | `backend/atlasse_v2/qa/` |
| P6-T03 | Implement evidence validator | 6 | pending | `backend/atlasse_v2/qa/` |
| P6-T04 | Implement answer generator with citations | 6 | pending | `backend/atlasse_v2/qa/` |
| P6-T05 | Implement citation verifier | 6 | pending | `backend/atlasse_v2/qa/` |
| P6-T06 | "The paper does not specify." fallback | 6 | pending | `backend/atlasse_v2/qa/` |
| P6-T07 | QA pipeline orchestrator | 6 | pending | `backend/atlasse_v2/qa/` |
| P6-T08 | API: POST /v2/papers/{id}/ask | 6 | pending | `backend/atlasse_v2/api/` |
| P6-T09 | Golden query test on LoRA paper | 6 | pending | `backend/tests/qa/` |
| P8-T01 | Architecture graph → module decomposition | 8 | pending | `backend/atlasse_v2/blueprint/` |
| P8-T02 | Derive data/training/evaluation/inference flows | 8 | pending | `backend/atlasse_v2/blueprint/` |
| P8-T03 | Project tree generation with evidence mapping | 8 | pending | `backend/atlasse_v2/blueprint/` |
| P8-T04 | Refuse modules without graph entity support | 8 | pending | `backend/atlasse_v2/blueprint/` |
| P8-T05 | Versioned blueprint artifact | 8 | pending | `backend/atlasse_v2/blueprint/` |
| P8-T06 | API: create, retrieve, review/approve | 8 | pending | `backend/atlasse_v2/api/` |
| P8-T07 | Integration test: LoRA blueprint maps modules to evidence | 8 | pending | `backend/tests/blueprint/` |

---

## Sprint 4 — Baseline and Reproduction (Phases 9, 10)

| ID | Task | Phase | Status | Module |
|----|------|-------|--------|--------|
| P9-T01 | Implement model family detector (20+ families) | 9 | pending | `backend/atlasse_v2/baseline/` |
| P9-T02 | Create family-specific template library | 9 | pending | `backend/atlasse_v2/baseline/templates/` |
| P9-T03 | Template filling from research graph + spec | 9 | pending | `backend/atlasse_v2/baseline/` |
| P9-T04 | Explicit assumption labeling for missing values | 9 | pending | `backend/atlasse_v2/baseline/` |
| P9-T05 | Refuse unsupported families with explanation | 9 | pending | `backend/atlasse_v2/baseline/` |
| P9-T06 | Generated project with evidence manifest | 9 | pending | `backend/atlasse_v2/baseline/` |
| P9-T07 | API: generate, retrieve baseline | 9 | pending | `backend/atlasse_v2/api/` |
| P9-T08 | Integration test: LoRA → LoRA-family baseline (not MLP) | 9 | pending | `backend/tests/baseline/` |
| P10-T01 | Reproduction level classifier | 10 | pending | `backend/atlasse_v2/reproduction/` |
| P10-T02 | Status label assignment | 10 | pending | `backend/atlasse_v2/reproduction/` |
| P10-T03 | Smoke test runner with bounded execution | 10 | pending | `backend/atlasse_v2/reproduction/` |
| P10-T04 | Comparability verdict (never synthetic vs paper) | 10 | pending | `backend/atlasse_v2/reproduction/` |
| P10-T05 | Reproduction report artifact | 10 | pending | `backend/atlasse_v2/reproduction/` |
| P10-T06 | API: run, retrieve report | 10 | pending | `backend/atlasse_v2/api/` |

---

## Sprint 5 — Evaluation, Agents, Production (Phases 11, 12, 14)

| ID | Task | Phase | Status | Module |
|----|------|-------|--------|--------|
| P11-T01 | Benchmark suite scaffold for 100 arXiv papers | 11 | pending | `backend/atlasse_v2/evaluation/` |
| P11-T02 | Extraction accuracy metrics | 11 | pending | `backend/atlasse_v2/evaluation/` |
| P11-T03 | Hallucination rate measurement | 11 | pending | `backend/atlasse_v2/evaluation/` |
| P11-T04 | Evidence and citation precision metrics | 11 | pending | `backend/atlasse_v2/evaluation/` |
| P11-T05 | Blueprint and baseline correctness scoring | 11 | pending | `backend/atlasse_v2/evaluation/` |
| P11-T06 | QA exact match evaluation | 11 | pending | `backend/atlasse_v2/evaluation/` |
| P11-T07 | Score tracking and CI regression gate | 11 | pending | `backend/atlasse_v2/evaluation/` |
| P11-T08 | Golden paper set (10 papers) | 11 | pending | `backend/atlasse_v2/evaluation/golden/` |
| P12-T01 | Document Agent | 12 | pending | `backend/atlasse_v2/agents/` |
| P12-T02 | Retrieval Agent | 12 | pending | `backend/atlasse_v2/agents/` |
| P12-T03 | Research Agent | 12 | pending | `backend/atlasse_v2/agents/` |
| P12-T04 | Evidence Agent | 12 | pending | `backend/atlasse_v2/agents/` |
| P12-T05 | Specification Agent | 12 | pending | `backend/atlasse_v2/agents/` |
| P12-T06 | Blueprint Agent | 12 | pending | `backend/atlasse_v2/agents/` |
| P12-T07 | Baseline Agent | 12 | pending | `backend/atlasse_v2/agents/` |
| P12-T08 | Evaluation Agent | 12 | pending | `backend/atlasse_v2/agents/` |
| P12-T09 | Agent orchestrator with structured handoffs | 12 | pending | `backend/atlasse_v2/agents/` |
| P14-T01 | Redis caching layer | 14 | pending | `backend/atlasse_v2/infra/` |
| P14-T02 | Background job queue | 14 | pending | `backend/atlasse_v2/infra/` |
| P14-T03 | Streaming response support | 14 | pending | `backend/atlasse_v2/infra/` |
| P14-T04 | Structured logging | 14 | pending | `backend/atlasse_v2/infra/` |
| P14-T05 | OpenTelemetry tracing | 14 | pending | `backend/atlasse_v2/infra/` |
| P14-T06 | Unit test suite | 14 | pending | `backend/tests/` |
| P14-T07 | Integration test suite | 14 | pending | `backend/tests/` |
| P14-T08 | Snapshot tests | 14 | pending | `backend/tests/` |

---

## Sprint 6 — UI and Acceptance (Phases 13, 15)

| ID | Task | Phase | Status | Module |
|----|------|-------|--------|--------|
| P13-T01 | Evidence viewer API | 13 | pending | `backend/atlasse_v2/api/` |
| P13-T02 | Graph explorer API | 13 | pending | `backend/atlasse_v2/api/` |
| P13-T03 | Architecture DAG API | 13 | pending | `backend/atlasse_v2/api/` |
| P13-T04 | Section tree API | 13 | pending | `backend/atlasse_v2/api/` |
| P13-T05 | Entity browser API | 13 | pending | `backend/atlasse_v2/api/` |
| P13-T06 | Assumption tracker API | 13 | pending | `backend/atlasse_v2/api/` |
| P13-T07 | Missing information tracker API | 13 | pending | `backend/atlasse_v2/api/` |
| P13-T08 | Confidence heatmap data API | 13 | pending | `backend/atlasse_v2/api/` |
| P13-T09 | Blueprint/spec diff APIs | 13 | pending | `backend/atlasse_v2/api/` |
| P15-T01 | LoRA golden paper acceptance | 15 | pending | `backend/tests/acceptance/` |
| P15-T02 | ResNet golden paper acceptance | 15 | pending | `backend/tests/acceptance/` |
| P15-T03 | Transformer golden paper acceptance | 15 | pending | `backend/tests/acceptance/` |
| P15-T04 | BERT golden paper acceptance | 15 | pending | `backend/tests/acceptance/` |
| P15-T05 | CLIP golden paper acceptance | 15 | pending | `backend/tests/acceptance/` |
| P15-T06 | SAM golden paper acceptance | 15 | pending | `backend/tests/acceptance/` |
| P15-T07 | ViT golden paper acceptance | 15 | pending | `backend/tests/acceptance/` |
| P15-T08 | YOLO golden paper acceptance | 15 | pending | `backend/tests/acceptance/` |
| P15-T09 | DINO golden paper acceptance | 15 | pending | `backend/tests/acceptance/` |
| P15-T10 | Stable Diffusion golden paper acceptance | 15 | pending | `backend/tests/acceptance/` |

---

## Completed Tasks

| ID | Task | Completed |
|----|------|-----------|
| P1-T01 | Core models defined | 2026-08-06 |
| P1-T02 | DocumentParser orchestrator | 2026-08-06 |
| P1-T03 | SectionTreeBuilder | 2026-08-06 |
| P1-T04 | PyMuPDF backend | 2026-08-06 |
| P2-T01 | Entity/edge type definitions | 2026-08-06 |
| P2-T02 | SemanticPaperGraph save/load | 2026-08-06 |
| P3-T01 | BaseExtractor contract | 2026-08-06 |
| P3-T02 | 13 dedicated extractors (stub) | 2026-08-06 |

---

## Blocked Tasks

None currently.

---

## Task Dependencies

```text
P1 (Parsing)
  └→ P5 (Memory)
       └→ P4 (Retrieval)
            └→ P3 (Extraction)
                 └→ P2 (Graph) — entity population from extractors
                 └→ P6 (QA)
                 └→ P7 (Specification)
                      └→ P8 (Blueprint)
                           └→ P9 (Baseline)
                                └→ P10 (Reproduction)
                                     └→ P11 (Evaluation)
                                          └→ P12 (Agents)
                                               └→ P13 (UI)
                                                    └→ P14 (Production)
                                                         └→ P15 (Acceptance)
```

---

## How to Use This File

1. Pick tasks from the current sprint (Sprint 1)
2. Mark status in this file and mirror checkboxes in [tracker_v2.md](tracker_v2.md)
3. Implement in [backend/atlasse_v2/](backend/atlasse_v2/)
4. Add tests under `backend/tests/`
5. Update tracker when tasks complete
6. Do not skip dependency order unless explicitly decoupling for parallel work
