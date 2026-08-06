"""PyMuPDF parser backend — primary fallback when GROBID/Docling unavailable."""

from __future__ import annotations

from pathlib import Path


class PyMuPDFBackend:
    def extract_pages(self, pdf_path: Path) -> list[dict]:
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("Install pymupdf: pip install pymupdf") from exc

        pages = []
        with fitz.open(pdf_path) as doc:
            for i, page in enumerate(doc):
                pages.append({"page": i + 1, "text": page.get_text("text")})
        return pages
