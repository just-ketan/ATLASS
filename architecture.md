# ATLASS Architecture

## Vision

ATLASS (Autonomous Transformer Learning and Search Systems) is a research cognition engine. It ingests scientific papers, builds hierarchical semantic memory with full provenance, retrieves grounded evidence, and supports autonomous literature synthesis — not a PDF chatbot.

## System Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Phase 10: ResearchAgent — explore, compare, gaps, experiments│
├─────────────────────────────────────────────────────────────┤
│  Phase 9:  KnowledgeGraph — entities, citations, relations   │
├─────────────────────────────────────────────────────────────┤
│  Phase 8:  CorpusMemory — multi-paper cross-retrieval        │
├─────────────────────────────────────────────────────────────┤
│  Phase 6:  QueryOrchestrator — evidence merge + provenance     │
├─────────────────────────────────────────────────────────────┤
│  Phase 5/7: Section routing, hybrid retrieval, traces, eval  │
├─────────────────────────────────────────────────────────────┤
│  Phase 1–4: Ingestion → Parsing → Chunking → FAISS (IDs)    │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
PDF → PaperProcessor → JSON
  → PaperMemory.build(paper_id) → chunk_metadata + FAISS index (persisted)
  → QueryOrchestrator.retrieve(query)
      → expand_query → section routing → filtered vector search
      → BM25 hybrid scoring → sentence ranking → confidence gate
      → EvidenceMerger → provenance citations
  → PaperUnderstandingEngine.ask_with_provenance → LLM fallback
  → ResearchAgent.run_research_loop → compare, gaps, experiments
```

## Core Principle: ID Indirection

```
embedding search → chunk_id → chunk_metadata[id] → { paper_id, section, text }
```

## Module Map

| Module | Path | Phase |
|--------|------|-------|
| `section_router` | `retrieval/section_router.py` | 5 |
| `PaperMemory` | `paper_embeddings/memory_builder.py` | 4–5 |
| `VectorStore` | `paper_embeddings/vector_store.py` | 4 (persist) |
| `TraceStore` | `observability/trace_store.py` | 7 |
| `EvalHarness` | `observability/eval_harness.py` | 7 |
| `QueryOrchestrator` | `orchestration/query_orchestrator.py` | 6 |
| `EvidenceMerger` | `orchestration/evidence_merger.py` | 6 |
| `CorpusMemory` | `corpus/corpus_memory.py` | 8 |
| `KnowledgeGraph` | `graph/knowledge_graph.py` | 9 |
| `ResearchAgent` | `agent/research_agent.py` | 10 |
| `cli` | `atlasse/cli.py` | prod |

## Section Routing (Phase 5)

Intent detection maps queries to section categories:

| Intent | Target Sections |
|--------|----------------|
| definition | abstract, introduction |
| problem | abstract, introduction, method |
| method | method, abstract |
| dataset | experiment, appendix |
| limitations | conclusion, discussion |
| future_work | conclusion |

Retrieval applies section-filtered vector search first, with unfiltered fallback. Appendix sections are included for dataset queries.

## Observability (Phase 7)

- `PaperMemory.last_trace` — per-query retrieval diagnostics
- `TraceStore` — persisted traces at `data/traces/{paper_id}/{trace_id}.json`
- `EvalHarness` — golden query regression (`python -m atlasse.cli eval`)
- `tests/` — unit tests for routing, persistence, graph, evidence merge

## Orchestration (Phase 6)

`QueryOrchestrator` decomposes queries, retrieves per sub-query, merges evidence with deduplication, and returns:

```python
{
    "answer": "...",
    "citations": "[1] (2106.09685 § abstract, chunk 0)",
    "provenance": [{ chunk_id, paper_id, section, score }],
    "confidence": 0.85
}
```

## Multi-Paper Memory (Phase 8)

`CorpusMemory` indexes multiple papers. `query(text)` searches all papers and merges results by score. Supports paper-scoped and cross-paper retrieval.

## Knowledge Graph (Phase 9)

`KnowledgeGraph` extracts entities, citations, and section/chunk relations from chunk metadata. Graphs persisted at `data/knowledge_graphs/{paper_id}/`.

## Research Agent (Phase 10)

`ResearchAgent` autonomous loop:

1. `understand_paper()` — structured field extraction with provenance
2. `compare_papers()` — cross-paper aspect comparison
3. `identify_gaps()` — open research gaps from limitations + future work
4. `suggest_experiments()` — concrete experiment proposals
5. `explore()` — topic search across corpus
6. `run_research_loop()` — full pipeline

## CLI

```bash
python -m atlasse.cli ingest 2106.09685
python -m atlasse.cli ask 2106.09685 -q "what is LoRA"
python -m atlasse.cli extract 2106.09685
python -m atlasse.cli eval 2106.09685
python -m atlasse.cli corpus -q "parameter efficient fine-tuning"
python -m atlasse.cli agent --mode loop --paper-id 2106.09685
python -m atlasse.cli agent --mode gaps --paper-id 2106.09685
```

## Phase Status

| Phase | Status |
|-------|--------|
| 1–4 | Complete |
| 5 | Complete |
| 6 | Complete |
| 7 | Complete |
| 8 | Complete |
| 9 | Complete (heuristic graph) |
| 10 | Complete (agent loop) |

## Design Principles

1. Retrieval > generation
2. Metadata indirection always
3. Parser is good enough
4. Provenance on every answer
5. Observability before scaling
