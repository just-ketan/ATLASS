# ATLASS v2 — Principal Architect Interview Deep Dive

Prepared answers for **FAANG/MAANG principal architect** interviews. Each section: **likely question**, **strong answer**, **follow-up probes**, **what they're testing**.

---

## 1. Elevator pitch (30 seconds)

**Q:** What is ATLASS v2 in one sentence?

**A:** ATLASS v2 is a research cognition engine that turns PDF papers into auditable structured objects—a typed knowledge graph, evidence-backed specification, architecture blueprint, and family-gated baseline code—through a fixed pipeline with span-bound extraction, not open-ended RAG summarization.

**They're testing:** Can you distinguish product from "chat with PDF."

---

## 2. Why not RAG?

**Q:** Everyone uses RAG. Why rebuild?

**A:** RAG optimizes for fluent answers from retrieved chunks. ATLASS optimizes for **field-isolated, provenance-backed artifacts** where each research attribute (dataset, method, metric) must come from the correct rhetorical section of the paper. v1's failure was **correlated errors**: one good-sounding paragraph polluted unrelated fields. That's a **system design** failure, not a prompt failure.

**Follow-ups:**

- *"Couldn't you use RAG with separate indexes per field?"* — You still need section semantics, span binding, and downstream graph/codegen contracts. That's the full v2 pipeline, not a thin RAG wrapper.
- *"What about GraphRAG?"* — We build an explicit research graph with typed edges (`uses_dataset`, `trained_with`). GraphRAG often clusters chunks; we need **field extractors + entity types** aligned to ML paper structure.

---

## 3. System boundaries & responsibilities

**Q:** Draw the architecture on a whiteboard.

**A:** Four layers:

1. **Ingress:** PDF → `ParsedDocument` (structure + IDs)
2. **Memory & retrieval:** `ResearchMemory` + `EvidenceRanker` (multi-signal)
3. **Cognition:** extractors → graph → spec → blueprint → baseline → reproduction
4. **Serving:** FastAPI + optional agent orchestration with traces

Persistence is artifact-oriented JSON per paper. Cross-cutting: benchmark harness, golden acceptance, QA with refusal.

**They're testing:** Layering, clear contracts between stages.

---

## 4. Data contract between stages

**Q:** What is the handoff between extraction and codegen?

**A:** `SemanticPaperGraph` with `GraphEntity` nodes carrying `provenance` back to `paragraph_id`/`chunk_id`. Blueprint modules require `evidence_entity_id` linking to a graph entity whose text contains a keyword match—not free-text spec alone. Baseline adds `FamilyDetector` output and refuses unsupported families.

**Probe:** *"Why not pass spec JSON directly to codegen?"* — Spec is flat; graph encodes **relations** (method uses dataset) for flows and sanity checks. Spec text can be right but decontextualized.

---

## 5. Retrieval design

**Q:** How do you rank evidence?

**A:** Composite score: semantic (dense max lexical), BM25, section weight from `SECTION_WEIGHTS`, entity keyword overlap, citation overlap. Optional cross-encoder rerank on top-k. Intents map to allowed sections via `INTENT_SECTIONS`—dataset queries shouldn't rank Introduction highly even if semantically similar.

**Probe:** *"How do you evaluate retrieval?"* — Golden queries in tests (dataset from EXPERIMENTS), `retrieval-debug` API, benchmark checks on section of first supporting span, golden acceptance on 10 paper profiles.

**Probe:** *"Why not only embeddings?"* — Dataset names and metrics are often **lexical** (GLUE, BLEU); BM25 catches exact mentions dense models spread across tokens.

---

## 6. Hallucination strategy

**Q:** How do you prevent hallucination?

**A:** Defense in depth:

1. **Span-bound evidence gate** — extractors return sentences from chunks only
2. **Section validators** in QA
3. **Score threshold** — refuse below 0.8 composite score
4. **Spec reuse detection** — duplicate field prefixes flagged
5. **Blueprint** — no module without entity support
6. **Baseline** — refuse unsupported families
7. **Explicit missing** — `missing: true` not silent defaults

