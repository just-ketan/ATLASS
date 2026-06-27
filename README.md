# ATLASS

**Autonomous Transformer Learning and Search Systems**

A research cognition engine that ingests scientific papers, builds hierarchical semantic memory, and produces grounded answers with full provenance — not a PDF chatbot.

## What ATLASS Does

- Ingests papers from arXiv or local PDFs
- Parses PDFs into structured JSON with semantic sections
- Builds chunk-level semantic memory with metadata indirection
- Performs hierarchical retrieval: sections → chunks → sentences
- Synthesizes grounded answers with hallucination guards
- Extracts structured knowledge (problem, method, dataset, limitations, future work)

## Architecture

See [architecture.md](architecture.md) for the full system design, retrieval pipeline, and phase roadmap.

```
PDF → Parsing → Chunking → Embedding → FAISS (chunk IDs)
  → Section Routing → Hybrid Retrieval → Sentence Ranking → LLM Synthesis
```

**Key design principle:** retrieval flows through `embedding → chunk_id → metadata lookup`, never `embedding → raw text`.

## Quick Start

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Ingest a paper (PDF → JSON)
python -m scripts.ingest_paper

# Interactive Q&A
python -m scripts.understand_paper

# Structured field extraction
python -m scripts.extract_paper

# Retrieval diagnostics (no LLM, inspect traces)
python -m scripts.debug_retrieval
```

Papers are cached in `data/processed_papers/`. Re-running skips download and re-parsing if the JSON exists.

## Example

```
Ask ATLASS: what is LoRA?

Answer:
LoRA (Low-Rank Adaptation) freezes the pre-trained model weights and injects
trainable rank decomposition matrices into each layer of the Transformer
architecture, greatly reducing the number of trainable parameters for
downstream tasks.
```

Unrelated queries are rejected:

```
Ask ATLASS: what powers does Pikachu have?

Answer:
This question does not seem related to the paper.
```

## Project Structure

```
atlasse/knowledge_engine/
├── paper_ingestion/       arXiv download, cache-first loading
├── paper_parser/          PDF extraction, section parsing
├── paper_embeddings/      chunking, embedding, FAISS, retrieval
└── paper_understanding/   Q&A engine, structured extraction, LLM

scripts/
├── ingest_paper.py        PDF → JSON pipeline
├── understand_paper.py    Interactive Q&A
├── extract_paper.py       Structured field extraction
├── query_paper.py         Alternative Q&A entry point
└── debug_retrieval.py     Retrieval trace diagnostics
```

## Retrieval Pipeline

1. **Query decomposition** — expand by intent (limitations, method, dataset, etc.)
2. **Section routing** — map query to relevant section categories
3. **Vector retrieval** — FAISS search returns chunk IDs
4. **Metadata lookup** — resolve chunk ID → text, section, boost
5. **Hybrid scoring** — cosine + BM25 + section boost + position boost
6. **Sentence reranking** — extract and rank individual sentences
7. **Confidence gate** — reject unrelated queries
8. **Synthesis** — LLM generation with retrieval fallback

## Tech Stack

| Component | Library |
|-----------|---------|
| PDF parsing | PyMuPDF |
| Paper download | arxiv |
| Embeddings | sentence-transformers (all-mpnet-base-v2) |
| Vector store | FAISS (IndexFlatL2) |
| Lexical ranking | rank-bm25 |
| Generation | HuggingFace Transformers (Flan-T5-large) |

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Paper ingestion | Done |
| 2 | Structured parsing | Done |
| 3 | Hybrid retrieval | Done |
| 4 | Hierarchical memory (ID indirection) | Done |
| 5 | Full hierarchical retrieval | In progress |
| 6 | Query decomposition | In progress |
| 7 | Retrieval observability | In progress |
| 8 | Multi-paper memory | Planned |
| 9 | Knowledge graph | Planned |
| 10 | Autonomous research agent | Planned |

## Design Principles

- **Retrieval > generation** — fix retrieval before tuning the LLM
- **Metadata is critical** — every answer traceable to chunk ID and section
- **Parser is good enough** — focus on orchestration, not parser perfection
- **No toy demos** — optimize for inspectability and provenance

## Known Limitations

- Single-paper scope (multi-paper memory not yet implemented)
- Flan-T5 synthesis quality varies; retrieval fallback compensates
- Vector index is rebuilt in-memory on each session (no persistence yet)
- Structured extraction quality depends on section routing maturity

## License

See [LICENSE](LICENSE).
