"""Build hierarchical section tree from parsed pages."""

from __future__ import annotations

import re
import uuid

from atlasse_v2.core.models import SectionNode
from atlasse_v2.core.types import SectionType
from atlasse_v2.parsing.section_classifier import classify_section


class SectionTreeBuilder:
    """Construct section tree with paragraph IDs and cross-references."""

    HEADING_PATTERN = re.compile(
        r"^\s*((?:\d+(?:\.\d+)*\.?\s+)?[A-Z][A-Za-z0-9\s\-&]{2,})\s*$",
        re.MULTILINE,
    )
    FIGURE_REF = re.compile(r"(?:Figure|Fig\.?)\s+(\d+)", re.IGNORECASE)
    TABLE_REF = re.compile(r"(?:Table|Tab\.?)\s+(\d+)", re.IGNORECASE)
    EQUATION_REF = re.compile(r"(?:Equation|Eq\.?)\s+\((\d+)\)", re.IGNORECASE)

    def build(self, pages: list[dict]) -> list[SectionNode]:
        full_text = "\n\n".join(p["text"] for p in pages)
        page_offsets = self._page_offsets(pages)

        matches = list(self.HEADING_PATTERN.finditer(full_text))
        if not matches:
            return [self._make_section("full_document", "Document", SectionType.UNKNOWN, full_text, 1)]

        sections: list[SectionNode] = []
        for i, match in enumerate(matches):
            title = match.group(1).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
            content = full_text[start:end].strip()
            page = self._char_to_page(start, page_offsets)
            section_type = classify_section(title)
            sections.append(self._make_section(
                section_id=f"sec_{i}",
                title=title,
                section_type=section_type,
                text=content,
                page=page,
            ))
        return sections

    def collect_paragraphs(self, section_tree: list[SectionNode]) -> dict[str, str]:
        paragraphs: dict[str, str] = {}
        for section in section_tree:
            blocks = [b.strip() for b in section.text.split("\n\n") if b.strip()]
            section.paragraph_ids = []
            for block in blocks:
                pid = f"p_{uuid.uuid4().hex[:8]}"
                paragraphs[pid] = block
                section.paragraph_ids.append(pid)
        return paragraphs

    def _make_section(
        self,
        section_id: str,
        title: str,
        section_type: SectionType,
        text: str,
        page: int | None = None,
    ) -> SectionNode:
        return SectionNode(
            section_id=section_id,
            title=title,
            section_type=section_type,
            level=1,
            page_start=page,
            page_end=page,
            text=text,
            figure_refs=self.FIGURE_REF.findall(text),
            table_refs=self.TABLE_REF.findall(text),
            equation_refs=self.EQUATION_REF.findall(text),
        )

    @staticmethod
    def _page_offsets(pages: list[dict]) -> list[tuple[int, int]]:
        offsets = []
        pos = 0
        for page in pages:
            start = pos
            pos += len(page["text"]) + 2
            offsets.append((start, page["page"]))
        return offsets

    @staticmethod
    def _char_to_page(char_pos: int, offsets: list[tuple[int, int]]) -> int | None:
        for start, page_num in reversed(offsets):
            if char_pos >= start:
                return page_num
        return offsets[0][1] if offsets else None