**Probe:** *"Isn't extractive QA still wrong if retrieval is wrong?"* — Yes. We prefer **wrong refusal** (low confidence) over **wrong assertion**. Human reviews provenance links.

**Probe:** *"Where could LLM help without breaking guarantees?"* — Optional reranking with constrained decoding aligned to spans; section classification; never end-to-end field fill without gate.

---

## 7. Consistency & versioning

**Q:** How do you handle paper updates or re-ingest?

**A:** Artifacts keyed by `paper_id`. Blueprint keeps `blueprint_prev.json` for diff API. Spec has `version: 1`. Re-ingest regenerates chunk UUIDs—**not** content-addressed yet; improvement would be `ingest_run_id` and stable chunk hashes.

**Probe:** *"CAP theorem for this system?"* — Current file store favors **availability + partition tolerance** locally with **weak consistency** on concurrent writes. Production needs per-paper locking or object store versioning.

---

## 8. Scalability

**Q:** How does this scale to 10 million papers?

**A:** Today: single-node, per-paper artifacts. Scale path:

- **PDF store:** S3 + CDN
- **Parse workers:** async queue (Kafka/SQS), horizontal workers
- **Vector tier:** sharded FAISS or managed vector DB; per-paper or per-corpus indexes
- **Graph:** Neo4j or Postgres JSONB with entity index for cross-paper queries
- **API:** read replicas serving precomputed artifacts; ingest off critical path
- **Hot path:** QA loads memory for one paper—cache memory index in Redis

**They're testing:** You know current limits and haven't over-engineered early.

---

## 9. Latency & cost

**Q:** What's expensive in ingest?

**A:** Embedding all chunks + optional cross-encoder on 13 extractor calls. Cold model load dominates dev. Optimizations: batch embeddings, cache model in process, disable cross-encoder in CI, parse-once memory reuse, incremental re-extract single field on human correction.

**Cost model:** Mostly CPU/GPU inference—not LLM API tokens in current implementation (extractive path).

---

## 10. Agent architecture critique

**Q:** You have agents—is this an agentic AI system?

**A:** **Orchestrated micro-pipeline**, not autonomous agents. Fixed sequence, typed `AgentResult`, persisted traces. No LLM planner choosing tools. This is **workflow decomposition** for observability and team ownership boundaries—same pattern as data engineering DAGs.

**Probe:** *"When would you add LLM agents?"* — Interactive refinement ("expand method section only"), multi-paper synthesis, or hypothesis generation—**never** for initial evidence-bound ingest without human gate.

---

## 11. Testing philosophy

**Q:** How do you know it works?

**A:**

- **37 pytest** unit/integration/API tests
- **Synthetic LoRA** integration PDF (arXiv 2106.09685 pattern)
- **Benchmark smoke** — field distinctness, hallucination proxy, section checks
- **Golden acceptance** — 10 profiles, all checks must pass for release
- **Agent trace** — 8 steps succeed in orchestrator test

**Probe:** *"Why synthetic golden PDFs?"* — CI determinism. Real PDF layout tests supplement but aren't nightly gate.

---

## 12. Reproduction honesty

**Q:** Can ATLASS reproduce papers?

**A:** It classifies **reproduction feasibility** honestly:

- `smoke_test` / `partial` / `full` levels
- `metric_comparable` false unless dataset + supported baseline + no synthetic assumptions
- Smoke compile validates Python syntax—not training results
- Explicit warning: never compare smoke metrics to paper tables

**They're testing:** Scientific integrity vs demo hype.

---

## 13. Security

**Q:** Threat model?

**A:**

- **Malicious PDF** → parser attack surface; size limits, sandbox parse, virus scan at upload
- **Prompt injection in paper text** → extractive QA limits blast radius; spans still show injected text
- **Multi-tenant isolation** → not in v2; need authZ on `paper_id` prefix + encryption at rest for uploads
- **Model supply chain** → pin HuggingFace revisions in prod images

---

## 14. Comparison to competitors (conceptual)

**Q:** How is this different from Elicit, Semantic Scholar, or ChatPDF?

