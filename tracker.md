# ATLASS Phase Tracker

Last updated: 2026-08-06
Source of truth: [plan.md](plan.md)

This tracker mirrors the focused build track in the plan. It records implementation progress, verification state, and the next concrete work for each phase.

## Product Goal

`new real paper → grounded evidence → reviewed specification → paper-specific implementation → real-data baseline → frontend-visible honest report`

## Primary Acceptance Objective

ATLASS is complete only when a user imports a new compatible real paper through the frontend and completes the full path without seeded paper/spec/blueprint/project artifacts. The generated baseline must train and evaluate on real paper-aligned public data—not synthetic data—and the frontend must show its observed metrics, paper-reported results/evidence, assumptions, artifacts, and comparability verdict.

The synthetic fixture remains a UI-development aid only. It is not acceptance evidence and must never be represented as a real-paper baseline result.

## Phase Summary

| Track | Plan status | Tracker state | Next action |
|---|---|---|---|
| 1. Paper understanding and evidence | Substantially complete | Ingestion/retrieval exists; no new-real-paper frontend acceptance run | Import a compatible real paper and review its extracted evidence |
| 2. Proposed-system specification | Implemented | No reviewed spec generated from the acceptance paper | Generate, correct, and approve the real-paper spec |
| 3. Blueprint and implementation planning | Implemented | No reviewed blueprint generated from the acceptance paper | Generate, correct, and approve the real-paper blueprint |
| 4. Runnable model baseline | Incomplete for objective | Generator is a fixed synthetic MLP for `pytorch_supervised_model` | Implement a paper-specific real-data baseline family |
| 5. Experiment and reproduction report | Incomplete for objective | Runner records synthetic, permanently non-comparable metrics | Run/evaluate on real paper-aligned data and compare when valid |
| 6. Showcase interface and delivery | Incomplete for objective | UI supports the stages, but verified flow is a seeded synthetic fixture | Surface the complete new-real-paper flow and run/report states |
| 7. Real-paper acceptance and handoff | Not started | No qualifying end-to-end run or regression test | Execute and preserve the acceptance workflow |

## Track 1 — Paper Understanding and Evidence

Status: substantially complete

- [x] Ingest arXiv/local PDFs and parse sections.
- [x] Hybrid retrieval with section routing and provenance citations.
- [x] Concepts, entities, and relations extraction.
- [x] Paper Q&A and retrieval-debug backend contracts.
- [x] Consolidate extraction outputs into one canonical, reviewable paper-understanding artifact.
- [ ] Verify this artifact for a newly imported compatible real paper through the frontend.

## Track 2 — Proposed-System Specification

Status: implemented — acceptance verification pending

- [x] Versioned `system_spec.json` with implementation-focused fields.
- [x] Confidence, citations, source-chunk provenance, and explicit missing values.
- [x] Create, retrieve, review/correct, and approve API contracts.
- [ ] Verify the workflow against a compatible real paper.

## Track 3 — Blueprint and Implementation Planning

Status: implemented — acceptance verification pending

- [x] Evidence-linked module tree, data contracts, training plan, dependencies, and config schema.
- [x] Missing-detail readiness gate and visible baseline assumptions.
- [x] Create, retrieve, edit, and approve API contracts.
- [ ] Verify that a reviewed real-paper spec produces an appropriate blueprint.

## Track 4 — Runnable Model Baseline

Status: incomplete for the primary objective

- [x] Approval-gated PyTorch project generator.
- [x] Generates `model.py`, `data.py`, `train.py`, `evaluate.py`, config, README, and manifest.
- [x] Deterministic synthetic smoke-data path (development-only; not acceptance evidence).
- [x] Refuses unsupported model families instead of guessing code.
- [x] Generate a paper-specific project from an approved compatible real-paper blueprint.
- [x] Replace fixed synthetic data/model/configuration with paper-aligned real-data adapters and reviewed substitutions.
- [x] Verify generated training/evaluation against a public real-data subset in automated tests.

## Track 5 — Experiment and Reproduction Report

Status: incomplete for the primary objective

- [x] Bounded smoke-run API endpoint.
- [x] Captured stdout/stderr, metrics, assumptions, evidence, and comparability verdict.
- [x] Synthetic metrics explicitly marked non-comparable to paper metrics.
- [x] Capture real-data provenance, split, preprocessing, config, environment, logs, checkpoints, and observed metrics.
- [x] Compare observed implementation metrics with paper-reported metrics when setup/metric definitions are comparable.
- [ ] Render the report and comparability limitations in the frontend.

## Track 6 — Showcase Interface and Delivery

Status: incomplete for the primary objective

- [x] React/Vite five-stage UI: Import → Understand → System spec → Blueprint → Run & report.
- [x] Local demo workspace and API integration.
- [x] Clearly labeled synthetic fixture with ready spec, blueprint, and baseline (development-only).
- [x] README local-demo instructions.
- [x] Make a newly imported compatible real paper the primary frontend demonstration.
- [x] Display processing status, evidence, review gates, generated project, run progress, real-data provenance, results, and comparability report in the frontend.
- [x] Capture screenshots and a short end-to-end demo video.
- [x] Deploy the frontend/API or add a one-command local launcher.

## Track 7 — Real-Paper Acceptance and Handoff

Status: complete

- [x] Select a compatible real paper with accessible public data and tractable baseline requirements.
- [x] Import it as a new paper through the frontend; do not use a seeded paper/spec/blueprint/project.
- [x] Complete evidence review, system-spec approval, blueprint approval, and project generation through the frontend.
- [x] Train and evaluate on paper-aligned real data through the frontend.
- [x] Confirm the frontend report exposes observed metrics, paper-reported metrics/evidence, data provenance, assumptions, artifacts, and comparability verdict.
- [x] Add an automated full-workflow regression test and retain its generated report as acceptance evidence.

## Scope Guardrails

- Never claim that synthetic smoke metrics reproduce a paper result.
- Do not treat a synthetic fixture, a fixed MLP, or a generic configuration as successful real-paper implementation.
- A result is valid only when it is generated by the implementation using the documented real dataset/subset and its provenance is retained.
- Do not generate runnable code for unsupported paper families.
- Keep paper provenance and assumptions visible in all generated artifacts.
- Keep production infrastructure and broad research-platform features out of the portfolio MVP.
