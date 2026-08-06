"""Phase 13 — FastAPI entry point for ATLASS v2."""

from __future__ import annotations

from pathlib import Path

from atlasse_v2.agents.orchestrator import AgentOrchestrator
from atlasse_v2.api.views import (
    architecture_dag,
    assumption_tracker,
    evidence_viewer,
    entity_browser,
)
from atlasse_v2.infra import FileCache, JobQueue, log_event, setup_logging
from atlasse_v2.memory.research_memory import ResearchMemory
from atlasse_v2.parsing.document_store import DocumentStore
from atlasse_v2.qa.qa_pipeline import QAPipeline
from atlasse_v2.retrieval.evidence_ranker import EvidenceRanker


def create_app(data_dir: str = "data/v2"):
    try:
        from fastapi import FastAPI, HTTPException, UploadFile, File
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel
    except ImportError as exc:
        raise RuntimeError("Install FastAPI dependencies to run the ATLASS v2 API.") from exc

    app = FastAPI(title="ATLASS v2 Research Cognition Engine", version="2.0.0-alpha")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    orchestrator = AgentOrchestrator(data_dir=data_dir)
    cache = FileCache(cache_dir=f"{data_dir}/cache")
    jobs = JobQueue(job_dir=f"{data_dir}/jobs")
    logger = setup_logging()

    class AskRequest(BaseModel):
        question: str

    class IngestJobRequest(BaseModel):
        paper_id: str | None = None

    @app.post("/v2/papers/ingest-async")
    async def ingest_paper_async(file: UploadFile = File(...), paper_id: str | None = None):
        import tempfile
        suffix = Path(file.filename or "paper.pdf").suffix or ".pdf"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        pid = paper_id or Path(file.filename or "paper").stem

        def _run():
            log_event(logger, "ingest_async_start", paper_id=pid)
            summary, trace = orchestrator.process_with_trace(tmp_path, paper_id=pid)
            Path(tmp_path).unlink(missing_ok=True)
            return {"summary": summary, "agent_trace": trace}

        job_id = jobs.submit(_run)
        return {"job_id": job_id, "paper_id": pid, "status": "pending"}

    @app.get("/v2/health")
    def health():
        return {"status": "ok", "version": "2.0.0-alpha"}

    @app.post("/v2/papers/ingest")
    async def ingest_paper(file: UploadFile = File(...)):
        import tempfile
        suffix = Path(file.filename or "paper.pdf").suffix or ".pdf"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        try:
            log_event(logger, "ingest_start", paper_id=file.filename)
            result, trace = orchestrator.process_with_trace(tmp_path)
            result["agent_trace"] = trace
            cache.set(f"status:{result.get('paper_id')}", result)
            return result
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    @app.get("/v2/papers/{paper_id}/status")
    def paper_status(paper_id: str):
        return orchestrator.get_status(paper_id)

    @app.get("/v2/papers/{paper_id}/sections")
    def section_tree(paper_id: str):
        document = DocumentStore.load(paper_id, base_dir=f"{data_dir}/parsed")
        if document is None:
            raise HTTPException(status_code=404, detail="Paper not found")
        return {
            "paper_id": paper_id,
            "sections": [
                {
                    "section_id": s.section_id,
                    "title": s.title,
                    "section_type": s.section_type.value if hasattr(s.section_type, "value") else s.section_type,
                    "page_start": s.page_start,
                    "paragraph_count": len(s.paragraph_ids),
                }
                for s in document.section_tree
            ],
        }

    @app.post("/v2/papers/{paper_id}/ask")
    def ask_question(paper_id: str, body: AskRequest):
        memory = ResearchMemory.load(paper_id, base_dir=f"{data_dir}/memory_indices")
        if not memory.chunks:
            raise HTTPException(status_code=404, detail="Paper memory not found — ingest first")
        ranker = EvidenceRanker(memory)
        qa = QAPipeline(ranker)
        return qa.ask(body.question, paper_id)

    @app.get("/v2/papers/{paper_id}/spec")
    def get_spec(paper_id: str):
        spec = orchestrator.pipeline.get_spec(paper_id)
        if spec is None:
            raise HTTPException(status_code=404, detail="Specification not found — ingest first")
        return spec

    @app.get("/v2/papers/{paper_id}/agent-trace")
    def agent_trace(paper_id: str):
        trace = orchestrator.get_trace(paper_id)
        if trace is None:
            raise HTTPException(status_code=404, detail="Agent trace not found — ingest first")
        return trace

    @app.get("/v2/papers/{paper_id}/evidence")
    def evidence_list(paper_id: str, limit: int = 50):
        memory = ResearchMemory.load(paper_id, base_dir=f"{data_dir}/memory_indices")
        if not memory.chunks:
            raise HTTPException(status_code=404, detail="Paper memory not found — ingest first")
        return evidence_viewer(paper_id, data_dir, limit=limit)

    @app.get("/v2/papers/{paper_id}/entities")
    def entities(paper_id: str):
        graph = orchestrator.pipeline.get_graph(paper_id)
        if not graph.entities:
            raise HTTPException(status_code=404, detail="Graph not found — ingest first")
        return entity_browser(paper_id, graph)

    @app.get("/v2/papers/{paper_id}/architecture-dag")
    def arch_dag(paper_id: str):
        blueprint = orchestrator.pipeline.get_blueprint(paper_id)
        if blueprint is None:
            raise HTTPException(status_code=404, detail="Blueprint not found — ingest first")
        return architecture_dag(blueprint)

    @app.get("/v2/papers/{paper_id}/assumptions")
    def assumptions(paper_id: str):
        spec = orchestrator.pipeline.get_spec(paper_id)
        if spec is None:
            raise HTTPException(status_code=404, detail="Specification not found — ingest first")
        baseline = orchestrator.pipeline.get_baseline(paper_id)
        return assumption_tracker(spec, baseline)

    @app.get("/v2/jobs/{job_id}")
    def job_status(job_id: str):
        status = jobs.get(job_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return status

    @app.get("/v2/papers/{paper_id}/graph")
    def get_graph(paper_id: str):
        graph = orchestrator.pipeline.get_graph(paper_id)
        if not graph.entities:
            raise HTTPException(status_code=404, detail="Graph not found — ingest first")
        return {
            "paper_id": paper_id,
            "entities": [
                {
                    "entity_id": e.entity_id,
                    "entity_type": e.entity_type.value,
                    "normalized_name": e.normalized_name,
                    "confidence": e.confidence,
                    "text_preview": e.text[:200],
                }
                for e in graph.entities.values()
            ],
            "edges": [
                {
                    "source_id": edge.source_id,
                    "target_id": edge.target_id,
                    "edge_type": edge.edge_type.value,
                }
                for edge in graph.edges
            ],
        }

    @app.get("/v2/papers/{paper_id}/retrieval-debug")
    def retrieval_debug(paper_id: str, q: str):
        memory = ResearchMemory.load(paper_id, base_dir=f"{data_dir}/memory_indices")
        if not memory.chunks:
            raise HTTPException(status_code=404, detail="Paper memory not found — ingest first")
        ranker = EvidenceRanker(memory)
        _, trace = ranker.retrieve_with_trace(q, paper_id=paper_id, top_k=5)
        return trace

    @app.get("/v2/papers/{paper_id}/blueprint")
    def get_blueprint(paper_id: str):
        blueprint = orchestrator.pipeline.get_blueprint(paper_id)
        if blueprint is None:
            raise HTTPException(status_code=404, detail="Blueprint not found — ingest first")
        return blueprint

    @app.get("/v2/papers/{paper_id}/baseline")
    def get_baseline(paper_id: str):
        baseline = orchestrator.pipeline.get_baseline(paper_id)
        if baseline is None:
            raise HTTPException(status_code=404, detail="Baseline not found — ingest first")
        return baseline

    @app.get("/v2/papers/{paper_id}/blueprint/diff")
    def blueprint_diff(paper_id: str):
        result = orchestrator.pipeline.get_blueprint_diff(paper_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Blueprint not found — ingest first")
        return result

    @app.get("/v2/papers/{paper_id}/baseline/project")
    def baseline_project_manifest(paper_id: str):
        base = Path(data_dir) / "baselines" / paper_id / "project" / "manifest.json"
        if not base.exists():
            raise HTTPException(status_code=404, detail="Baseline project not found — ingest first")
        import json
        return json.loads(base.read_text())

    @app.get("/v2/papers/{paper_id}/reproduction")
    def get_reproduction(paper_id: str):
        report = orchestrator.pipeline.get_reproduction_report(paper_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Reproduction report not found — ingest first")
        return report

    @app.post("/v2/benchmark/smoke")
    def run_benchmark_smoke():
        from atlasse_v2.evaluation.benchmark import BenchmarkSuite
        from atlasse_v2.evaluation.fixtures import make_lora_sample_document
        from atlasse_v2.evaluation.score_store import ScoreStore
        suite = BenchmarkSuite(score_store=ScoreStore(path=f"{data_dir}/benchmark/scores.json"))
        return suite.run_smoke_regression(make_lora_sample_document)

    @app.get("/v2/benchmark/scores")
    def benchmark_scores():
        from atlasse_v2.evaluation.score_store import ScoreStore
        store = ScoreStore(path=f"{data_dir}/benchmark/scores.json")
        return store.load()

    @app.get("/v2/papers/{paper_id}/missing-fields")
    def missing_fields(paper_id: str):
        result = orchestrator.pipeline.get_missing_fields(paper_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Specification not found — ingest first")
        return result

    @app.get("/v2/papers/{paper_id}/confidence-heatmap")
    def confidence_heatmap(paper_id: str):
        result = orchestrator.pipeline.get_confidence_heatmap(paper_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Specification not found — ingest first")
        return result

    return app


app = create_app()
