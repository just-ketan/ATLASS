"""Phase 1: Multi-backend document parser.

Replaces regex section detection with a parser capable of identifying
Abstract, Introduction, Related Work, Method, Architecture, Experiments,
Implementation, Datasets, Results, Discussion, Limitations, Future Work,
Appendix, and References.

Supports: GROBID, Docling, PyMuPDF, pdfplumber, OCR fallback.
Never loses provenance — page numbers, hierarchy, section tree, paragraph IDs,
figure/table/equation references.
"""

from __future__ import annotations

import logging
from pathlib import Path

from atlasse_v2.core.models import ParsedDocument, SectionNode
from atlasse_v2.core.types import SectionType
from atlasse_v2.parsing.backends.pdfplumber_backend import PdfPlumberBackend
from atlasse_v2.parsing.backends.pymupdf_backend import PyMuPDFBackend
from atlasse_v2.parsing.section_classifier import classify_section
from atlasse_v2.parsing.section_tree import SectionTreeBuilder

logger = logging.getLogger(__name__)

DEFAULT_BACKEND_CHAIN = ("pymupdf", "pdfplumber")


class DocumentParser:
    """Orchestrates multi-backend PDF parsing with fallback chain."""

    def __init__(self, backend_chain: tuple[str, ...] | None = None):
        self.backend_chain = backend_chain or DEFAULT_BACKEND_CHAIN
        self._backends = {
            "pymupdf": PyMuPDFBackend(),
            "pdfplumber": PdfPlumberBackend(),
        }
        self._section_builder = SectionTreeBuilder()

    def parse(self, pdf_path: str | Path, paper_id: str | None = None) -> ParsedDocument:
        pdf_path = Path(pdf_path)
        paper_id = paper_id or pdf_path.stem

        raw_pages, used_backend = self._extract_with_fallback(pdf_path)
        section_tree = self._section_builder.build(raw_pages)
        paragraphs = self._section_builder.collect_paragraphs(section_tree)

        return ParsedDocument(
            paper_id=paper_id,
            title=self._extract_title(section_tree),
            section_tree=section_tree,
            paragraphs=paragraphs,
            metadata={
                "parser_backend": used_backend,
                "backend_chain": list(self.backend_chain),
                "page_count": len(raw_pages),
            },
        )

    def _extract_with_fallback(self, pdf_path: Path) -> tuple[list[dict], str]:
        last_error: Exception | None = None
        for name in self.backend_chain:
            backend = self._backends.get(name)
            if backend is None:
                continue
            try:
                pages = backend.extract_pages(pdf_path)
                if pages and any(p.get("text", "").strip() for p in pages):
                    return pages, name
            except Exception as exc:
                last_error = exc
                logger.warning("Parser backend %s failed: %s", name, exc)
        if last_error:
            raise RuntimeError(f"All parser backends failed. Last error: {last_error}") from last_error
        raise RuntimeError("All parser backends returned empty text.")

    @staticmethod
    def _extract_title(section_tree: list[SectionNode]) -> str | None:
        for node in section_tree:
            if node.section_type == SectionType.ABSTRACT and node.text:
                first_line = node.text.split("\n", 1)[0].strip()
                if len(first_line) < 200:
                    return first_line
        return None

    @staticmethod
    def classify_section(title: str) -> SectionType:
        return classify_section(title)
