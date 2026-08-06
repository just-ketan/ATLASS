# ATLASS v2 Phase Tracker

Last updated: 2026-08-06  
Source of truth: [plan_v2.md](plan_v2.md)  
Task breakdown: [tasks_v2.md](tasks_v2.md)  
Implementation root: [backend/](backend/)

---

## Product Goal

Transform ATLASS from a chunk-and-summarize RAG system into a **research cognition engine** where every artifact — specification, blueprint, baseline, QA answer — traces to structured research objects with explicit provenance.

```text
Paper → parse → graph → extract → spec → blueprint → baseline → reproduce
         ↑ evidence-ranked memory feeds every stage ↑
```

## Primary Acceptance Objective

ATLASS v2 is complete when it correctly processes golden papers (LoRA, ResNet, Transformer, BERT, CLIP, SAM, ViT, YOLO, DINO, Stable Diffusion) without:

- Repeating introduction paragraphs across unrelated fields
- Extracting datasets from non-experiment sections
- Hallucinating blueprint modules unsupported by evidence
- Generating generic PyTorch templates for known model families
- Comparing synthetic metrics against paper-reported results

Every missing field must be explicitly marked. **Never hallucinate.**

---

## Phase Summary

| Phase | Name | Plan Status | Tracker State | Next Action |
|-------|------|-------------|---------------|-------------|
| 1 | Robust Document Parsing | Scaffolded | PyMuPDF backend + section tree | Add GROBID/Docling backends, OCR fallback |
| 2 | Semantic Paper Graph | Scaffolded | Typed entities/edges, heuristic build | Wire to Phase 3 extractors for entity population |
| 3 | Research Information Extraction | Scaffolded | 13 extractors with stub logic | Connect to Phase 4 retriever, add LLM evidence gate |
| 4 | Evidence Ranking | Not started | — | Implement BM25 + dense + cross-encoder reranker |
| 5 | Research Memory | Not started | — | Build paragraph/table/equation chunk store |
| 6 | Question Answering | Not started | — | Implement intent → retrieve → validate → answer pipeline |
| 7 | System Specification | Not started | — | Compose extractors into versioned system_spec.json |
| 8 | Blueprint Generator | Not started | — | Derive module tree from architecture graph |
| 9 | Baseline Generator | Not started | — | Model-family detection + template filling |
| 10 | Reproduction Engine | Not started | — | Smoke/partial/full classification |
| 11 | Evaluation Framework | Not started | — | Golden paper benchmark harness |
| 12 | Agentic Pipeline | Not started | — | Agent orchestration with structured objects |
| 13 | UI Improvements | Not started | — | Rich API contracts for frontend |
| 14 | Production Quality | Not started | — | Tests, caching, observability |
| 15 | Success Criteria | Not started | — | Golden paper acceptance run |

---

## Phase 1 — Robust Document Parsing

**Status:** scaffolded

- [x] Define `ParsedDocument`, `SectionNode` core models
- [x] Canonical section type enumeration (14 section types)
- [x] `DocumentParser` orchestrator with backend chain interface
- [x] `SectionTreeBuilder` with paragraph IDs and cross-references
- [x] PyMuPDF backend implementation
- [ ] GROBID backend integration
- [ ] Docling backend integration
- [ ] pdfplumber backend integration
- [ ] OCR fallback for scanned PDFs
- [ ] Persist parsed document artifact to `data/v2/parsed/`
- [ ] Unit tests for section classification and paragraph ID assignment
- [ ] Integration test on LoRA paper (2106.09685)

---

## Phase 2 — Semantic Paper Graph

**Status:** scaffolded

- [x] Define 18 entity types and 9 edge types
- [x] `GraphEntity` and `GraphEdge` models with provenance
- [x] `SemanticPaperGraph` with add/query/save/load
- [x] Heuristic entity extraction from parsed sections
- [ ] Entity extraction driven by Phase 3 extractors (not heuristics)
- [ ] Edge inference (uses_dataset, compares_against, etc.)
- [ ] Graph query API (entities by type, neighbors, paths)
- [ ] Persist to `data/v2/knowledge_graphs/`
- [ ] Unit tests for entity deduplication and edge integrity
- [ ] Verify graph for LoRA paper: Method, Dataset, Loss entities present

