"""GROBID parser backend — structured TEI XML extraction (Phase 1)."""

from __future__ import annotations

from pathlib import Path


class GROBIDBackend:
    """Placeholder for GROBID integration."""

    def __init__(self, grobid_url: str = "http://localhost:8070"):
        self.grobid_url = grobid_url

    def extract_pages(self, pdf_path: Path) -> list[dict]:
        raise NotImplementedError(
            "GROBID backend not yet implemented. Use pymupdf backend as fallback."
        )
