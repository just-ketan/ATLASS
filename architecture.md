# ATLASS Architecture

## Vision

ATLASS (Autonomous Transformer Learning and Search Systems) is a research cognition engine — not a PDF chatbot. It ingests scientific papers, builds hierarchical semantic memory with full provenance, retrieves grounded evidence through multi-stage ranking, and synthesizes answers backed by chunk and section metadata.

## System Layers

```
┌─────────────────────────────────────────────────────────────┐
│              Autonomous Research Agent                       │  Phase 10
├─────────────────────────────────────────────────────────────┤
│         Knowledge Graph / Multi-Paper Memory                 │  Phase 8–9
├─────────────────────────────────────────────────────────────┤
│   Query Decomposition → Hierarchical Retrieval → Synthesis   │  Phase 5–7
├─────────────────────────────────────────────────────────────┤
│   Ingestion → Parsing → Chunking → Embedding → FAISS       │  Phase 1–4
└─────────────────────────────────────────────────────────────┘
```

## End-to-End Data Flow

```
PDF
  → PaperProcessor          OCR cleanup, regex + heuristic section extraction
  → JSON                    { full_text, sections[{ title, level, text }] }
  → PaperMemory.build()
      → TextChunker         500-word chunks, 100-word overlap
      → chunk_metadata      { id, section, text, level, position_boost }
      → Embedder            all-mpnet-base-v2, L2-normalized
      → VectorStore         FAISS IndexFlatL2, stores integer chunk IDs
  → PaperUnderstandingEngine.ask(query)
      → decompose_query()   intent-based sub-query expansion
      → section routing     query categories ↔ section categories
      → vector search       returns chunk IDs (never raw text)
      → metadata lookup     chunk_metadata[id] → text, section, boost
      → BM25 reranking      hybrid score with section + position boost
      → sentence extraction split top chunks, filter noise
      → sentence reranking  BM25 + parent chunk score
      → confidence scoring  gates unrelated queries
      → LLM synthesis       Flan-T5 with retrieval fallback
```

## Core Design Principle: ID Indirection

Retrieval never operates on raw text from the vector store.

```
embedding search → chunk_id → chunk_metadata[id] → { section, text, level }
```

The vector store API:

```python
vector_store.add(embeddings, ids)          # ids are integer chunk IDs
results = vector_store.search(query, k)    # returns [(chunk_id, distance), ...]
```

## Module Map

| Module | Path | Responsibility |
|--------|------|----------------|
| `PaperLoader` | `paper_ingestion/paper_loader.py` | Cache-first paper loading (processed JSON → raw PDF → arXiv) |
| `ArxivDownloader` | `paper_ingestion/arxiv_downloader.py` | Download papers from arXiv |
| `PaperProcessor` | `paper_parser/paper_processor.py` | PDF → structured JSON with sections |
| `TextChunker` | `paper_embeddings/chunker.py` | Word-based chunking with overlap |
| `Embedder` | `paper_embeddings/embedder.py` | Sentence-transformer encoding |
| `VectorStore` | `paper_embeddings/vector_store.py` | FAISS index over chunk IDs |
| `PaperMemory` | `paper_embeddings/memory_builder.py` | Memory build + hierarchical retrieval |
| `PaperUnderstandingEngine` | `paper_understanding/paper_understanding_engine.py` | Q&A orchestration + hallucination guard |
| `StructuredExtractor` | `paper_understanding/structured_extractor.py` | Multi-field paper understanding |
| `LLMEngine` | `paper_understanding/llm_engine.py` | Grounded answer generation |

## Retrieval Pipeline

### 1. Query Decomposition

`PaperMemory.decompose_query()` expands a single user query into intent-specific sub-queries:

- **limitations** → "drawbacks and disadvantages", "weaknesses or negative results"
- **method** → "proposed method architecture", "design and implementation details"
- **dataset** → "datasets and benchmarks used in experiments"
- **problem** → "problem statement and motivation"
- **future work** → "conclusion and future research directions"

Each sub-query is retrieved independently; evidence is merged by chunk ID.

