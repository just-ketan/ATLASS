# ATLASS v2 — Architecture Documentation Pack

Interview-oriented documentation for the ATLASS v2 **Research Cognition Engine**.

| Document | Purpose |
|----------|---------|
| [architecture.md](architecture.md) | System layers, components, deployment topology, module map |
| [data_flow.md](data_flow.md) | Artifacts, schemas, storage layout, transformations |
| [end_to_end_flow.md](end_to_end_flow.md) | Request lifecycles: ingest, QA, agents, API, evaluation |
| [design_decisions.md](design_decisions.md) | ADR-style tradeoffs (why not RAG, why graph, etc.) |
| [interview_deep_dive.md](interview_deep_dive.md) | Principal-architect interview topics, answers, probing questions |
| [failure_modes.md](failure_modes.md) | v1 failures, v2 mitigations, residual risks |

**Source of truth:** `upgrade_v2.md`, `backend/atlasse_v2/`, `v2tracker.md`

**Run the system:**

```bash
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/ -q
PYTHONPATH=backend .venv/bin/python -m uvicorn atlasse_v2.api.app:app --port 8001
PYTHONPATH=backend .venv/bin/python -m atlasse_v2.cli accept
```
