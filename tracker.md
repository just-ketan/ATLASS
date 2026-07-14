# ATLASS Phase Tracker

Last updated: 2026-07-14  
Source of truth: [plan.md](plan.md)

This tracker mirrors the focused build track in the plan. It records implementation progress, verification state, and the next concrete work for each phase.

## Product Goal

`paper → grounded evidence → system specification → implementation blueprint → runnable baseline → honest report`

## Phase Summary

| Track | Plan status | Tracker state | Next action |
|---|---|---|---|
| 1. Paper understanding and evidence | Substantially complete | Implementation exists; canonical review artifact still needed | Consolidate extraction outputs into a reviewable paper-understanding view |
| 2. Proposed-system specification | Complete — local MVP | Implemented; not yet end-to-end verified | Generate and review a spec from a compatible real paper |
| 3. Blueprint and implementation planning | Complete — local MVP | Implemented; not yet end-to-end verified | Approve/edit a real-paper blueprint |
| 4. Runnable model baseline | Complete — constrained local MVP | Generator implemented for `pytorch_supervised_model` only | Generate a baseline from a compatible approved blueprint |
| 5. Experiment and reproduction report | Implementation complete — ready for per-paper execution | Runner/reporting implemented; no run recorded | Execute one generated baseline and inspect the report |
| 6. Showcase interface and delivery | Substantially complete — local showcase shell | UI and synthetic fixture implemented; portfolio assets pending | Add real examples, record demo, and deliver locally/deployed |
| 7. Portfolio verification and handoff | Next module | Not started | Run the complete synthetic workflow and fix integration issues |

## Track 1 — Paper Understanding and Evidence

Status: substantially complete

- [x] Ingest arXiv/local PDFs and parse sections.
- [x] Hybrid retrieval with section routing and provenance citations.
- [x] Concepts, entities, and relations extraction.
- [x] Paper Q&A and retrieval-debug backend contracts.
- [ ] Consolidate extraction outputs into one canonical, reviewable paper-understanding artifact.

## Track 2 — Proposed-System Specification

Status: complete — local MVP

- [x] Versioned `system_spec.json` with implementation-focused fields.
- [x] Confidence, citations, source-chunk provenance, and explicit missing values.
- [x] Create, retrieve, review/correct, and approve API contracts.
- [ ] Verify the workflow against a compatible real paper.

## Track 3 — Blueprint and Implementation Planning

Status: complete — local MVP

- [x] Evidence-linked module tree, data contracts, training plan, dependencies, and config schema.
- [x] Missing-detail readiness gate and visible baseline assumptions.
- [x] Create, retrieve, edit, and approve API contracts.
- [ ] Verify that a reviewed real-paper spec produces an appropriate blueprint.

## Track 4 — Runnable Model Baseline

Status: complete — constrained local MVP

- [x] Approval-gated PyTorch project generator.
- [x] Generates `model.py`, `data.py`, `train.py`, `evaluate.py`, config, README, and manifest.
- [x] Deterministic synthetic smoke-data path.
- [x] Refuses unsupported model families instead of guessing code.
- [ ] Run a generated project from an approved compatible paper/fixture.

## Track 5 — Experiment and Reproduction Report

Status: implementation complete — ready for per-paper execution

- [x] Bounded smoke-run API endpoint.
- [x] Captured stdout/stderr, metrics, assumptions, evidence, and comparability verdict.
- [x] Synthetic metrics explicitly marked non-comparable to paper metrics.
- [ ] Execute the smoke path once and retain the resulting report.

## Track 6 — Showcase Interface and Delivery

Status: substantially complete — local showcase shell

- [x] React/Vite five-stage UI: Import → Understand → System spec → Blueprint → Run & report.
- [x] Local demo workspace and API integration.
- [x] Clearly labeled synthetic fixture with ready spec, blueprint, and baseline.
- [x] README local-demo instructions.
- [ ] Add 1–2 compatible real-paper examples and document their limitations.
- [ ] Capture screenshots and a short end-to-end demo video.
- [ ] Deploy the frontend/API or add a one-command local launcher.

## Track 7 — Portfolio Verification and Handoff

Status: next module

- [ ] Start the API and frontend.
- [ ] Load the synthetic demo fixture.
- [ ] Run all five UI stages through to the reproduction report.
- [ ] Fix integration failures found during the walkthrough.
- [ ] Create a focused final commit after verification.

## Scope Guardrails

- Never claim that synthetic smoke metrics reproduce a paper result.
- Do not generate runnable code for unsupported paper families.
- Keep paper provenance and assumptions visible in all generated artifacts.
- Keep production infrastructure and broad research-platform features out of the portfolio MVP.