### 2. Section Routing

Sections are categorized (abstract, introduction, method, experiment, conclusion, related_work, appendix). Query intent maps to target categories. Chunks whose section category overlaps the query intent receive a section boost in hybrid scoring.

### 3. Hybrid Chunk Scoring

```
score = 0.35 × norm_cosine + 0.35 × norm_bm25 + 0.15 × section_boost + 0.15 × position_boost
```

- **cosine_sim** — derived from L2 distance on normalized embeddings
- **bm25_score** — lexical relevance per sub-query
- **section_boost** — 1.0 when section category matches query intent
- **position_boost** — early chunks in a section (abstract/intro) weighted higher

### 4. Sentence-Level Reranking

Top 3 chunks are split into sentences. Noise and table fragments are filtered. Sentences are reranked:

```
sentence_score = 0.5 × norm_sentence_bm25 + 0.5 × parent_chunk_score
```

Definition sentences receive a bonus for definition-type queries.

### 5. Confidence Gate

```
confidence = clamp((top_cosine - 0.2) / 0.6, 0, 1)
```

Queries with confidence < 0.05 are rejected as unrelated to the paper.

### 6. Synthesis with Retrieval Fallback

`PaperUnderstandingEngine.ask()` uses a tiered strategy:

1. High-confidence definition match → return retrieved sentence directly
2. High retrieval score (≥ 0.85) → return retrieved sentences directly
3. Otherwise → Flan-T5 generation with simplified prompt
4. If LLM output is empty or says "not found" → fall back to top retrieved sentences

## Observability

Every query populates `PaperMemory.last_trace`:

```python
{
    "original_query": "...",
    "decomposed_queries": [...],
    "target_categories": [...],
    "top_candidates": [{ chunk_id, section, cosine_sim, bm25_score, score, text_preview }],
    "ranked_sentences": [{ text, score, is_def, section }],
    "confidence_score": 0.0–1.0
}
```

Use `scripts/debug_retrieval.py` to inspect retrieval traces without LLM synthesis overhead on trace fields.

## Structured Extraction

`StructuredExtractor` queries five canonical fields:

| Field | Query Intent |
|-------|-------------|
| `problem` | What problem does the paper address? |
| `method` | What method is proposed? |
| `dataset` | What datasets/benchmarks are used? |
| `limitations` | What limitations are mentioned? |
| `future_work` | What future work is suggested? |

Each field runs through the full retrieval + synthesis pipeline independently.

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Paper ingestion (arXiv + cache) | Complete |
| 2 | Structured paper parsing | Complete |
| 3 | Hybrid retrieval (semantic + BM25) | Complete |
| 4 | Hierarchical memory (ID indirection) | Complete |
| 5 | Full hierarchical retrieval | Partial |
| 6 | Query decomposition | Partial |
| 7 | Retrieval observability | Partial |
| 8 | Multi-paper memory | Planned |
| 9 | Knowledge graph memory | Planned |
| 10 | Autonomous research agent | Planned |

## Planned Extensions

### Multi-Paper Memory (Phase 8)

Add `paper_id` to chunk metadata. Namespace vector indices per paper or use a unified index with paper-scoped filtering.

### Knowledge Graph (Phase 9)

Extract entities, concepts, and citations from chunks. Build a semantic graph for cross-paper retrieval and relation-aware reasoning.

### Autonomous Agent (Phase 10)

Literature synthesis loop: read → understand → compare → identify gaps → suggest experiments → iterate.

## Design Principles

1. **Retrieval > generation** — most failures are retrieval failures, not LLM failures
2. **Metadata is critical** — all retrieval flows through `embedding → id → metadata → hierarchy → synthesis`
3. **Parser is good enough** — further parser work has diminishing returns; focus on orchestration
4. **Provenance always** — every answer traceable to chunk ID and section
5. **No toy demos** — optimize for inspectability, scalability, and grounded reasoning

## Non-Goals

- Parser perfection beyond current quality
- Ungrounded generation without retrieval evidence
- Single-shot embedding → LLM pipelines without ranking
