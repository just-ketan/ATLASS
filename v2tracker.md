# ATLASS v2 Sprint Tracker

Last updated: 2026-08-06  
Plan: [plan_v2.md](plan_v2.md)  
Tasks: [tasks_v2.md](tasks_v2.md)  
Legacy tracker: [tracker_v2.md](tracker_v2.md)  
Implementation: [backend/](backend/)

---

## How to Use

Each sprint has a **goal**, **entry criteria**, **exit criteria**, and a **task checklist**.  
Mark items `[x]` when done. Current sprint is highlighted at the top.

**Quota note:** Development sessions should pause when ~30% of monthly quota is consumed. Track usage in Cursor settings; this file does not auto-monitor quota.

---

## Sprint Overview

| Sprint | Name | Phases | Status | Exit criteria |
|--------|------|--------|--------|---------------|
| **S1** | Foundation | 1, 5, 4, 2, 3, 7–9 (scaffold) | **Complete** | Parse → memory → rank → extract → graph → spec → blueprint → baseline pipeline runs on synthetic LoRA PDF |
| **S2** | Extraction & Retrieval Hardening | 3, 4, 5 | **Complete** | All exit criteria met |
| **S3** | QA & Specification Quality | 6, 7 | **Complete** | QA validator, citation verifier, heatmap/missing APIs |
| **S4** | Blueprint & Baseline Codegen | 8, 9 | **Complete** | LoRA project files, manifest, blueprint diff API |
| **S5** | Reproduction & Evaluation | 10, 11 | **Complete** | Reproduction reports, benchmark harness, score tracking |
| **S6** | Agents, API & Production | 12, 13, 14 | **Active** | Agent orchestration; rich API; production hardening |
| **S7** | Golden Paper Acceptance | 15 | Planned | 10 golden papers pass minimum benchmark thresholds |

---

## Sprint 1 — Foundation ✅ Complete

**Goal:** End-to-end pipeline from PDF to structured artifacts with provenance.

**Phases:** 1, 5, 4, 2, 3, 7, 8, 9 (initial)

### Entry criteria
- [x] `upgrade_v2.md` and `plan_v2.md` documented
- [x] `backend/atlasse_v2/` package scaffolded

### Tasks
- [x] Core models and type enums
- [x] DocumentParser + PyMuPDF + pdfplumber fallback
- [x] Section tree + paragraph IDs + DocumentStore persistence
- [x] ResearchMemory (paragraph + caption/table/equation chunks)
- [x] EvidenceRanker (BM25 + dense + section priors + trace)
- [x] 13 dedicated extractors wired to ranker
- [x] SemanticPaperGraph from extractors + edge inference
- [x] SpecBuilder in pipeline
- [x] BlueprintGenerator + BaselineGenerator in pipeline
- [x] FastAPI v2 API (ingest, status, ask, spec, graph, retrieval-debug)
- [x] CLI (`atlasse_v2 ingest|ask|spec|status`)
- [x] Integration test: synthetic LoRA PDF (2106.09685)
- [x] 19 unit/integration tests passing

### Exit criteria
- [x] `pytest backend/tests/` passes
- [x] `pipeline.ingest()` produces parsed, memory, graph, spec, blueprint, baseline artifacts

---

## Sprint 2 — Extraction & Retrieval Hardening 🔄 Active

**Goal:** Evidence strictly bound to spans; retrieval quality measurable and persistent.

**Phases:** 3, 4, 5

### Entry criteria
- [x] Sprint 1 exit criteria met

### Tasks
- [x] Span-bound evidence gate (no synthesis outside retrieved text)
- [x] Cross-encoder reranker (optional fallback when model unavailable)
- [x] FAISS vector index for research memory
- [x] Algorithm chunk detection in memory builder
- [x] Entity tagging on chunks from graph keywords
- [x] Tests: evidence gate, vector retrieval, blueprint/baseline API

### Exit criteria
- [x] Extractors return only sentences present in evidence spans
- [x] Memory index persists embeddings + FAISS alongside chunks.json
- [x] Retrieval debug shows cross-encoder component when enabled
- [x] Blueprint/baseline retrievable via API without filesystem access

### Blockers
- None

---

## Sprint 3 — QA & Specification Quality

**Goal:** User-facing QA never hallucinates; specification is review-ready.

**Phases:** 6, 7

### Entry criteria
- [x] Sprint 2 exit criteria met

### Tasks
- [x] QA evidence validator (reject wrong-section spans)
- [x] Citation verifier on every QA answer
- [x] Intent → entity-type routing table complete
- [ ] Spec diff API (version compare)
- [x] Missing-information tracker data model + API
- [x] Confidence heatmap per spec field + API
- [x] Golden QA queries for LoRA paper (test_qa.py)
- [x] CI test: dataset field ≠ problem field text

