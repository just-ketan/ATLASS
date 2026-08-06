# ATLASS Student MVP Track

ATLASS (Autonomous Transformer Learning and Search Systems) ingests a new scientific paper, builds a grounded understanding of its proposed system, and turns that understanding into a runnable, evidence-linked baseline on real paper-aligned data. It is not primarily a paper library, generic PDF chatbot, or synthetic-demo generator.

## Core Intention

The user should be able to take a newly imported, compatible research paper through this path in the frontend:

```text
Paper PDF / arXiv
  → grounded evidence and paper understanding
  → structured proposed-system specification
  → reviewed implementation plan and paper-specific project scaffold
  → real-data baseline experiment
  → frontend-visible, evidence-linked report of observed versus paper-reported results
```

Every generated design or code decision must link back to paper sections/chunks. When information is absent or ambiguous, ATLASS must mark it as an assumption rather than inventing a detail. A synthetic fixture may be retained solely for UI development; it cannot satisfy this product objective, validate the end-to-end workflow, or produce a baseline result.

## Resume-Ready Definition of Done

The MVP is complete only when a reviewer can import a new compatible real paper through the frontend and:

1. import it and see processing complete;
2. ask grounded questions with citations;
3. inspect the extracted problem, method, inputs, outputs, training setup, datasets, metrics, and claimed results;
4. approve an implementation blueprint that identifies paper evidence versus assumptions;
5. approve a paper-specific PyTorch baseline scaffold whose data, model, training configuration, and metrics are derived from the reviewed specification (with every substitution labeled);
6. run that implementation on the paper's public dataset or documented public-data subset, not synthetic data;
7. view observed implementation metrics alongside paper-reported metrics, a comparability verdict, configuration, logs, and evidence links in the frontend; and
8. repeat the same flow from a clean workspace without seeded paper/spec/blueprint/project artifacts.

## Focused Build Track

### Track 1 — Paper understanding and evidence

Status: substantially complete; real-paper frontend verification pending

- Ingest arXiv/local PDFs and parse sections.
- Build hybrid semantic retrieval with section routing and provenance citations.
- Extract concepts, entities, and relationships.
- Expose paper Q&A and retrieval-debug output through the backend.

Remaining: consolidate the existing extraction outputs into one canonical, reviewable paper-understanding artifact and verify it for a newly ingested real paper in the frontend.

### Track 2 — Proposed-system specification

Status: implemented — real-paper verification pending

Create a versioned `system_spec.json` for each paper. It should contain:

- problem statement and contribution;
- task definition, inputs, outputs, and assumptions;
- model components and data flow;
- objective/loss, optimization, and training loop;
- dataset, preprocessing, metrics, baselines, and reported results;
- implementation-critical hyperparameters;
- unresolved details, explicitly labeled assumptions, and provenance for every field.

Success criterion: a student can read the artifact and understand exactly what must be built before any code is generated.

Implemented:

- Versioned `system_spec.json` artifact with implementation-focused fields, retrieval confidence, citations, and source-chunk provenance.
- Create, retrieve, and review/correct API contracts.
- Explicit missing fields and manual assumptions; no unsupported implementation detail is silently inferred.

### Track 3 — Blueprint and implementation planning

Status: implemented — real-paper verification pending

Turn the approved system specification into a human-reviewable blueprint:

- module tree and responsibilities;
- tensor/data contracts between modules;
- training and evaluation steps;
- dependency list and configuration schema;
- mapping from blueprint elements to paper evidence;
- implementation choices that are assumptions or baseline substitutions.

Success criterion: the blueprint can be approved or edited before ATLASS writes source code.

Implemented:

- Versioned, evidence-linked implementation blueprint with module tree, data contracts, training plan, dependencies, and configuration schema.
- Explicit readiness gate for missing paper details and baseline-scope assumptions.
- Create, retrieve, review/edit, and approve API contracts; Track 4 code generation remains blocked until blueprint approval.

### Track 4 — Runnable model baseline

Status: incomplete for the product objective

Generate a constrained, runnable PyTorch project rather than claiming to fully reproduce arbitrary papers:

