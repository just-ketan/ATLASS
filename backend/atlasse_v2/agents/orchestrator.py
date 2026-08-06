"""Phase 12: Agent orchestrator — agents communicate through structured objects, never free-form text."""

from __future__ import annotations

from atlasse_v2.pipeline import PaperPipeline


class AgentOrchestrator:
    """Coordinates specialized agents through typed object handoffs."""

    def __init__(self, data_dir: str = "data/v2"):
        self.pipeline = PaperPipeline(data_dir=data_dir)

    def process_paper(self, pdf_path: str, paper_id: str | None = None) -> dict:
        return self.pipeline.ingest(pdf_path, paper_id=paper_id)

    def get_status(self, paper_id: str) -> dict:
        return self.pipeline.get_status(paper_id)
