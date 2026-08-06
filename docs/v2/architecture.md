# ATLASS v2 — System Architecture

## Executive summary

ATLASS v2 is a **research cognition engine**: it transforms PDF papers into **typed, provenance-backed research objects** (graph entities, specifications, blueprints, baseline code skeletons, reproduction reports) through a **fixed pipeline** with **evidence gates**, not through open-ended LLM summarization.

It is deliberately **not**:

- A PDF chatbot
- A generic RAG stack (retrieve → prompt → answer)
- A prompt-tuning exercise on v1

The architectural bet: **correctness and auditability beat apparent completeness**. When evidence is insufficient, the system says *"The paper does not specify"* or marks fields `missing` rather than hallucinating.

---

## Problem statement (why v1 failed)

| Failure mode | Root cause | v2 response |
|--------------|------------|-------------|
| Same intro paragraph in `dataset` and `problem` | One retrieval pool + one LLM call for all fields | Dedicated extractors + section priors + reuse detection |
| Blueprint modules with no paper basis | LLM imagines architecture | Blueprint from **graph entities** + keyword→file mapping with `evidence_entity_id` |
| Generic PyTorch baseline for every paper | Template without family detection | `FamilyDetector` + supported-family gate; refuse unsupported families |
| QA answers from wrong sections | Weak retrieval | Intent → section routing + evidence validator + score threshold |
| "Reproduced" metrics vs paper | Smoke run compared to paper numbers | Explicit `metric_comparable: false` + synthetic warning |

---

## Architectural principles (non-negotiable)

1. **Structured objects downstream** — Phases 7–10 consume graph/spec objects, not raw paragraphs.
2. **Evidence before generation** — Retrieval ranks spans; extractors are span-bound; QA returns chunk text or refuses.
3. **One extractor per research field** — No monolithic "extract everything" prompt.
4. **Provenance on every artifact** — `page`, `section`, `paragraph_id`, `chunk_id`, `confidence`, `citations`.
5. **Explicit uncertainty** — `missing`, `assumptions`, low-confidence heatmaps.
6. **Correctness over completeness** — Partial honest spec beats full hallucinated spec.
7. **Never compare synthetic smoke to paper metrics** — Reproduction engine enforces comparability verdict.

---

## Layered architecture

```text
┌─────────────────────────────────────────────────────────────────────────┐
│  Presentation / API (Phase 13)                                          │
│  FastAPI :8001 — ingest, ask, spec, graph, blueprint, baseline,         │
│  evidence viewer, entity browser, architecture DAG, agent traces        │
├─────────────────────────────────────────────────────────────────────────┤
│  Agent orchestration (Phase 12)                                         │
│  AgentOrchestrator — 8 specialized agents, typed AgentResult handoffs     │
├─────────────────────────────────────────────────────────────────────────┤
│  Cognition pipeline (Phases 1–10)                                       │
│  Parse → Memory → Rank → Extract → Graph → Spec → Blueprint → Baseline  │
│  → Reproduction                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│  Cross-cutting services                                                 │
│  EvidenceRanker │ QAPipeline │ BenchmarkSuite │ GoldenAcceptance        │
├─────────────────────────────────────────────────────────────────────────┤
│  Infrastructure (Phase 14)                                              │
│  FileCache │ JobQueue │ structured logging │ OpenTelemetry hook         │
├─────────────────────────────────────────────────────────────────────────┤
│  Persistence (file-backed artifacts per paper_id)                       │
│  parsed/ memory_indices/ knowledge_graphs/ specifications/ blueprints/  │
│  baselines/ reproduction_reports/ agent_traces/ jobs/ cache/            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Module map (`backend/atlasse_v2/`)

| Package | Phase | Responsibility |
|---------|-------|----------------|
| `core/` | — | `ParsedDocument`, `ResearchChunk`, `GraphEntity`, `ExtractedField`, enums |
| `parsing/` | 1 | Multi-backend PDF parse, section tree, paragraph IDs |
| `memory/` | 5 | Research memory builder, FAISS `vector_index`, chunk patterns |
| `retrieval/` | 4 | BM25 + dense + cross-encoder + section/entity/citation signals |
| `extraction/` | 3 | 13 extractors + `evidence_gate` (span-bound sentences) |
| `graph/` | 2 | `SemanticPaperGraph` — entities, typed edges, persistence |
| `specification/` | 7 | `SpecBuilder` — versioned `system_spec.json`, reuse validation |
| `blueprint/` | 8 | Module decomposition, flow derivation, diff |
| `baseline/` | 9 | Family detection, template render, project manifest |
| `reproduction/` | 10 | Level classifier, smoke compile, comparability verdict |
| `qa/` | 6 | Intent → retrieve → validate → answer → cite verify |
| `agents/` | 12 | Orchestrator + specialized agents + trace store |
| `evaluation/` | 11, 15 | Benchmark harness, score store, golden acceptance |
| `api/` | 13 | FastAPI app + view builders |
| `infra/` | 14 | Cache, jobs, logging, OTel hook |
| `pipeline.py` | — | `PaperPipeline.ingest()` — synchronous cognition chain |

---

## Cognition pipeline (logical order)

Actual execution order in `PaperPipeline.ingest()`:

```text
PDF
  → DocumentParser (Phase 1)
  → DocumentStore.save → ParsedDocument
  → ResearchMemory.build_from_document (Phase 5)
  → EvidenceRanker (Phase 4) — built on memory
  → EXTRACTORS × 13 (Phase 3) — each uses ranker + evidence_gate
  → SemanticPaperGraph.build_from_extracted (Phase 2)
  → memory.tag_from_graph + re-rank
  → SpecBuilder (Phase 7)
  → BlueprintGenerator (Phase 8) — graph + spec
  → BaselineGenerator (Phase 9) — graph + spec
  → ReproductionEngine (Phase 10)