| Dimension | ChatPDF-style | ATLASS v2 |
|-----------|---------------|-----------|
| Primary output | Chat answer | Spec, graph, blueprint, baseline |
| Provenance | Optional cite | Required on every field |
| Codegen | Rare / generic | Family-gated with refusal |
| Missing info | Often filled | Explicit `missing` |
| Evaluation | User trust | Golden suite + benchmarks |

---

## 15. Org & team design

**Q:** How would you staff this?

**A:** Suggested ownership:

- **Parsing team** — PDF backends, section ID
- **Retrieval/ML** — ranker, embeddings, eval
- **Cognition** — extractors, graph, spec
- **Codegen** — blueprint, baseline templates
- **Platform** — API, jobs, observability
- **Quality** — golden papers, human eval loop

Interface contracts: `ExtractedField`, `GraphEntity`, artifact JSON schemas versioned.

---

## 16. Roadmap questions (be honest)

**Q:** What's not done?

**A:**

- GROBID/Docling/OCR in default parse chain (scaffolded)
- Redis cache (file cache today)
- Real multi-paper search
- LLM with constrained decoding (optional layer)
- Human-in-the-loop correction loop feeding re-extract
- Distributed job workers

**Shows:** You know shipped vs planned (see `v2tracker.md`).

---

## 17. Behavioral / leadership

**Q:** Tell me about a hard tradeoff you made.

**A (template using ATLASS):** We chose **extractive QA** over fluent summarization. Product wanted chatty answers; research users needed auditability. We shipped refusal + provenance, measured wrong-section rate down in golden tests, accepted lower NPS on "chat feel." Principal lesson: **optimize for the user's liability model**—wrong citation is worse than no answer.

---

## 18. Whiteboard exercises

### Exercise A — Add a new spec field `hardware`

1. Add `HardwareExtractor` with `INTENT_SECTIONS` → IMPLEMENTATION, EXPERIMENTS
2. Register in `EXTRACTORS` and `SPEC_FIELDS`
3. Map to `EntityType` in `FIELD_ENTITY_MAP`
4. Golden test: hardware mentions only from implementation section
5. Spec reuse validator applies automatically

### Exercise B — Cross-paper "what datasets appear in our corpus?"

Not in core v2. Design:

- Ingest emits events to Kafka
- Worker indexes `dataset` entities to Elasticsearch
- Query API separate from per-paper artifact read path

### Exercise C — Human corrects dataset field

1. UI stores human override with reviewer ID
2. Re-extract dataset only with boosted chunk IDs
3. Bump spec `version`
4. Re-run blueprint/baseline if dataset entity changed
5. Do not silently overwrite human override on re-ingest without merge policy

---

## 19. Metrics to cite in interviews

| Metric | Meaning |
|--------|---------|
| 37 tests passing | Regression gate |
| 10/10 golden papers | Acceptance gate |
| 13 independent extractors | Field isolation |
| 8 agent steps | Full orchestration coverage |
| 0.8 QA threshold | Conservative refusal |
| `fields_distinct` | dataset ≠ problem (anti-bleed) |

---

## 20. Questions to ask the interviewer

Shows principal-level curiosity:

1. How do you balance **user-facing fluency** vs **auditability** in your AI products?
2. Where does human review sit in your ML document pipelines—pre or post model?
3. How do you version structured extractions when models upgrade?
4. What's your standard for **comparability** in automated benchmark reproduction?

---

## Quick reference — file to concept

| Concept | Code anchor |
|---------|-------------|
| Pipeline order | `pipeline.py` |
| Evidence gate | `extraction/evidence_gate.py` |
| Ranker | `retrieval/evidence_ranker.py` |
| Graph contract | `graph/semantic_graph.py` |
| Spec reuse | `specification/spec_builder.py` |
| QA refusal | `qa/qa_pipeline.py` |
| Reproduction honesty | `reproduction/reproduction_engine.py` |
| Agents | `agents/orchestrator.py` |
| Golden gate | `evaluation/golden_acceptance.py` |

---

## Related documents

- [architecture.md](architecture.md)
- [data_flow.md](data_flow.md)
- [end_to_end_flow.md](end_to_end_flow.md)
- [design_decisions.md](design_decisions.md)
- [failure_modes.md](failure_modes.md)