- `src/model.py`, `src/data.py`, `src/train.py`, and `src/evaluate.py`;
- a typed/configurable experiment file;
- a paper-aligned public-data execution path (full dataset or documented subset);
- a README with setup and run commands;
- source comments and a manifest linking code modules to `system_spec.json` evidence.

Scope boundary: support a narrow initial family of papers, such as supervised neural-network architectures with public datasets. Complex distributed systems, unavailable data, custom hardware, and proprietary training recipes should produce an implementation plan—not fabricated runnable code.

Current implementation:

- Approval-gated generator for a safe, runnable PyTorch supervised-learning baseline.
- Generates `model.py`, `data.py`, `train.py`, `evaluate.py`, configuration, README, and an evidence/assumption manifest.
- Uses deterministic synthetic data for the smoke path and refuses unsupported model families rather than producing misleading code.

Required to meet the objective:

- Support one explicitly selected compatible paper family end to end.
- Generate or configure a real dataset adapter, paper-aligned preprocessing, model structure, objective, optimizer, and metrics from the approved blueprint.
- Derive configuration values from paper evidence or show them as reviewed substitutions; do not emit fixed MLP dimensions, dataset sizes, or hyperparameters as if they came from the paper.
- Add an automated integration test that proves the generated project trains and evaluates on real public data.

### Track 5 — Experiment and reproduction report

Status: incomplete for the product objective

- Run the generated real-data baseline locally.
- Capture environment, configuration, metrics, logs, and generated artifacts.
- Compare observed metrics with the paper's reported metrics when comparable.
- Produce a report separating reproduced evidence, implementation assumptions, and known gaps.

Success criterion: the project demonstrates an honest working baseline, not an unverified claim of paper reproduction.

Current implementation:

- Explicit smoke-run endpoint for generated baseline projects, with bounded execution and captured stdout/stderr.
- Persisted reproduction report containing observed metrics, the paper's reported-result evidence, assumptions, and a comparability verdict.
- Synthetic smoke metrics are explicitly marked not comparable to paper metrics.

Required to meet the objective:

- Capture the exact dataset/subset, split, preprocessing, seed, environment, generated source revision, configuration, logs, and artifacts used by the real run.
- Calculate paper-aligned metrics from the implementation and compare them with the extracted paper-reported results only when the setup is comparable.
- Mark any mismatch in data, preprocessing, architecture, training budget, or metric definition as a concrete limitation in the report.

### Track 6 — Showcase interface and delivery

Status: implemented shell; real-paper end-to-end alignment pending

- Build one focused UI: Library → Paper understanding → System spec → Blueprint → Run/report.
- Provide an import-to-report flow for one compatible real paper, with its status, evidence, review gates, generated project, live run state, and report visible in the same frontend workflow.
- Add architecture diagram, screenshots, and reproducible setup instructions to the README.
- Deploy the frontend/API or provide a one-command local demo.

Implemented:

- Focused React/Vite interface with the five MVP stages: import, understand, system specification, blueprint, and run/report.
- Local demo-workspace login and API-backed controls for the complete paper-to-baseline workflow.
- Responsive, dependency-light visual shell ready for local demo or deployment.
- Clearly labeled synthetic demo-paper fixture that preloads the approved spec, blueprint, and generated baseline for an immediate local walkthrough.

Remaining:

- Replace the seeded-fixture demonstration as the primary path with one newly imported compatible real paper and a documented real-data baseline result.
- Ensure all API statuses/artifact locations/run results are rendered by the frontend without manual filesystem inspection.
- Capture the complete end-to-end walkthrough as screenshots/video.
- Deploy the API/frontend or provide a one-command local launcher.

## Immediate Implementation Sequence

### Track 7 — Real-paper acceptance and handoff

Status: next module — real-paper end-to-end acceptance

1. Select one compatible paper with an accessible public dataset and a tractable single-machine baseline.
2. Import it as a new paper through the frontend, wait for processing, and review the evidence-backed system specification.
3. Correct/approve missing details, generate and approve the blueprint, then generate the baseline project.
4. Run training and evaluation on real paper-aligned data from the frontend; retain all artifacts and compare observed metrics to the paper only when comparable.
5. Add a regression test for the full API workflow and capture the same complete frontend walkthrough.