```

**Important:** Extraction runs **before** the graph is fully populated from extractors, then the graph is rebuilt from extractor outputs. Blueprint/baseline consume the **graph + spec**, not free text.

---

## Agent architecture (Phase 12)

`AgentOrchestrator` mirrors the pipeline but emits **inspectable traces**:

| Agent | Input type | Output type | Side effect |
|-------|------------|-------------|-------------|
| DocumentAgent | PDF path | `ParsedDocument` | `parsed/` |
| RetrievalAgent | `ParsedDocument` | `ResearchMemory` | `memory_indices/` |
| ResearchAgent | ranker | `SemanticPaperGraph` | `knowledge_graphs/` |
| EvidenceAgent | paper_id | tagged memory stats | memory update |
| SpecificationAgent | ranker | `SystemSpec` | `specifications/` |
| BlueprintAgent | graph + spec | `Blueprint` | `blueprints/` |
| BaselineAgent | graph + spec | `Baseline` | `baselines/` |
| EvaluationAgent | baseline + spec | `ReproductionReport` | `reproduction_reports/` |

**Design choice:** Agents return `AgentResult` (structured payload keys, duration, success) — not natural-language plans. This is **orchestration with typed handoffs**, not an autonomous LLM agent swarm.

Traces persist to `{data_dir}/agent_traces/{paper_id}.json`.

---

## Retrieval architecture (Phase 4)

`EvidenceRanker` is a **multi-signal scorer**, not a single embedding search:

```text
score = semantic + keyword(BM25) + section_weight + entity_overlap + citation_overlap
        → optional cross-encoder rerank on top-k
```

**Section priors:** `INTENT_SECTIONS` maps field intents (e.g. `dataset`) to allowed `SectionType` lists. Dataset evidence should not rank Introduction highly.

**Intent routing table** (excerpt):

| Intent | Preferred sections |
|--------|-------------------|
| `dataset` | DATASETS, EXPERIMENTS, APPENDIX |
| `method` | METHOD, ARCHITECTURE |
| `problem` | ABSTRACT, INTRODUCTION |
| `metric` | EXPERIMENTS, RESULTS |

Every retrieval can emit a **trace** (`retrieve_with_trace`) for debugging and API `/retrieval-debug`.

---

## Graph as integration contract (Phase 2)

`SemanticPaperGraph` is the **typed integration boundary** between extraction and codegen:

- **Entities:** Method, Dataset, Loss, Metric, Model, Module, Task, …
- **Edges:** `uses_dataset`, `evaluates_on`, `trained_with`, `compares_against`, …
- Built from `ExtractedField` outputs via `FIELD_ENTITY_MAP`
- Edge inference via `EDGE_RULES` (e.g. method→dataset → `USES_DATASET`)

Downstream **BlueprintGenerator** only adds modules when keywords match **entity text** in the graph — if no entity supports a module, it is not invented.

---

## API surface (Phase 13)

Base path: `/v2/`

| Endpoint | Purpose |
|----------|---------|
| `POST /papers/ingest` | Sync ingest via orchestrator + trace |
| `POST /papers/ingest-async` | Background job |
| `GET /jobs/{job_id}` | Job status |
| `GET /papers/{id}/status` | Artifact presence |
| `GET /papers/{id}/sections` | Section tree for UI |
| `GET /papers/{id}/graph` | Entity/edge JSON |
| `GET /papers/{id}/spec` | Full system spec |
| `GET /papers/{id}/blueprint` | Blueprint JSON |
| `GET /papers/{id}/baseline` | Baseline metadata |
| `GET /papers/{id}/reproduction` | Reproduction report |
| `POST /papers/{id}/ask` | Grounded QA |
| `GET /papers/{id}/evidence` | Chunk browser |
| `GET /papers/{id}/entities` | Entity browser |
| `GET /papers/{id}/architecture-dag` | Blueprint DAG view |
| `GET /papers/{id}/assumptions` | Spec + baseline assumptions |
| `GET /papers/{id}/agent-trace` | Orchestration trace |
| `GET /papers/{id}/retrieval-debug?q=` | Ranker trace |
| `GET /papers/{id}/confidence-heatmap` | Per-field confidence |
| `GET /papers/{id}/missing-fields` | Explicit gaps |
| `POST /benchmark/smoke` | CI regression |

v2 runs on **port 8001** alongside v1 on 8000.

---

## Persistence model

Per `paper_id`, artifacts are **immutable JSON files** under `data_dir` (default `data/v2/`):

```text
data/v2/
  parsed/{paper_id}/document.json
  memory_indices/{paper_id}/chunks.json + embeddings + faiss index
  knowledge_graphs/{paper_id}/graph.json
  specifications/{paper_id}/system_spec.json
  blueprints/{paper_id}/blueprint.json (+ blueprint_prev.json)
  baselines/{paper_id}/baseline.json + project/
  reproduction_reports/{paper_id}/reproduction_report.json
  agent_traces/{paper_id}/trace.json
  jobs/{job_id}.json
  cache/{key}.json
  benchmark/scores.json
