# ATLASS v2 — Research Cognition Refactor Plan

Source: [upgrade_v2.md](upgrade_v2.md)  
Implementation root: [backend/](backend/)  
Progress tracker: [tracker_v2.md](tracker_v2.md)  
Task breakdown: [tasks_v2.md](tasks_v2.md)

---

## What ATLASS Is (and Is Not)

| ATLASS is | ATLASS is not |
|-----------|---------------|
| A research cognition engine | A PDF chatbot |
| Structured research objects with provenance | A RAG system that summarizes chunks |
| Evidence-derived specifications and blueprints | Prompt-engineered copy-paste from introductions |
| Explicit uncertainty when information is missing | A system that hallucinates to appear complete |

### Why v2 Exists

The current implementation retrieves chunks and asks an LLM to synthesize answers. This architecture fundamentally fails:

- Identical paragraphs populate unrelated fields
- Datasets come from irrelevant text
- Objectives are extracted from introductions
- Blueprint modules are hallucinated
- Baselines become generic PyTorch templates

**Do not fix prompts. Redesign the reasoning engine.**

---

## Core Pipeline

Every downstream artifact must consume **structured research objects**, never raw paragraphs.

```text
Paper
  ↓ Structural parsing              (Phase 1)
  ↓ Evidence extraction             (Phase 3)
  ↓ Typed knowledge graph           (Phase 2)
  ↓ Research object graph           (Phase 2 + 5)
  ↓ Specification generation        (Phase 7)
  ↓ Blueprint generation            (Phase 8)
  ↓ Baseline synthesis              (Phase 9)
  ↓ Reproduction planning           (Phase 10)
```

Cross-cutting layers:

- **Phase 4** — Evidence ranking (feeds Phases 3, 6, 7)
- **Phase 5** — Research memory (feeds all retrieval stages)
- **Phase 6** — Question answering (user-facing evidence pipeline)
- **Phase 11** — Evaluation framework (quality gate for all phases)
- **Phase 12** — Agentic pipeline (orchestrates all phases)
- **Phase 13** — UI improvements (exposes structured outputs)
- **Phase 14** — Production quality (infra, tests, observability)
- **Phase 15** — Success criteria (acceptance benchmark)

---

## Design Principles (Non-Negotiable)

1. **Graph objects only** — downstream stages never consume raw paragraphs
2. **Dedicated extractors** — one focused module per research field, not one giant prompt
3. **Evidence ranking before LLM** — BM25 + dense + cross-encoder + section priors
4. **No field reuse** — each spec field has its own extractor and evidence set
5. **Explicit uncertainty** — report missing information; never invent details
6. **Provenance everywhere** — page, section, paragraph ID, confidence, citations on every artifact
7. **Correctness over completeness** — a partial honest answer beats a complete hallucination

---

## Phase 1 — Robust Document Parsing

**Goal:** Replace regex section detection with a parser that preserves full provenance.

**Status:** Scaffolded — PyMuPDF backend only

### Deliverables

- [ ] Multi-backend parser chain: GROBID → Docling → PyMuPDF → pdfplumber → OCR fallback
- [ ] Canonical section classification: Abstract, Introduction, Related Work, Method, Architecture, Experiments, Implementation, Datasets, Results, Discussion, Limitations, Future Work, Appendix, References
- [ ] Section tree with hierarchy and page ranges
- [ ] Paragraph IDs assigned to every text block
- [ ] Figure, table, and equation reference extraction
- [ ] `ParsedDocument` artifact persisted with full provenance

### Success Criteria

A parsed paper yields a navigable section tree where every paragraph is addressable by ID and page number. No text is silently discarded.

### Module

`backend/atlasse_v2/parsing/`

---

## Phase 2 — Semantic Paper Graph

**Goal:** Build a typed knowledge graph; only graph objects may be consumed downstream.

**Status:** Scaffolded — heuristic entity extraction

### Entity Types

Method, Dataset, Loss, Optimizer, Metric, Model, Module, Task, Input, Output, Contribution, Limitation, Future Work, Hyperparameter, Experiment, Baseline, Claim, Observation

### Edge Types

uses_dataset, evaluates_on, improves, trained_with, compares_against, depends_on, extends, proposes, reports

### Entity Fields

text, normalized_name, page, section, paragraph_id, confidence, citations

### Success Criteria

Every entity and edge traces to a paragraph ID. Downstream extractors query the graph, not raw text.

### Module

`backend/atlasse_v2/graph/`

---

## Phase 3 — Research Information Extraction

**Goal:** Dedicated extractors per field; no extractor answers outside retrieved evidence.

**Status:** Scaffolded — 13 extractors with stub logic

### Extractors

ProblemExtractor, ContributionExtractor, TaskExtractor, DatasetExtractor, MetricExtractor, MethodExtractor, ArchitectureExtractor, LossExtractor, TrainingExtractor, EvaluationExtractor, BaselineExtractor, LimitationExtractor, FutureWorkExtractor

### Extractor Contract

