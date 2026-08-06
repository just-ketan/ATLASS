"""Phase 2: Typed knowledge graph over research entities.

Entities: Method, Dataset, Loss, Optimizer, Metric, Model, Module, Task,
Input, Output, Contribution, Limitation, Future Work, Hyperparameter,
Experiment, Baseline, Claim, Observation.

Each entity stores: text, normalized name, page, section, paragraph id,
confidence, citations.

Graph edges: uses_dataset, evaluates_on, improves, trained_with,
compares_against, depends_on, extends, proposes, reports.

Only graph objects may be consumed by downstream stages — never raw paragraphs.
"""

from __future__ import annotations

import json
from pathlib import Path

from atlasse_v2.core.models import ExtractedField, GraphEdge, GraphEntity, ParsedDocument, Provenance
from atlasse_v2.core.types import EdgeType, EntityType

FIELD_ENTITY_MAP = {
    "problem": EntityType.TASK,
    "contribution": EntityType.CONTRIBUTION,
    "task": EntityType.TASK,
    "dataset": EntityType.DATASET,
    "metric": EntityType.METRIC,
    "method": EntityType.METHOD,
    "architecture": EntityType.MODEL,
    "loss": EntityType.LOSS,
    "training": EntityType.HYPERPARAMETER,
    "evaluation": EntityType.EXPERIMENT,
    "baseline": EntityType.BASELINE,
    "limitation": EntityType.LIMITATION,
    "future_work": EntityType.FUTURE_WORK,
}

EDGE_RULES = [
    ("method", "dataset", EdgeType.USES_DATASET),
    ("method", "metric", EdgeType.REPORTS),
    ("method", "baseline", EdgeType.COMPARES_AGAINST),
    ("architecture", "dataset", EdgeType.EVALUATES_ON),
    ("method", "loss", EdgeType.TRAINED_WITH),
]


class SemanticPaperGraph:
    GRAPH_DIR = "data/v2/knowledge_graphs"

    def __init__(self, paper_id: str):
        self.paper_id = paper_id
        self.entities: dict[str, GraphEntity] = {}
        self.edges: list[GraphEdge] = []
        self._counter = 0

    def add_entity(
        self,
        entity_type: EntityType,
        text: str,
        normalized_name: str,
        provenance: Provenance,
        confidence: float = 0.0,
        citations: list[str] | None = None,
    ) -> str:
        for eid, entity in self.entities.items():
            if (
                entity.entity_type == entity_type
                and entity.normalized_name.lower() == normalized_name.lower()
            ):
                return eid

        eid = f"ent_{self._counter}"
        self._counter += 1
        self.entities[eid] = GraphEntity(
            entity_id=eid,
            entity_type=entity_type,
            text=text,
            normalized_name=normalized_name,
            provenance=provenance,
            confidence=confidence,
            citations=citations or [],
        )
        return eid

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        confidence: float = 0.0,
        provenance: Provenance | None = None,
    ) -> None:
        self.edges.append(GraphEdge(
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            confidence=confidence,
            provenance=provenance,
        ))

    def build_from_document(self, document: ParsedDocument) -> SemanticPaperGraph:
        """Heuristic entity extraction from parsed document — to be replaced by Phase 3 extractors."""
        for section in document.section_tree:
            provenance = Provenance(
                page=section.page_start,
                section=section.section_type,
                confidence=0.5,
            )
            if section.section_type.value in ("datasets", "experiments"):
                self.add_entity(
                    EntityType.DATASET,
                    text=section.text[:500],
                    normalized_name=section.title,
                    provenance=provenance,
                )
            elif section.section_type.value in ("method", "architecture"):
                self.add_entity(
                    EntityType.METHOD,
                    text=section.text[:500],
                    normalized_name=section.title,
                    provenance=provenance,
                )
        return self

    def build_from_extracted(self, extracted: dict[str, ExtractedField]) -> SemanticPaperGraph:
        """Populate graph from Phase 3 extractor outputs and infer typed edges."""
        entity_ids: dict[str, str] = {}
        for field_name, field in extracted.items():
            if field.missing or not field.value:
                continue
            entity_type = FIELD_ENTITY_MAP.get(field_name)
            if entity_type is None:
                continue
            provenance = (
                field.supporting_spans[0].provenance
                if field.supporting_spans
                else Provenance()
            )
            eid = self.add_entity(
                entity_type=entity_type,
                text=field.value[:500],
                normalized_name=field_name,
                provenance=provenance,
                confidence=field.confidence,
                citations=field.citations,
            )
            entity_ids[field_name] = eid

        for src_field, dst_field, edge_type in EDGE_RULES:
            src_id = entity_ids.get(src_field)
            dst_id = entity_ids.get(dst_field)
            if src_id and dst_id:
                self.add_edge(src_id, dst_id, edge_type, confidence=0.7)
        return self

    def get_entities_by_type(self, entity_type: EntityType) -> list[GraphEntity]:
        return [e for e in self.entities.values() if e.entity_type == entity_type]

    def get_neighbors(self, entity_id: str) -> list[tuple[GraphEntity, EdgeType]]:
        neighbors = []
        for edge in self.edges:
            target_id = None
            if edge.source_id == entity_id:
                target_id = edge.target_id
            elif edge.target_id == entity_id:
                target_id = edge.source_id
            if target_id and target_id in self.entities:
                neighbors.append((self.entities[target_id], edge.edge_type))
        return neighbors

    def save(self, base_dir: str | None = None) -> str:
        base = Path(base_dir or self.GRAPH_DIR) / self.paper_id
        base.mkdir(parents=True, exist_ok=True)
        path = base / "graph.json"
        payload = {
            "paper_id": self.paper_id,
            "entities": {
                eid: {
                    "entity_id": e.entity_id,
                    "entity_type": e.entity_type.value,
                    "text": e.text,
                    "normalized_name": e.normalized_name,
                    "confidence": e.confidence,
                    "citations": e.citations,
                    "provenance": {
                        "page": e.provenance.page,
                        "section": str(e.provenance.section),
                        "paragraph_id": e.provenance.paragraph_id,
                        "confidence": e.provenance.confidence,
                    },
                }
                for eid, e in self.entities.items()
            },
            "edges": [
                {
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "edge_type": e.edge_type.value,
                    "confidence": e.confidence,
                }
                for e in self.edges
            ],
        }
        path.write_text(json.dumps(payload, indent=2))
        return str(path)

    @classmethod
    def load(cls, paper_id: str, base_dir: str | None = None) -> SemanticPaperGraph:
        path = Path(base_dir or cls.GRAPH_DIR) / paper_id / "graph.json"
        graph = cls(paper_id)
        if not path.exists():
            return graph
        payload = json.loads(path.read_text())
        for eid, edata in payload.get("entities", {}).items():
            prov = edata.get("provenance", {})
            graph.entities[eid] = GraphEntity(
                entity_id=edata["entity_id"],
                entity_type=EntityType(edata["entity_type"]),
                text=edata["text"],
                normalized_name=edata["normalized_name"],
                provenance=Provenance(
                    page=prov.get("page"),
                    section=prov.get("section", "unknown"),
                    paragraph_id=prov.get("paragraph_id"),
                    confidence=prov.get("confidence", 0.0),
                ),
                confidence=edata.get("confidence", 0.0),
                citations=edata.get("citations", []),
            )
            graph._counter += 1
        for edata in payload.get("edges", []):
            graph.edges.append(GraphEdge(
                source_id=edata["source_id"],
                target_id=edata["target_id"],
                edge_type=EdgeType(edata["edge_type"]),
                confidence=edata.get("confidence", 0.0),
            ))
        return graph
