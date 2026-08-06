"""Core data models shared across all ATLASS v2 phases."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .types import EdgeType, EntityType, SectionType


@dataclass
class Provenance:
    page: int | None = None
    section: SectionType | str = SectionType.UNKNOWN
    paragraph_id: str | None = None
    chunk_id: str | None = None
    confidence: float = 0.0
    citations: list[str] = field(default_factory=list)


@dataclass
class EvidenceSpan:
    text: str
    provenance: Provenance
    score: float = 0.0


@dataclass
class ExtractedField:
    """Result of a dedicated extractor — never answers outside retrieved evidence."""

    value: str | None
    supporting_spans: list[EvidenceSpan] = field(default_factory=list)
    confidence: float = 0.0
    citations: list[str] = field(default_factory=list)
    missing: bool = False
    assumptions: list[str] = field(default_factory=list)


@dataclass
class ResearchChunk:
    """Permanent research memory unit (Phase 5)."""

    chunk_id: str
    text: str
    page: int | None
    section: SectionType | str
    paragraph_id: str | None
    chunk_type: str  # paragraph | semantic_block | table | caption | equation | algorithm
    entities: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    embedding: list[float] | None = None


@dataclass
class GraphEntity:
    entity_id: str
    entity_type: EntityType
    text: str
    normalized_name: str
    provenance: Provenance
    confidence: float = 0.0
    citations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source_id: str
    target_id: str
    edge_type: EdgeType
    confidence: float = 0.0
    provenance: Provenance | None = None


@dataclass
class SectionNode:
    section_id: str
    title: str
    section_type: SectionType
    level: int
    page_start: int | None
    page_end: int | None
    paragraph_ids: list[str] = field(default_factory=list)
    figure_refs: list[str] = field(default_factory=list)
    table_refs: list[str] = field(default_factory=list)
    equation_refs: list[str] = field(default_factory=list)
    children: list[SectionNode] = field(default_factory=list)
    text: str = ""


@dataclass
class ParsedDocument:
    """Phase 1 output — full structural parse with provenance."""

    paper_id: str
    title: str | None
    section_tree: list[SectionNode]
    paragraphs: dict[str, str]  # paragraph_id → text
    figures: list[dict[str, Any]] = field(default_factory=list)
    tables: list[dict[str, Any]] = field(default_factory=list)
    equations: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