Each returns: `value`, `supporting_spans`, `confidence`, `citations`, `missing`

### Success Criteria

DatasetExtractor retrieves only from Datasets/Experiments/Appendix sections. ProblemExtractor retrieves only from Abstract/Introduction. No field receives text from an unrelated section.

### Module

`backend/atlasse_v2/extraction/`

---

## Phase 4 — Evidence Ranking

**Goal:** Replace naive retrieval with a multi-signal reranker.

**Status:** Not started

### Components

- BM25 keyword retrieval
- Dense embedding retrieval
- CrossEncoder reranking
- Section prior weighting
- Entity overlap scoring
- Recency-within-paper scoring

### Score Formula

```text
score = semantic + keyword + section_weight + entity_overlap + citation_overlap
```

Only top reranked evidence reaches the LLM.

### Success Criteria

For a dataset query, top-5 evidence spans come from Experiments/Datasets sections with measurable precision improvement over v1.

### Module

`backend/atlasse_v2/retrieval/`

---

## Phase 5 — Research Memory

**Goal:** Replace coarse chunks with fine-grained, permanently indexed research memory.

**Status:** Not started

### Chunk Types

paragraphs, semantic blocks, tables, captions, equations, algorithms

### Chunk Metadata

chunk_id, page, section, paragraph, entities, embedding, keywords, citations

### Success Criteria

Every chunk is independently retrievable and addressable. Memory persists across sessions.

### Module

`backend/atlasse_v2/memory/`

---

## Phase 6 — Question Answering

**Goal:** Replace summarize-and-hope with an evidence-validated QA pipeline.

**Status:** Not started

### Pipeline

```text
Question → Intent classifier → Required entity types → Retriever → Reranker
  → Evidence validator → Answer generator → Citation verifier
```

If evidence is missing: respond **"The paper does not specify."** Never hallucinate.

### Success Criteria

QA on LoRA paper returns cited answers from method/experiment sections, not introduction boilerplate.

### Module

`backend/atlasse_v2/qa/`

---

## Phase 7 — System Specification

**Goal:** Each spec field has a dedicated extractor; no field reuses another field's answer.

**Status:** Not started

### Fields

Problem, Contribution, Task, Inputs, Outputs, Architecture, Loss, Optimizer, Datasets, Metrics, Training, Evaluation, Results, Limitations, Future Work

### Field Schema

value, citations, confidence, missing, source_chunks

### Success Criteria

`system_spec.json` for LoRA has distinct, evidence-backed values for every field. Dataset field does not contain introduction text.

### Module

`backend/atlasse_v2/specification/`

---

## Phase 8 — Blueprint Generator

**Goal:** Derive blueprint from extracted architecture graph, not GPT imagination.

**Status:** Not started

### Pipeline

```text
Architecture graph → Module decomposition → Data flow → Training flow
  → Evaluation flow → Inference flow → Project tree → Interfaces → Dependencies
```

Each generated file maps back to evidence (e.g., TransformerEncoder → `src/model/encoder.py`).

Never generate modules unsupported by evidence.

### Success Criteria

Blueprint module tree matches architecture entities in the knowledge graph. Every file has an evidence link.

### Module

`backend/atlasse_v2/blueprint/`

---

## Phase 9 — Baseline Generator

**Goal:** Infer model family and fill family-specific templates from the research graph.

**Status:** Not started

### Model Families

CNN, Transformer, Diffusion, GAN, VAE, GNN, RNN, LSTM, MLP, RL, Siamese, UNet, Seq2Seq, ViT, MoE, Encoder-Decoder, Retrieval, LoRA, PEFT, NeRF, etc.

Missing values become explicit assumptions, not silent defaults.

### Success Criteria

LoRA paper produces a LoRA-family baseline, not a generic MLP. Unsupported families are refused with explanation.

### Module

`backend/atlasse_v2/baseline/`

---

## Phase 10 — Reproduction Engine

**Goal:** Classify reproduction feasibility; never compare synthetic metrics against paper metrics.

**Status:** Not started

### Reproduction Levels

Smoke Test, Partial Reproduction, Paper Reproduction

### Classification Labels

Executable, Architecture matched, Dataset unavailable, Hyperparameters missing, Training infeasible, Metric comparable, Overall confidence

### Success Criteria

Synthetic smoke runs are permanently marked non-comparable. Real-data runs produce honest comparability verdicts.

### Module

`backend/atlasse_v2/reproduction/`

---

## Phase 11 — Evaluation Framework

**Goal:** Benchmark suite against 100 arXiv papers with regression testing every commit.

**Status:** Not started

### Metrics

Dataset extraction accuracy, Metric extraction accuracy, Contribution extraction, Architecture extraction, Hallucination rate, Evidence precision, Citation precision, Blueprint correctness, Baseline correctness, QA exact match

### Success Criteria

Benchmark harness runs in CI. Scores tracked over time. Regressions block merges.

### Module

`backend/atlasse_v2/evaluation/`

---

## Phase 12 — Agentic Pipeline

