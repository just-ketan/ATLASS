"""Blueprint version comparison."""

from __future__ import annotations


def diff_blueprints(old: dict, new: dict) -> dict:
    old_modules = {m.get("file"): m for m in old.get("modules", []) if m.get("file")}
    new_modules = {m.get("file"): m for m in new.get("modules", []) if m.get("file")}

    added = [new_modules[k] for k in new_modules if k not in old_modules]
    removed = [old_modules[k] for k in old_modules if k not in new_modules]
    changed = []
    for k in old_modules:
        if k in new_modules and old_modules[k] != new_modules[k]:
            changed.append({"file": k, "old": old_modules[k], "new": new_modules[k]})

    return {
        "paper_id": new.get("paper_id"),
        "old_version": old.get("version"),
        "new_version": new.get("version"),
        "modules_added": added,
        "modules_removed": removed,
        "modules_changed": changed,
        "flows_changed": {
            "data_flow": old.get("data_flow") != new.get("data_flow"),
            "training_flow": old.get("training_flow") != new.get("training_flow"),
            "evaluation_flow": old.get("evaluation_flow") != new.get("evaluation_flow"),
            "inference_flow": old.get("inference_flow") != new.get("inference_flow"),
        },
    }
