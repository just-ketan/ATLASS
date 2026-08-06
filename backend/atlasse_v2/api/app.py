"""Phase 13 — FastAPI entry point for ATLASS v2."""

from __future__ import annotations

from pathlib import Path

from atlasse_v2.agents.orchestrator import AgentOrchestrator
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

    class AskRequest(BaseModel):
        question: str

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
            result = orchestrator.process_paper(tmp_path)
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

    return app


app = create_app()
