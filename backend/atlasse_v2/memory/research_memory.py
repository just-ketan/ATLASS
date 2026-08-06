"""Phase 5: Build permanent research memory from parsed documents.

Splits paper into paragraphs, semantic blocks, tables, captions, equations,
and algorithms. Each chunk stores chunk_id, page, section, paragraph,
entities, embedding, keywords, and citations.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from atlasse_v2.core.models import ParsedDocument, ResearchChunk
from atlasse_v2.core.types import SectionType
from atlasse_v2.memory.chunk_patterns import (
    extract_algorithms,
    extract_captions,
    extract_equations,
    extract_tables,
)


class ResearchMemory:
    MEMORY_DIR = "data/v2/memory_indices"

    def __init__(self, paper_id: str):
        self.paper_id = paper_id
        self.chunks: dict[str, ResearchChunk] = {}

    def build_from_document(self, document: ParsedDocument) -> ResearchMemory:
        for section in document.section_tree:
            for pid in section.paragraph_ids:
                text = document.paragraphs.get(pid, "")
                if not text.strip():
                    continue
                self._add_chunk(
                    text=text,
                    page=section.page_start,
                    section=section.section_type,
                    paragraph_id=pid,
                    chunk_type="paragraph",
                )
            self._add_structured_chunks(section)
        return self

    def _add_chunk(
        self,
        text: str,
        page: int | None,
        section: SectionType | str,
        paragraph_id: str | None,
        chunk_type: str,
    ) -> str:
        chunk_id = f"chunk_{uuid.uuid4().hex[:8]}"
        self.chunks[chunk_id] = ResearchChunk(
            chunk_id=chunk_id,
            text=text,
            page=page,
            section=section,
            paragraph_id=paragraph_id,
            chunk_type=chunk_type,
            keywords=self._extract_keywords(text),
            citations=self._extract_citations(text),
        )
        return chunk_id

    def _add_structured_chunks(self, section) -> None:
        text = section.text
        for fig_num, caption in extract_captions(text):
            self._add_chunk(
                text=f"Figure {fig_num}: {caption}",
                page=section.page_start,
                section=section.section_type,
                paragraph_id=None,
                chunk_type="caption",
            )
        for tab_num, body in extract_tables(text):
            self._add_chunk(
                text=f"Table {tab_num}: {body}",
                page=section.page_start,
                section=section.section_type,
                paragraph_id=None,
                chunk_type="table",
            )
        for eq in extract_equations(text):
            self._add_chunk(
                text=eq,
                page=section.page_start,
                section=section.section_type,
                paragraph_id=None,
                chunk_type="equation",
            )
        for alg in extract_algorithms(text):
            self._add_chunk(
                text=alg,
                page=section.page_start,
                section=section.section_type,
                paragraph_id=None,
                chunk_type="algorithm",
            )

    def get_by_section(self, section: SectionType | str) -> list[ResearchChunk]:
        target = section.value if isinstance(section, SectionType) else section
        return [
            c for c in self.chunks.values()
            if (c.section.value if isinstance(c.section, SectionType) else c.section) == target
        ]

    def get_by_sections(self, sections: list[SectionType]) -> list[ResearchChunk]:
        targets = {s.value for s in sections}
        return [
            c for c in self.chunks.values()
            if (c.section.value if isinstance(c.section, SectionType) else c.section) in targets
        ]

    def tag_from_graph(self, graph) -> ResearchMemory:
        """Attach graph entity names to chunks whose text mentions them."""
        for chunk in self.chunks.values():
            text_lower = chunk.text.lower()
            tagged = list(chunk.entities)
            for entity in graph.entities.values():
                name = entity.normalized_name.lower()
                if len(name) > 2 and name in text_lower:
                    tagged.append(entity.normalized_name)
                for kw in entity.text.split()[:5]:
                    kw = kw.strip().lower()
                    if len(kw) > 3 and kw in text_lower:
                        tagged.append(entity.normalized_name)
            chunk.entities = list(dict.fromkeys(tagged))
        return self

    @staticmethod
    def _extract_keywords(text: str) -> list[str]:
        import re
        tokens = re.findall(r"\b[A-Z][A-Za-z0-9\-]{2,}\b", text)
        return list(dict.fromkeys(tokens))[:10]

    @staticmethod
    def _extract_citations(text: str) -> list[str]:
        import re
        return re.findall(r"([A-Z][a-z]+ et al\.?, \d{4})", text)

    def save(self, base_dir: str | None = None) -> str:
        base = Path(base_dir or self.MEMORY_DIR) / self.paper_id
        base.mkdir(parents=True, exist_ok=True)
        path = base / "chunks.json"
        payload = {
            "paper_id": self.paper_id,
            "chunks": {
                cid: {
                    "chunk_id": c.chunk_id,
                    "text": c.text,
                    "page": c.page,
                    "section": c.section.value if isinstance(c.section, SectionType) else c.section,
                    "paragraph_id": c.paragraph_id,
                    "chunk_type": c.chunk_type,
                    "entities": c.entities,
                    "keywords": c.keywords,
                    "citations": c.citations,
                }
                for cid, c in self.chunks.items()
            },
        }
        path.write_text(json.dumps(payload, indent=2))
        from atlasse_v2.memory.vector_index import MemoryVectorIndex
        MemoryVectorIndex(self.paper_id).build(self.chunks).save(base_dir or self.MEMORY_DIR)
        return str(path)

    @classmethod
    def load(cls, paper_id: str, base_dir: str | None = None) -> ResearchMemory:
        path = Path(base_dir or cls.MEMORY_DIR) / paper_id / "chunks.json"
        memory = cls(paper_id)
        if not path.exists():
            return memory
        payload = json.loads(path.read_text())
        for cid, cdata in payload.get("chunks", {}).items():
            section_raw = cdata.get("section", "unknown")
            try:
                section = SectionType(section_raw)
            except ValueError:
                section = section_raw
            memory.chunks[cid] = ResearchChunk(
                chunk_id=cdata["chunk_id"],
                text=cdata["text"],
                page=cdata.get("page"),
                section=section,
                paragraph_id=cdata.get("paragraph_id"),
                chunk_type=cdata.get("chunk_type", "paragraph"),
                entities=cdata.get("entities", []),
                keywords=cdata.get("keywords", []),
                citations=cdata.get("citations", []),
            )
        return memory
