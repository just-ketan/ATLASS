"""Docling parser backend — IBM Docling document understanding (Phase 1)."""

from __future__ import annotations

from pathlib import Path


class DoclingBackend:
    """Placeholder for Docling integration."""

    def extract_pages(self, pdf_path: Path) -> list[dict]:
        raise NotImplementedError(
            "Docling backend not yet implemented. Use pymupdf backend as fallback."
        )