Acceptance evidence: the repository contains a run report for the real paper with a non-synthetic dataset provenance, generated-project manifest, observed metrics, paper-reported metrics/evidence, and an explicit comparability verdict. The result must be reachable in the frontend from the imported paper record.

## What We Will Not Build Before the Demo

- Multi-user production authentication, billing, or managed cloud infrastructure.
- A general agent that can faithfully implement every paper.
- Synthetic metrics or seeded demo fixtures as evidence that the core paper-to-baseline objective is complete.
- OCR/DOI ingestion hardening, live paper feeds, GitHub repo analysis, or broad social/recommendation features.
- Paid-model dependence for the main demo path.

Those are valid future extensions, but they do not strengthen the central demonstration: paper → understanding → runnable baseline.

## Current Foundation Completed

- Paper ingestion from arXiv/local PDFs
- PDF parsing and section extraction
- Chunking, embeddings, FAISS vector store, BM25 retrieval
- Section-aware retrieval with intent detection and query expansion
- Provenance-aware orchestration and citations
- Trace storage and golden-query eval harness
- Multi-paper corpus memory
- Lightweight knowledge graph
- Research agent for paper understanding, comparison, gaps, experiments
- Unified CLI: `python -m atlasse.cli`

## Supporting Product Architecture (Future Extension)

Frontend: Lovable / React / Tailwind on Vercel

Backend: FastAPI ATLASS API

Core services:

- Authentication
- Paper Management
- Knowledge Engine
- LLM Engine
- Agent Engine
- Search Engine
- Memory Engine
- Citation Engine
- Project Engine

Storage:

- Postgres for product data
- Qdrant/vector database for semantic retrieval
- Redis for jobs, cache, and realtime status
- Object storage for PDFs and generated artifacts

Model providers:

- Hugging Face models
- OpenAI
- Anthropic
- Local models

## Deferred Production / Paid Systems Backlog

These are important for a real hosted product, but they are not blockers for the local portfolio MVP.

- Managed Postgres for durable multi-user product data
- Qdrant or managed vector database for hosted semantic search
- Redis-backed worker queue, cache, and realtime processing status
- S3/R2/GCS object storage for PDFs and generated artifacts
- Hosted auth provider and production OAuth app verification
- Paid LLM providers for high-quality synthesis and agent workflows
- Cloud OCR service for scanned/low-quality PDFs
- Monitoring, tracing, token accounting, and hosted eval dashboards
- Vercel/Render/Fly/Railway deployment hardening

## Deferred Product-Platform Roadmap

### Phase 1 - User System

Goal: every research artifact belongs to a user-owned workspace.

Status: Foundation slice complete

Deliverables:

- User model
- OAuth identity entry point
- Dashboard summary
- Research library ownership
- User-owned papers, projects, notes, conversations, memory, citations
- Backend service boundary ready for Postgres
- Initial FastAPI routes

Implemented files:

- `atlasse/platform/models.py`
- `atlasse/platform/store.py`
- `atlasse/platform/service.py`
- `atlasse/platform/api.py`
- `tests/test_platform.py`
- `tests/test_platform_api.py`

### Phase 2 - Paper Management

Goal: production ingestion pipeline for PDFs, arXiv, DOI, and drag/drop uploads.

Status: Backend foundation slice complete

Deliverables:

- Upload endpoint - implemented
- arXiv import endpoint - implemented through generic paper import API
- DOI import endpoint - implemented as a record/import contract; resolver still pending
- Processing status state machine - implemented
- Object storage abstraction - implemented with local filesystem MVP
- OCR hook - pending
- Parser/chunker/embedding job pipeline - implemented as background job scaffold
- Ready/failed status UI contract - implemented with processing events

Implemented files:

- `atlasse/platform/models.py`
- `atlasse/platform/store.py`
- `atlasse/platform/service.py`
- `atlasse/platform/api.py`
- `atlasse/platform/storage.py`
- `atlasse/platform/jobs.py`
- `tests/test_platform.py`
- `tests/test_platform_api.py`
- `tests/test_storage.py`

Next steps:

- Add DOI metadata/PDF resolver
- Add OCR fallback for scanned PDFs
- Replace local job execution with Redis-backed workers
- Persist processing artifacts and events in Postgres/object storage

