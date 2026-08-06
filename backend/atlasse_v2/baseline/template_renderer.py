"""Render and write baseline template files with spec-filled values."""

from __future__ import annotations

import json
import re
from pathlib import Path

from atlasse_v2.baseline.templates import TEMPLATES
from atlasse_v2.core.types import ModelFamily


DEFAULTS = {
    "rank": 8,
    "alpha": 16,
    "d_model": 768,
    "n_heads": 12,
    "model_name": "roberta-base",
    "dataset_name": "glue",
    "learning_rate": 5e-5,
    "batch_size": 32,
    "epochs": 3,
}


def _spec_value(spec: dict, field: str, default: str = "") -> str:
    val = spec.get("fields", {}).get(field, {}).get("value")
    return (val or default)[:200]


def _infer_model_name(spec: dict) -> str:
    text = _spec_value(spec, "method") + " " + _spec_value(spec, "architecture")
    if "roberta" in text.lower():
        return "roberta-base"
    if "bert" in text.lower():
        return "bert-base-uncased"
    return DEFAULTS["model_name"]


def _infer_dataset(spec: dict) -> str:
    text = _spec_value(spec, "dataset").lower()
    if "glue" in text:
        return "glue"
    if "mnist" in text:
        return "mnist"
    return DEFAULTS["dataset_name"]


def build_context(paper_id: str, family: str, spec: dict, assumptions: list[str]) -> dict:
    ctx = dict(DEFAULTS)
    ctx["paper_id"] = paper_id
    ctx["family"] = family
    ctx["model_name"] = _infer_model_name(spec)
    ctx["dataset_name"] = _infer_dataset(spec)
    ctx["evidence_note"] = "Derived from system_spec.json fields: method, architecture, dataset."
    ctx["assumptions"] = "\n".join(f"- {a}" for a in assumptions) or "- None"
    return ctx


def render_template(name: str, ctx: dict) -> str:
    template = TEMPLATES.get(name, "")
    if not template:
        return ""
    try:
        return template.format(**ctx)
    except KeyError:
        return template


def write_project(
    project_dir: Path,
    paper_id: str,
    family: ModelFamily,
    file_specs: list[dict],
    spec: dict,
    assumptions: list[str],
    evidence_entity_ids: list[str],
) -> list[dict]:
    ctx = build_context(paper_id, family.value, spec, assumptions)
    manifest = []
    project_dir.mkdir(parents=True, exist_ok=True)

    for fspec in file_specs:
        path = project_dir / fspec["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        content = render_template(fspec["template"], ctx)
        path.write_text(content)
        entry = {
            "path": fspec["path"],
            "template": fspec["template"],
            "evidence_entity_ids": evidence_entity_ids,
            "spec_fields": _linked_spec_fields(fspec["template"], spec),
            "assumptions": assumptions if fspec["template"] in ("config", "train") else [],
        }
        manifest.append(entry)

    (project_dir / "requirements.txt").write_text("torch\ntransformers\ndatasets\npyyaml\n")
    manifest.append({
        "path": "requirements.txt",
        "template": "requirements",
        "evidence_entity_ids": evidence_entity_ids,
        "spec_fields": [],
        "assumptions": [],
    })
    (project_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def _linked_spec_fields(template: str, spec: dict) -> list[str]:
    mapping = {
        "lora": ["method", "architecture"],
        "base_model": ["method", "architecture"],
        "transformer": ["architecture", "method"],
        "attention": ["architecture"],
        "dataset": ["dataset"],
        "train": ["training", "loss"],
        "evaluate": ["metric", "evaluation"],
        "config": ["training", "dataset", "method"],
    }
    fields = mapping.get(template, [])
    return [f for f in fields if spec.get("fields", {}).get(f, {}).get("value")]