---

## Phase 3 — Research Information Extraction

**Status:** scaffolded

- [x] `BaseExtractor` contract (evidence-gated extraction)
- [x] Extractor registry with 13 dedicated modules
- [x] Section-targeted evidence queries per extractor
- [ ] Connect extractors to Phase 4 retriever (currently no retriever)
- [ ] LLM evidence gate: extract only from provided spans
- [ ] Missing-field detection and explicit reporting
- [ ] Confidence scoring from evidence quality
- [ ] Integration test: DatasetExtractor returns experiment-section evidence only
- [ ] Integration test: ProblemExtractor returns abstract/intro evidence only

---

## Phase 4 — Evidence Ranking

**Status:** not started

- [ ] BM25 retriever over research memory
- [ ] Dense embedding retriever (sentence-transformers)
- [ ] CrossEncoder reranker
- [ ] Section prior weighting
- [ ] Entity overlap scoring
- [ ] Recency-within-paper scoring
- [ ] Combined score formula implementation
- [ ] Top-k evidence gate before LLM
- [ ] Retrieval debug trace output
- [ ] Unit tests for score composition
- [ ] Benchmark: dataset query precision vs v1 baseline

---

## Phase 5 — Research Memory

**Status:** not started

- [ ] `ResearchMemory` builder from `ParsedDocument`
- [ ] Chunk types: paragraph, semantic_block, table, caption, equation, algorithm
- [ ] Per-chunk metadata: chunk_id, page, section, paragraph, entities, keywords, citations
- [ ] Embedding generation and FAISS index
- [ ] Persist to `data/v2/memory_indices/`
- [ ] Incremental indexing support
- [ ] Unit tests for chunk granularity and metadata completeness

---

## Phase 6 — Question Answering

**Status:** not started

- [ ] Intent classifier (definition, problem, method, dataset, limitation, etc.)
- [ ] Required entity type mapping per intent
- [ ] Retriever integration (Phase 4)
- [ ] Evidence validator (reject spans outside required sections)
- [ ] Answer generator with citation formatting
- [ ] Citation verifier (every claim maps to a span)
- [ ] "The paper does not specify." fallback
- [ ] API endpoint: `POST /v2/papers/{id}/ask`
- [ ] Unit tests for evidence-missing case
- [ ] Golden query test on LoRA paper

---

## Phase 7 — System Specification

**Status:** not started

- [ ] `SpecBuilder` composing all Phase 3 extractors
- [ ] 15 dedicated fields with independent evidence sets
- [ ] Field schema: value, citations, confidence, missing, source_chunks
- [ ] No-field-reuse validation
- [ ] Versioned `system_spec.json` artifact
- [ ] API: create, retrieve, review/correct
- [ ] Persist to `data/v2/specifications/`
- [ ] Integration test: LoRA spec has distinct field values
- [ ] Integration test: no introduction text in dataset/metric fields

---

## Phase 8 — Blueprint Generator

**Status:** not started

- [ ] Architecture graph → module decomposition
- [ ] Data flow, training flow, evaluation flow, inference flow derivation
- [ ] Project tree generation with evidence mapping
- [ ] Interface and dependency extraction
- [ ] Refuse modules without graph entity support
- [ ] Versioned blueprint artifact with evidence links
- [ ] API: create, retrieve, review/approve
- [ ] Persist to `data/v2/blueprints/`
- [ ] Integration test: LoRA blueprint maps attention → attention.py

---

## Phase 9 — Baseline Generator

**Status:** not started

- [ ] Model family detector (20+ families)
- [ ] Family-specific template library
- [ ] Template filling from research graph + spec
- [ ] Explicit assumption labeling for missing values
- [ ] Refuse unsupported families with explanation
- [ ] Generated project with evidence manifest
- [ ] API: generate, retrieve
- [ ] Persist to `data/v2/baselines/`
- [ ] Integration test: LoRA paper → LoRA-family baseline (not MLP)

---