### Phase 3 - Knowledge Engine

Goal: extend paper understanding beyond chunks.

Status: Local MVP slice complete

Deliverables:

- Concept extraction - implemented with deterministic local extractor
- Entity extraction - implemented with deterministic local extractor
- Section/chunk/entity persistence - implemented as local `knowledge.json` artifact
- Knowledge graph persistence - existing local graph persistence
- Semantic memory abstraction - implemented as workspace memory promotion
- Library-wide knowledge search/filter API - implemented

Implemented files:

- `atlasse/knowledge_engine/paper_understanding/concept_extractor.py`
- `atlasse/knowledge_engine/paper_understanding/__init__.py`
- `atlasse/platform/service.py`
- `atlasse/platform/api.py`
- `atlasse/platform/jobs.py`
- `tests/test_concept_extractor.py`
- `tests/test_platform.py`
- `tests/test_platform_api.py`

Implemented refinement:

- Rich relation extraction between concepts, methods, datasets, and citations, with provenance-backed search and memory promotion

### Phase 4 - Retrieval Engine

Goal: production-grade evidence retrieval.

Status: MVP backend in progress

Deliverables:

- Intent detection
- Query expansion
- Section routing
- Chunk retrieval
- Sentence retrieval
- Citation retrieval
- Evidence ranking
- Debuggable retrieval traces

Implemented MVP slice:

- Paper-scoped question endpoint backed by hybrid retrieval, evidence synthesis, provenance citations, and optional retrieval-debug output

### Phase 5 - Multi-Paper Reasoning

Goal: compare and synthesize across papers.

Status: MVP backend in progress

Deliverables:

- Paper set retrieval
- Aspect-specific retrieval
- Comparison engine
- Multi-paper citations
- Literature review primitives

Implemented MVP slice:

- User-scoped, extractive multi-paper comparison endpoint with aspect retrieval and per-paper provenance

### Phase 6 - Research Projects

Goal: project workspaces that bind papers, notes, code, datasets, and conversations.

Deliverables:

- Project CRUD
- Attach papers, notes, datasets, repos, conversations
- Project memory
- Project timeline seed

### Phase 7 - Conversation Memory

Goal: conversations become durable research memory.

Deliverables:

- Conversation persistence
- Generated notes
- Follow-up question tracking
- Personal insight extraction
- Memory promotion workflow

### Phase 8 - Knowledge Graph

Goal: concept-first graph of papers and relationships.

Deliverables:

- Concept nodes
- Relationship extraction
- Graph query API
- Graph visualization API contract

### Phase 9 - Agents

Goal: specialized research agents.

Deliverables:

- Research Agent
- Literature Review Agent
- Citation Agent
- Experiment Agent
- Writing Agent
- Reviewer Agent

### Phase 10 - Live Research Feed

Goal: personalized daily research updates.

Deliverables:

- Topic subscriptions
- New paper ingestion
- Ranking/recommendations
- Daily summaries

### Phase 11 - Code Understanding

Goal: attach GitHub repositories to research projects.

Deliverables:

- GitHub import
- Repository tree parser
- Code embeddings
- Dependency graph
- Repo Q&A

### Phase 12 - Research Timeline

Goal: chronological memory of how a project evolves.

Deliverables:

- Timeline events
- Paper/idea/experiment/note/draft/publication milestones
- Project history API

### Phase 13 - API

Goal: API-first platform.

Initial endpoints:

- `POST /papers/upload`
- `POST /papers/arxiv`
- `GET /papers`
- `POST /chat`
- `POST /compare`
- `POST /summarize`
- `POST /extract`
- `POST /review`
- `POST /projects`
- `GET /graph`

### Phase 14 - Observability

Goal: make research quality measurable.

Deliverables:

- Retrieval debug
- Embedding debug
- Latency metrics
- Token usage
- Hallucination rate
- Confidence score

### Phase 15 - Deployment

Goal: deployable ATLASS stack.

Deliverables:

- Vercel frontend
- Railway/Render/Fly FastAPI backend
- Supabase or Cloudflare R2 storage
- Postgres
- Qdrant
- Upstash Redis
