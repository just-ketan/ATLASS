# ATLASS Product Implementation Plan

ATLASS is an AI-native research operating system: GitHub Copilot meets Perplexity meets NotebookLM meets Semantic Scholar, specialized for scientific research.

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

## Target Architecture

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

## Phase Roadmap

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

Deliverables:

- Upload endpoint
- arXiv import endpoint
- DOI import endpoint
- Processing status state machine
- Object storage abstraction
- OCR hook
- Parser/chunker/embedding job pipeline
- Ready/failed status UI contract

### Phase 3 - Knowledge Engine

Goal: extend paper understanding beyond chunks.

Deliverables:

- Concept extraction
- Entity extraction
- Section/chunk/entity persistence
- Knowledge graph persistence
- Semantic memory abstraction

### Phase 4 - Retrieval Engine

Goal: production-grade evidence retrieval.

Deliverables:

- Intent detection
- Query expansion
- Section routing
- Chunk retrieval
- Sentence retrieval
- Citation retrieval
- Evidence ranking
- Debuggable retrieval traces

### Phase 5 - Multi-Paper Reasoning

Goal: compare and synthesize across papers.

Deliverables:

- Paper set retrieval
- Aspect-specific retrieval
- Comparison engine
- Multi-paper citations
- Literature review primitives

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