**Goal:** Replace linear pipeline with agents communicating through structured objects.

**Status:** Not started

### Agents

Document Agent, Retrieval Agent, Research Agent, Evidence Agent, Specification Agent, Blueprint Agent, Baseline Agent, Evaluation Agent

Agents pass typed objects (ParsedDocument, GraphEntity, ExtractedField, etc.), never free-form text.

### Success Criteria

Full paper processing runs through agent orchestration with structured handoffs logged and inspectable.

### Module

`backend/atlasse_v2/agents/`

---

## Phase 13 — UI Improvements

**Goal:** Expose richer structured outputs through the backend API.

**Status:** Not started (backend contracts only in v2 scope)

### New UI Surfaces

Evidence viewer, Graph explorer, Architecture DAG, Section tree, Citation browser, Entity browser, Assumption tracker, Missing information tracker, Blueprint diff, Specification diff, Evidence inspector, Confidence heatmap

### Success Criteria

Frontend can render section tree, entity graph, and per-field confidence without filesystem inspection.

### Module

`backend/atlasse_v2/api/` + frontend integration

---

## Phase 14 — Production Quality

**Goal:** Make v2 deployable and testable at production standards.

**Status:** Not started

### Deliverables

Redis caching, Background jobs, Streaming responses, Incremental indexing, Persistent vector DB, Structured logging, OpenTelemetry, Unit tests, Integration tests, Golden paper tests, Snapshot tests, Benchmark harness

### Success Criteria

`pytest backend/tests/` passes. Golden paper tests cover LoRA, ResNet, Transformer. CI runs benchmark regression.

### Module

`backend/atlasse_v2/infra/` + `backend/tests/`

---

## Phase 15 — Success Criteria

ATLASS v2 is complete when it correctly handles papers such as:

LoRA, ResNet, Transformer, BERT, CLIP, SAM, ViT, YOLO, DINO, Stable Diffusion

**Without** repeating introduction paragraphs.

### Acceptance Checklist

- [ ] Every generated artifact traces back to explicit evidence
- [ ] Generated baseline represents the paper's actual architecture when sufficient evidence exists
- [ ] Missing information is explicitly reported as uncertainty
- [ ] No field in system_spec reuses another field's text
- [ ] Dataset/metric fields come from experiment sections, not introductions
- [ ] Blueprint modules map to architecture graph entities
- [ ] QA returns "The paper does not specify." when evidence is absent
- [ ] Benchmark suite scores meet minimum thresholds on golden papers

---

## Implementation Sequence

Recommended build order (dependencies flow downward):

| Order | Phase | Depends On | Rationale |
|-------|-------|------------|-----------|
| 1 | Phase 1 — Parsing | — | Foundation for all provenance |
| 2 | Phase 5 — Memory | Phase 1 | Fine-grained chunks from parsed doc |
| 3 | Phase 4 — Retrieval | Phase 5 | Rank over memory chunks |
| 4 | Phase 2 — Graph | Phase 1, 3 | Typed entities from parsed + extracted |
| 5 | Phase 3 — Extraction | Phase 4, 5 | Extractors need ranked evidence |
| 6 | Phase 6 — QA | Phase 3, 4 | QA uses extractors + reranker |
| 7 | Phase 7 — Specification | Phase 3 | Spec = all extractors composed |
| 8 | Phase 8 — Blueprint | Phase 2, 7 | Blueprint from architecture graph + spec |
| 9 | Phase 9 — Baseline | Phase 7, 8 | Baseline from spec + blueprint |
| 10 | Phase 10 — Reproduction | Phase 9 | Reproduction of generated baseline |
| 11 | Phase 11 — Evaluation | Phases 1–10 | Measure everything |
| 12 | Phase 12 — Agents | Phases 1–10 | Orchestrate completed modules |
| 13 | Phase 13 — UI | Phases 1–12 | Expose to frontend |
| 14 | Phase 14 — Production | All | Harden for deployment |
| 15 | Phase 15 — Acceptance | All | Golden paper validation |

---

## Relationship to v1

| v1 (`atlasse/`) | v2 (`backend/atlasse_v2/`) |
|-----------------|---------------------------|
| Regex section detection | Multi-backend structural parsing |
| One LLM prompt per field | Dedicated extractors with evidence gates |
| Heuristic knowledge graph | Typed semantic graph with 18 entity types |
| Coarse chunk retrieval | Multi-signal reranking over fine memory |
| Generic PyTorch MLP baseline | Model-family template filling |
| Synthetic smoke metrics | Reproduction classification with honest comparability |

v1 remains operational during v2 development. v2 backend runs on port 8001 alongside v1 on port 8000.

---

## What We Will Not Do in v2

- Patch v1 prompts to mask architectural failures
- Allow extractors to answer outside retrieved evidence
- Generate blueprint modules without graph entity support
- Compare synthetic smoke metrics against paper-reported results
- Treat prompt engineering as a substitute for structured reasoning
- Ship v2 without benchmark regression tests on golden papers
