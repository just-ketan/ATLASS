# ATLASS v2 — Design Decisions & Tradeoffs

ADR-style record of **why** the system is shaped this way. Principal architects probe alternatives — know what you rejected and why.

---

## ADR-001: Research cognition engine, not RAG chatbot

**Context:** v1 retrieved chunks and asked an LLM to fill all fields from the same context.

**Decision:** Fixed multi-stage pipeline producing typed artifacts with provenance.

**Alternatives considered:**

| Alternative | Why rejected |
|-------------|--------------|
| Better prompts on v1 | Does not fix shared-context field bleed |
| Single "super-prompt" extraction | One failure mode corrupts all fields |
| Agent with free-form tool use | Hard to audit; prone to tool hallucination |
| Fine-tune domain model on papers | Expensive; poor cold-start; opaque errors |

**Consequences:** Higher engineering complexity, longer ingest latency, much better auditability.

---

## ADR-002: Dedicated extractors per field

**Context:** Research papers have distinct rhetorical zones (intro problem vs experiments dataset).

**Decision:** 13 extractors in `extraction/registry.py`, each with own retrieval query and section prior.

**Tradeoff:** More code paths vs one generic extractor. Maintenance cost is linear in fields but **failure isolation** is worth it.

**Interview line:** *"We traded prompt simplicity for fault isolation — a bad dataset extraction doesn't poison the method field."*

---

## ADR-003: Span-bound evidence gate (no synthesis)

**Context:** LLMs invent plausible sentences not in the paper.

**Decision:** `evidence_gate.extract_span_bound_sentences` returns verbatim sentences from retrieved chunks only.

**Alternatives:**

- LLM extract with citation requirement — still hallucinates citations
- Structured output JSON from LLM — format valid, content wrong

**Current limitation:** Cannot paraphrase — answers may be verbose. **Future:** Constrained generation with token-level alignment check against spans.

---

## ADR-004: Multi-signal retrieval vs pure dense RAG

**Decision:** `score = semantic + BM25 + section + entity + citation` (+ optional cross-encoder).

**Why BM25 still matters:** Exact dataset names (GLUE, ImageNet) and metrics (BLEU, mIoU) need lexical matching.

**Why section priors:** Introduction text is semantically similar to many queries but **wrong epistemically**.

**Calibration:** Scores are heuristic sums — not probabilistic. QA uses conservative threshold; retrieval-debug exposes components for tuning.

---

## ADR-005: Graph as downstream contract

**Decision:** Blueprint/baseline consume `SemanticPaperGraph`, not re-read PDF.

**Alternatives:**

- Blueprint from spec text only — loses relational structure (method uses dataset)
- End-to-end LLM codegen — unverifiable modules

**Edge inference:** Rule-based `EDGE_RULES` today — interview: could upgrade to learned linker with human review loop.

---

## ADR-006: Refuse unsupported baseline families

**Decision:** `BaselineGenerator` returns `supported: false` with explicit message for unknown families.

**Why not generic template:** Generic CNN stub for a diffusion paper is **actively harmful** — user believes they have a reproduction.

**Supported set is explicit:** LORA, TRANSFORMER, MLP, CNN, VIT, DIFFUSION — expandable with new template packs.

---

## ADR-007: Honest reproduction comparability

**Decision:** `metric_comparable` flag + `synthetic_warning` in every reproduction report.

**Rule:** Smoke compile success ≠ paper metric reproduction.

**Levels:**

- `smoke_test` — unsupported family or no project
- `partial` — missing training or dataset in spec
- `full` — spec complete enough for serious attempt (still not auto-comparable without human validation)

---

## ADR-008: File-backed artifacts vs database

**Decision:** JSON files per paper under `data/v2/`.

**Pros:** Git-diffable, easy local dev, no DB ops, clear artifact boundaries for tests.

**Cons:** No cross-paper SQL, concurrent write needs care, no built-in ACL.

**Scale path:** Object store (S3) + metadata in Postgres; graph in Neo4j optional.

---

## ADR-009: Agents with typed handoffs, not LLM planners

**Decision:** `AgentOrchestrator` runs fixed agent sequence; `AgentResult` is structured.

**Not chosen:** LLM decides next agent dynamically.

**Reason:** Deterministic ingest, reproducible traces, CI-testable. Agents are **module boundaries**, not autonomous reasoning.

---

## ADR-010: QA returns retrieved text (extractive)

**Decision:** `QAPipeline` answer = top chunk text slice after validation.

**Not chosen:** LLM summarization of multiple chunks.

**Tradeoff:** Less fluent answers, zero synthesis hallucination in answer body. Good for research audit tools; bad for consumer chat UX.

---

## ADR-011: v2 parallel package (strangler fig)

**Decision:** `backend/atlasse_v2/` on port 8001; v1 unchanged on 8000.

**Benefits:** Risk isolation, A/B on golden papers, no big-bang rewrite.

---

## ADR-012: Golden acceptance on synthetic PDFs

**Decision:** `golden_acceptance.py` generates minimal PDFs from text profiles, not scraping arXiv.

**Pros:** CI-stable, no network, fast, controlled section content.

**Cons:** Does not test parser on real PDF layout noise — supplement with real PDF integration tests (LoRA synthetic in `test_integration.py`).

---

## ADR-013: Cross-encoder optional with fallback

**Decision:** `CrossEncoderReranker` catches errors; logs fallback message.

**Reason:** CI sandboxes and air-gapped deploys must not fail ingest on HuggingFace download.

---

## ADR-014: Spec reuse detection post-hoc

**Decision:** `_validate_no_reuse` flags duplicate field prefixes with lowered confidence.

**Not chosen:** Hard fail on reuse — would flake on legitimately similar short fields.

**Improvement path:** Compare `source_chunks` disjointness, not just string prefix.

---

## Decision matrix (quick reference)

| Question | v2 answer |
|----------|-----------|
| Where is truth? | Evidence spans in memory + graph entities |
| What if missing? | `missing: true`, assumptions listed |
| Can LLM invent modules? | No — blueprint needs entity keyword match |
| Can we compare metrics? | Only if `metric_comparable` true |
| How to debug wrong field? | retrieval-debug + agent trace + source_chunks |
| Multi-paper search? | Not in v2 core — add search tier |

---

## Related documents

- [interview_deep_dive.md](interview_deep_dive.md)
- [failure_modes.md](failure_modes.md)
