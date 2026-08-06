"""Persist and load ParsedDocument artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from atlasse_v2.core.models import ParsedDocument, SectionNode
from atlasse_v2.core.types import SectionType


class DocumentStore:
    PARSED_DIR = "data/v2/parsed"

    @classmethod
    def save(cls, document: ParsedDocument, base_dir: str | None = None) -> str:
        base = Path(base_dir or cls.PARSED_DIR) / document.paper_id
        base.mkdir(parents=True, exist_ok=True)
        path = base / "document.json"
        payload = {
            "paper_id": document.paper_id,
            "title": document.title,
            "paragraphs": document.paragraphs,
            "figures": document.figures,
            "tables": document.tables,
            "equations": document.equations,
            "metadata": document.metadata,
            "section_tree": [_section_to_dict(s) for s in document.section_tree],
        }
        path.write_text(json.dumps(payload, indent=2))
        return str(path)

    @classmethod
    def load(cls, paper_id: str, base_dir: str | None = None) -> ParsedDocument | None:
        path = Path(base_dir or cls.PARSED_DIR) / paper_id / "document.json"
        if not path.exists():
            return None
        payload = json.loads(path.read_text())
        return ParsedDocument(
            paper_id=payload["paper_id"],
            title=payload.get("title"),
            section_tree=[_section_from_dict(s) for s in payload.get("section_tree", [])],
            paragraphs=payload.get("paragraphs", {}),
            figures=payload.get("figures", []),
            tables=payload.get("tables", []),
            equations=payload.get("equations", []),
            metadata=payload.get("metadata", {}),
        )


def _section_to_dict(section: SectionNode) -> dict:
    return {
        "section_id": section.section_id,
        "title": section.title,
        "section_type": section.section_type.value if isinstance(section.section_type, SectionType) else section.section_type,
        "level": section.level,
        "page_start": section.page_start,
        "page_end": section.page_end,
        "paragraph_ids": section.paragraph_ids,
        "figure_refs": section.figure_refs,
        "table_refs": section.table_refs,
        "equation_refs": section.equation_refs,
        "text": section.text,
    }


def _section_from_dict(data: dict) -> SectionNode:
    try:
        section_type = SectionType(data.get("section_type", "unknown"))
    except ValueError:
        section_type = data.get("section_type", "unknown")
    return SectionNode(
        section_id=data["section_id"],
        title=data["title"],
        section_type=section_type,
        level=data.get("level", 1),
        page_start=data.get("page_start"),
        page_end=data.get("page_end"),
        paragraph_ids=data.get("paragraph_ids", []),
        figure_refs=data.get("figure_refs", []),
        table_refs=data.get("table_refs", []),
        equation_refs=data.get("equation_refs", []),
        text=data.get("text", ""),
    )
