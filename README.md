# ATLASS

**Autonomous Transformer Learning and Search Systems**

A research cognition engine that turns a paper into grounded understanding, a reviewable system specification, an implementation blueprint, and a constrained runnable baseline.

See [architecture.md](architecture.md) for full system design.

## Capabilities

- Paper ingestion from arXiv with local caching
- Hierarchical retrieval: sections → chunks → sentences
- Section-aware routing (future work, limitations, datasets)
- Hybrid scoring: cosine + BM25 + section boost
- Provenance citations on every answer
- Persistent vector indices and retrieval traces
- Multi-paper corpus search
- Knowledge graph (entities, citations, relations)
- Autonomous research agent (understand, compare, gaps, experiments)
- Paper-to-baseline workflow: evidence → system specification → blueprint → PyTorch smoke baseline

## Quick Start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Ingest
python -m atlasse.cli ingest 2106.09685

# Ask with provenance
python -m atlasse.cli ask 2106.09685 -q "what is LoRA"

# Structured extraction
python -m atlasse.cli extract 2106.09685

# Retrieval evaluation
python -m atlasse.cli eval 2106.09685

# Cross-paper search
python -m atlasse.cli corpus -q "low rank adaptation"

# Research agent
python -m atlasse.cli agent --mode gaps --paper-id 2106.09685
python -m atlasse.cli agent --mode loop --paper-id 2106.09685

# Unit tests
python -m unittest discover tests
```

## Student MVP Demo

The resume-focused workflow is intentionally narrow: import a paper, inspect evidence, approve the extracted proposed-system specification and implementation blueprint, then generate and run a synthetic-data PyTorch smoke baseline. It never presents the smoke result as a paper reproduction.

```bash
# Terminal 1: API
uvicorn atlasse.platform.api:app --reload

# Terminal 2: React demo UI
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The local demo workspace offers five stages: Import, Understand, System spec, Blueprint, and Run & report.

Use **Load synthetic demo** for an immediate, clearly labeled end-to-end fixture. It exists to demonstrate the workflow and is not presented as a published paper or reproduction result. See [tracker.md](tracker.md) for delivery status and remaining portfolio work.

The initial code generator supports the `pytorch_supervised_model` family. Unsupported papers still receive a system specification and implementation blueprint, but code generation is intentionally refused rather than guessed.

## Project Structure

```
atlasse/
├── cli.py                          Unified CLI
└── knowledge_engine/
    ├── paper_ingestion/            arXiv download, cache-first loading
    ├── paper_parser/               PDF → structured JSON
    ├── paper_embeddings/           chunking, FAISS, PaperMemory
    ├── paper_understanding/        Q&A, structured extraction
    ├── retrieval/                  section routing, intent detection
    ├── orchestration/              evidence merge, provenance
    ├── observability/              traces, eval harness
    ├── corpus/                     multi-paper CorpusMemory
    ├── graph/                      KnowledgeGraph
    └── agent/                      ResearchAgent

scripts/                            Legacy script entry points
tests/                              Unit and integration tests
data/
├── processed_papers/               Parsed JSON cache
├── memory_indices/                 Persisted FAISS indices
├── traces/                         Retrieval trace logs
├── knowledge_graphs/               Paper knowledge graphs
├── system_specs/                   Reviewable proposed-system artifacts
├── implementation_blueprints/      Approval-gated build plans
├── generated_projects/             Generated PyTorch baselines
└── reproduction_reports/            Smoke-run reports
```

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Paper ingestion | Done |
| 2 | Structured parsing | Done |
| 3 | Hybrid retrieval | Done |
| 4 | Hierarchical memory (ID indirection) | Done |
| 5 | Section-aware routing | Done |
| 6 | Query orchestration + provenance | Done |
| 7 | Observability (traces, eval, tests) | Done |
| 8 | Multi-paper memory | Done |
| 9 | Knowledge graph | Done |
| 10 | Autonomous research agent | Done |

## Tech Stack

Python · PyMuPDF · arxiv · sentence-transformers · FAISS · rank-bm25 · HuggingFace Transformers (Flan-T5)

## License

See [LICENSE](LICENSE).
