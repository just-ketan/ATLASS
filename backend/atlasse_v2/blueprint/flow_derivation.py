"""Derive data/training/evaluation/inference flows from graph and spec."""

from __future__ import annotations

from atlasse_v2.core.types import EdgeType, EntityType
from atlasse_v2.graph.semantic_graph import SemanticPaperGraph


def derive_flows(graph: SemanticPaperGraph, spec: dict | None = None) -> dict:
    spec = spec or {}
    fields = spec.get("fields", {})

    data_flow = _build_data_flow(graph, fields)
    training_flow = _build_training_flow(graph, fields)
    evaluation_flow = _build_evaluation_flow(graph, fields)
    inference_flow = _build_inference_flow(graph, fields)
    dependencies = _derive_dependencies(spec)

    return {
        "data_flow": data_flow,
        "training_flow": training_flow,
        "evaluation_flow": evaluation_flow,
        "inference_flow": inference_flow,
        "dependencies": dependencies,
    }


def _entity_label(graph: SemanticPaperGraph, entity_type: EntityType) -> str | None:
    entities = graph.get_entities_by_type(entity_type)
    if entities:
        return entities[0].normalized_name
    return None


def _build_data_flow(graph: SemanticPaperGraph, fields: dict) -> list[dict]:
    steps = []
    dataset = _entity_label(graph, EntityType.DATASET) or fields.get("dataset", {}).get("value", "")[:80]
    if dataset:
        steps.append({"step": "load_dataset", "target": "src/data/dataset.py", "source": "dataset"})
    task = fields.get("task", {}).get("value")
    if task:
        steps.append({"step": "preprocess", "source": "task", "detail": task[:120]})
    if steps:
        steps.append({"step": "batch", "target": "src/data/dataset.py", "output": "model_input"})
    return steps


def _build_training_flow(graph: SemanticPaperGraph, fields: dict) -> list[dict]:
    steps = []
    method = _entity_label(graph, EntityType.METHOD)
    if method:
        steps.append({"step": "forward", "source": "method", "entity": method})
    loss = _entity_label(graph, EntityType.LOSS) or fields.get("loss", {}).get("value", "")[:80]
    if loss:
        steps.append({"step": "compute_loss", "target": "src/training/loss.py", "source": "loss"})
    training = fields.get("training", {}).get("value")
    if training:
        steps.append({"step": "optimize", "target": "src/train.py", "detail": training[:120]})
    elif method:
        steps.append({"step": "optimize", "target": "src/train.py", "source": "method"})
    return steps


def _build_evaluation_flow(graph: SemanticPaperGraph, fields: dict) -> list[dict]:
    steps = []
    metric = _entity_label(graph, EntityType.METRIC) or fields.get("metric", {}).get("value", "")[:80]
    if metric:
        steps.append({"step": "compute_metrics", "target": "src/evaluate.py", "source": "metric"})
    eval_field = fields.get("evaluation", {}).get("value")
    if eval_field:
        steps.append({"step": "evaluate", "detail": eval_field[:120]})
    baseline = fields.get("baseline", {}).get("value")
    if baseline:
        steps.append({"step": "compare_baselines", "source": "baseline", "detail": baseline[:80]})
    return steps


def _build_inference_flow(graph: SemanticPaperGraph, fields: dict) -> list[dict]:
    steps = []
    arch = fields.get("architecture", {}).get("value") or fields.get("method", {}).get("value")
    if arch:
        steps.append({"step": "encode_input", "source": "architecture", "detail": arch[:120]})
        steps.append({"step": "model_forward", "target": "src/model/"})
        steps.append({"step": "decode_output", "source": "task"})
    return steps


def _derive_dependencies(spec: dict) -> list[str]:
    deps = ["torch"]
    fields = spec.get("fields", {})
    combined = " ".join(
        str(f.get("value", "")) for f in fields.values() if f.get("value")
    ).lower()
    if "transformer" in combined or "bert" in combined or "lora" in combined:
        deps.append("transformers")
    if "glue" in combined or "dataset" in combined:
        deps.append("datasets")
    deps.append("pyyaml")
    return sorted(set(deps))
