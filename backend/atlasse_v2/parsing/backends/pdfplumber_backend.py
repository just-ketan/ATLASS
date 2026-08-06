"""pdfplumber parser backend — fallback when PyMuPDF yields poor layout."""

from __future__ import annotations

from pathlib import Path


class PdfPlumberBackend:
    def extract_pages(self, pdf_path: Path) -> list[dict]:
        try:
            import pdfplumber
        except ImportError as exc:
            raise RuntimeError("Install pdfplumber: pip install pdfplumber") from exc

        pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                pages.append({"page": i + 1, "text": page.extract_text() or ""})
        return pages