### Exit criteria
- [x] QA returns "The paper does not specify." when score < threshold
- [x] All spec fields independently evidence-backed in LoRA integration test

---

## Sprint 4 — Blueprint & Baseline Codegen

**Goal:** Generated blueprint and baseline code reflect paper architecture, not templates.

**Phases:** 8, 9

### Entry criteria
- [x] Sprint 3 exit criteria met

### Tasks
- [x] Module decomposition from architecture graph entities
- [x] Data / training / evaluation / inference flow derivation
- [x] Refuse blueprint modules without graph entity
- [x] LoRA template: `lora.py`, `base_model.py` with spec-filled hyperparams
- [x] Transformer template family
- [x] Explicit assumption manifest on every generated file
- [x] Blueprint diff API
- [x] Integration test: LoRA → LoRA-family baseline (not MLP)

### Exit criteria
- [x] Generated baseline project directory with runnable stubs for supported families
- [x] Every file in manifest links to graph entity or spec field

---

## Sprint 5 — Reproduction & Evaluation

**Goal:** Honest reproduction classification; regression benchmarks in CI.

**Phases:** 10, 11

### Entry criteria
- [x] Sprint 4 exit criteria met

### Tasks
- [x] Reproduction level classifier (smoke / partial / full)
- [x] Never compare synthetic vs paper metrics
- [x] Benchmark harness scaffold (10 golden papers)
- [x] Metrics: extraction accuracy, hallucination rate, citation precision
- [x] Score tracking JSON over commits
- [x] CI job: `pytest backend/tests/` + benchmark smoke

### Exit criteria
- [x] Reproduction report with comparability verdict and limitations
- [x] Benchmark runs locally in < 5 minutes (smoke subset)

---

## Sprint 6 — Agents, API & Production

**Goal:** Agent orchestration with structured handoffs; production-ready infra.

**Phases:** 12, 13, 14

### Entry criteria
- [x] Sprint 5 exit criteria met

### Tasks
- [ ] Document, Retrieval, Research, Evidence agents (structured objects only)
- [ ] Specification, Blueprint, Baseline, Evaluation agents
- [ ] Agent trace logging
- [ ] Evidence viewer, graph explorer, section tree APIs
- [ ] Entity browser, assumption tracker APIs
- [ ] Redis caching layer (optional)
- [ ] Background job queue for ingest
- [ ] Structured logging + OpenTelemetry hooks
- [ ] Snapshot tests for API responses

### Exit criteria
- [ ] Full ingest via AgentOrchestrator with inspectable trace
- [ ] Frontend can render section tree + graph without raw filesystem reads

---

## Sprint 7 — Golden Paper Acceptance

**Goal:** v2 success criteria from `upgrade_v2.md` Phase 15.

**Phases:** 15

### Entry criteria
- [ ] Sprint 6 exit criteria met

### Golden papers
- [ ] LoRA
- [ ] ResNet
- [ ] Transformer ("Attention Is All You Need")
- [ ] BERT
- [ ] CLIP
- [ ] SAM
- [ ] ViT
- [ ] YOLO
- [ ] DINO
- [ ] Stable Diffusion

### Exit criteria
- [ ] No introduction paragraph reuse across unrelated spec fields
- [ ] Blueprint modules trace to evidence
- [ ] Baseline family matches paper when evidence sufficient
- [ ] Missing fields explicitly marked; no hallucination

---

## Current Sprint Focus

**Sprint 6** — agent orchestration, rich APIs, and production hardening.

```bash
# Run tests
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/ -q

# Ingest sample
PYTHONPATH=backend .venv/bin/python -m atlasse_v2.cli ingest /path/to/paper.pdf

# Start API
PYTHONPATH=backend .venv/bin/python -m uvicorn atlasse_v2.api.app:app --port 8001
```

---

## Sprint Burndown (task counts)

| Sprint | Total tasks | Done | Remaining |
|--------|-------------|------|-----------|
| S1 | 24 | 24 | 0 |
| S2 | 8 | 8 | 0 |
| S3 | 8 | 8 | 0 |
| S4 | 8 | 8 | 0 |
| S5 | 6 | 6 | 0 |
| S6 | 10 | 0 | 10 |
| S7 | 11 | 0 | 11 |

---

## Scope Guardrails (all sprints)

- Never allow extractors to answer outside retrieved evidence
- Never generate blueprint modules without graph entity support
- Never compare synthetic smoke metrics to paper-reported results
- Never reuse one spec field's text for another field
- Prioritize correctness over completeness
- Report uncertainty explicitly — never hallucinate