```

**Interview angle:** This is **artifact-oriented** storage (good for audit, diff, replay) vs a single document DB. Tradeoff: no cross-paper query without indexing layer.

---

## Deployment topology (current vs target)

**Current (implemented):**

- Single-process FastAPI + in-process `JobQueue` (thread + file status)
- File-backed cache (Redis optional in design, not required)
- Local FAISS + sentence-transformers for dense retrieval
- Cross-encoder with graceful fallback when model/network unavailable

**Target (principal architect will ask):**

| Concern | Current | Typical scale path |
|---------|---------|-------------------|
| Ingest throughput | Sync + light async jobs | Queue worker pool (SQS/Kafka), object store for PDFs |
| Memory index | Per-paper FAISS on disk | Sharded vector DB (Pinecone, pgvector) per corpus |
| Graph | JSON file | Graph DB (Neo4j) or property graph in Postgres |
| Multi-tenant | Single `data_dir` | Tenant prefix + authZ on `paper_id` |
| Observability | JSON logs + OTel hook | Full traces, retrieval dashboards |

---

## Security & compliance (interview topics)

- **Data residency:** PDFs are user uploads; artifacts contain extracted text — treat as sensitive research data.
- **Provenance as audit trail:** Every field links to spans — supports human review for high-stakes use (grant review, legal).
- **No training on user data** (by architecture): extraction is retrieval-bound, not fine-tune loop.
- **Supply chain:** Parser backends (PyMuPDF, optional GROBID/Docling) — document parsing is a common malware vector; validate uploads, size limits, sandbox parse.
- **Prompt injection in papers:** Adversarial PDF text ("ignore previous instructions") — span-bound extraction limits blast radius; QA returns retrieved text, not LLM synthesis (reduces but does not eliminate risk if LLM added later).

---

## Testing & quality gates

| Layer | Mechanism |
|-------|-----------|
| Unit | Per-module tests (parsing, gate, graph, retrieval) |
| Integration | Synthetic LoRA PDF (`2106.09685`) full pipeline |
| API | FastAPI TestClient snapshot-style checks |
| Regression | `BenchmarkSuite.run_smoke_regression` — field distinctness, hallucination rate |
| Acceptance | 10 golden papers — `golden_acceptance.py` |
| CI target | `pytest backend/tests/` — 37 tests |

---

## Relationship to v1

ATLASS v1 (port 8000) remains separate. v2 is a **parallel package** (`atlasse_v2`) with no shared pipeline code — intentional strangler-fig pattern: prove v2 cognition path before cutover.

---

## Further reading

- [data_flow.md](data_flow.md) — artifact schemas and transformations
- [end_to_end_flow.md](end_to_end_flow.md) — step-by-step lifecycles
- [design_decisions.md](design_decisions.md) — tradeoffs and alternatives
- [interview_deep_dive.md](interview_deep_dive.md) — FAANG/MAANG principal questions
- [failure_modes.md](failure_modes.md) — risks and mitigations