## Phase 10 — Reproduction Engine

**Status:** not started

- [ ] Reproduction level classifier (smoke, partial, full)
- [ ] Status labels: executable, architecture_matched, dataset_unavailable, etc.
- [ ] Smoke test runner (bounded execution)
- [ ] Never compare synthetic metrics against paper metrics
- [ ] Comparability verdict with explicit limitations
- [ ] Reproduction report artifact
- [ ] API: run, retrieve report
- [ ] Persist to `data/v2/reproduction_reports/`

---

## Phase 11 — Evaluation Framework

**Status:** not started

- [ ] Benchmark suite for 100 arXiv papers
- [ ] Metrics: extraction accuracy, hallucination rate, evidence/citation precision
- [ ] Blueprint and baseline correctness scoring
- [ ] QA exact match evaluation
- [ ] Score tracking over time
- [ ] CI regression test on every commit
- [ ] Golden paper set: LoRA, ResNet, Transformer, BERT, CLIP, SAM, ViT, YOLO, DINO, Stable Diffusion

---

## Phase 12 — Agentic Pipeline

**Status:** not started

- [ ] Document Agent (Phase 1 orchestration)
- [ ] Retrieval Agent (Phase 4/5 orchestration)
- [ ] Research Agent (Phase 2/3 orchestration)
- [ ] Evidence Agent (validation and ranking)
- [ ] Specification Agent (Phase 7)
- [ ] Blueprint Agent (Phase 8)
- [ ] Baseline Agent (Phase 9)
- [ ] Evaluation Agent (Phase 11)
- [ ] Structured object handoffs (no free-form text between agents)
- [ ] Agent trace logging

---

## Phase 13 — UI Improvements

**Status:** not started

- [ ] Evidence viewer API
- [ ] Graph explorer API
- [ ] Architecture DAG API
- [ ] Section tree API
- [ ] Citation browser API
- [ ] Entity browser API
- [ ] Assumption tracker API
- [ ] Missing information tracker API
- [ ] Blueprint diff API
- [ ] Specification diff API
- [ ] Confidence heatmap data API
- [ ] Frontend integration (separate from backend scope)

---

## Phase 14 — Production Quality

**Status:** not started

- [ ] Redis caching layer
- [ ] Background job queue
- [ ] Streaming response support
- [ ] Persistent vector DB (beyond FAISS files)
- [ ] Structured logging
- [ ] OpenTelemetry tracing
- [ ] Unit test suite (`backend/tests/`)
- [ ] Integration test suite
- [ ] Golden paper tests
- [ ] Snapshot tests
- [ ] Benchmark harness in CI

---

## Phase 15 — Success Criteria

**Status:** not started

- [ ] LoRA paper: correct field extraction, no intro reuse
- [ ] ResNet paper: architecture-matched blueprint
- [ ] Transformer paper: correct module decomposition
- [ ] BERT paper: correct task/dataset/metric extraction
- [ ] CLIP paper: multimodal architecture in graph
- [ ] SAM paper: segmentation-specific baseline
- [ ] ViT paper: vision transformer family baseline
- [ ] YOLO paper: detection-specific extraction
- [ ] DINO paper: self-supervised method extraction
- [ ] Stable Diffusion paper: diffusion family baseline
- [ ] All artifacts trace to explicit evidence
- [ ] Benchmark scores meet minimum thresholds

---

## Scope Guardrails

- Never patch v1 prompts to mask v2 architectural requirements
- Never allow extractors to answer outside retrieved evidence
- Never generate blueprint modules without graph entity support
- Never compare synthetic smoke metrics against paper-reported results
- Never reuse one field's extracted text for another field
- Prioritize correctness over completeness
- Report uncertainty explicitly; never hallucinate

---

## Current Sprint Focus

**Sprint 1 (current):** Foundation — Phases 1, 5, 4

1. Complete Phase 1 parsing with persistence and tests
2. Build Phase 5 research memory from parsed documents
3. Implement Phase 4 evidence ranking over memory
4. Wire Phase 3 extractors to ranked retriever

See [tasks_v2.md](tasks_v2.md) for actionable task IDs.
