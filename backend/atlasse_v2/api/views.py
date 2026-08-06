"""API response builders for rich UI surfaces."""

from __future__ import annotations

from atlasse_v2.core.types import SectionType
from atlasse_v2.graph.semantic_graph import SemanticPaperGraph
from atlasse_v2.memory.research_memory import ResearchMemory


def evidence_viewer(paper_id: str, data_dir: str, limit: int = 50) -> dict:
    memory = ResearchMemory.load(paper_id, base_dir=f"{data_dir}/memory_indices")
    chunks = []
    for c in list(memory.chunks.values())[:limit]:
        chunks.append({
            "chunk_id": c.chunk_id,
            "chunk_type": c.chunk_type,
            "section": c.section.value if isinstance(c.section, SectionType) else c.section,
            "page": c.page,
            "text_preview": c.text[:300],
            "entities": c.entities,
            "keywords": c.keywords[:5],
            "citations": c.citations,
        })
    return {"paper_id": paper_id, "chunk_count": len(memory.chunks), "chunks": chunks}


def entity_browser(paper_id: str, graph: SemanticPaperGraph) -> dict:
    entities = []
    for e in graph.entities.values():
        entities.append({
            "entity_id": e.entity_id,
            "entity_type": e.entity_type.value,
            "normalized_name": e.normalized_name,
            "confidence": e.confidence,
            "text_preview": e.text[:200],
            "provenance": {
                "page": e.provenance.page,
                "section": str(e.provenance.section),
            },
        })
    return {"paper_id": paper_id, "entity_count": len(entities), "entities": entities}


def architecture_dag(blueprint: dict) -> dict:
    modules = blueprint.get("modules", [])
    nodes = [
        {
            "id": m.get("file") or m.get("module"),
            "label": m.get("module"),
            "evidence_entity_id": m.get("evidence_entity_id"),
        }
        for m in modules
        if m.get("file")
    ]
    edges = []
    data_flow = blueprint.get("data_flow", [])
    training_flow = blueprint.get("training_flow", [])
    for i, step in enumerate(data_flow):
        target = step.get("target")
        if target and i > 0:
            edges.append({"source": data_flow[i - 1].get("target", "data"), "target": target})
    return {
        "paper_id": blueprint.get("paper_id"),
        "nodes": nodes,
        "edges": edges,
        "data_flow": data_flow,
        "training_flow": training_flow,
        "evaluation_flow": blueprint.get("evaluation_flow", []),
    }


def assumption_tracker(spec: dict, baseline: dict | None) -> dict:
    assumptions = []
    for name, field in spec.get("fields", {}).items():
        for a in field.get("assumptions", []):
            assumptions.append({"field": name, "assumption": a, "source": "spec"})
        if field.get("missing"):
            assumptions.append({
                "field": name,
                "assumption": "Field missing from paper evidence",
                "source": "spec",
            })
    if baseline:
        for a in baseline.get("assumptions", []):
            assumptions.append({"field": "baseline", "assumption": a, "source": "baseline"})
    return {"paper_id": spec.get("paper_id"), "assumptions": assumptions, "count": len(assumptions)}
