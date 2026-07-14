"""Generate a constrained, runnable PyTorch baseline from an approved blueprint."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path


GENERATED_PROJECTS_DIR = "data/generated_projects"
SUPPORTED_FAMILIES = {"pytorch_supervised_model"}


class BaselineProjectGenerator:
    """Writes a safe local baseline, never executable code copied from paper text."""

    def __init__(self, paper_id: str, output_dir: str | Path = GENERATED_PROJECTS_DIR):
        self.paper_id = paper_id
        self.output_dir = Path(output_dir)

    def generate(self, blueprint: dict) -> dict:
        readiness = blueprint.get("readiness", {})
        family = readiness.get("supported_family")
        if blueprint.get("review", {}).get("status") != "approved":
            raise ValueError("Approve the implementation blueprint before generating code.")
        if readiness.get("status") != "ready_for_review":
            missing = ", ".join(readiness.get("missing_implementation_fields", []))
            raise ValueError(f"Blueprint has unresolved implementation fields: {missing}")
        if family not in SUPPORTED_FAMILIES:
            raise ValueError(
                f"{family} is not yet a runnable baseline family. "
                "ATLASS currently generates only pytorch_supervised_model baselines."
            )

        project_dir = self.output_dir / self.paper_id
        files = self._files(blueprint)
        for relative_path, content in files.items():
            path = project_dir / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)

        manifest = {
            "paper_id": self.paper_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": "ATLASS constrained PyTorch supervised baseline",
            "project_dir": str(project_dir),
            "entrypoint": "python -m src.train --config config/experiment.json",
            "smoke_command": "python -m src.train --config config/experiment.json --epochs 1",
            "scope": "Synthetic-data MLP baseline. This is an implementation scaffold, not a claim of faithful paper reproduction.",
            "source_mapping": {
                "src/model.py": ["model_components", "inputs", "outputs"],
                "src/data.py": ["datasets", "preprocessing", "inputs", "outputs"],
                "src/train.py": ["objective", "training_setup"],
                "src/evaluate.py": ["metrics", "reported_results"],
            },
            "blueprint_evidence": blueprint.get("evidence_map", {}),
            "assumptions": blueprint.get("assumptions", []),
        }
        manifest_path = project_dir / "atlass_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))
        return manifest

    def _files(self, blueprint: dict) -> dict[str, str]:
        return {
            "requirements.txt": "torch\nnumpy\n",
            "config/experiment.json": json.dumps({
                "seed": 7,
                "input_dim": 32,
                "hidden_dim": 64,
                "num_classes": 2,
                "train_samples": 512,
                "eval_samples": 128,
                "batch_size": 32,
                "epochs": 5,
                "learning_rate": 0.001,
            }, indent=2) + "\n",
            "src/__init__.py": "",
            "src/model.py": self._model_source(),
            "src/data.py": self._data_source(),
            "src/train.py": self._train_source(),
            "src/evaluate.py": self._evaluate_source(),
            "README.md": self._readme(blueprint),
        }

    @staticmethod
    def _model_source() -> str:
        return '''"""ATLASS generated baseline model."""
import torch.nn as nn


class BaselineClassifier(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, num_classes: int):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_classes),
        )

    def forward(self, features):
        return self.network(features)
'''

    @staticmethod
    def _data_source() -> str:
        return '''"""Deterministic synthetic data for the ATLASS smoke experiment."""
import torch
from torch.utils.data import DataLoader, TensorDataset


def make_loader(samples: int, input_dim: int, num_classes: int, batch_size: int, seed: int, shuffle: bool):
    generator = torch.Generator().manual_seed(seed)
    labels = torch.randint(num_classes, (samples,), generator=generator)
    centers = torch.randn(num_classes, input_dim, generator=generator)
    features = centers[labels] + 0.5 * torch.randn(samples, input_dim, generator=generator)
    return DataLoader(TensorDataset(features, labels), batch_size=batch_size, shuffle=shuffle)
'''

    @staticmethod
    def _train_source() -> str:
        return '''"""Train the ATLASS generated baseline."""
import argparse
import json
from pathlib import Path

import torch
from torch import nn

from src.data import make_loader
from src.model import BaselineClassifier


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/experiment.json")
    parser.add_argument("--epochs", type=int, default=None)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    epochs = args.epochs or config["epochs"]
    torch.manual_seed(config["seed"])
    loader = make_loader(config["train_samples"], config["input_dim"], config["num_classes"], config["batch_size"], config["seed"], True)
    model = BaselineClassifier(config["input_dim"], config["hidden_dim"], config["num_classes"])
    optimizer = torch.optim.Adam(model.parameters(), lr=config["learning_rate"])
    loss_fn = nn.CrossEntropyLoss()
    model.train()
    for _ in range(epochs):
        for features, labels in loader:
            optimizer.zero_grad()
            loss_fn(model(features), labels).backward()
            optimizer.step()
    Path("artifacts").mkdir(exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "config": config}, "artifacts/checkpoint.pt")
    print(json.dumps({"status": "trained", "epochs": epochs, "checkpoint": "artifacts/checkpoint.pt"}))


if __name__ == "__main__":
    main()
'''

    @staticmethod
    def _evaluate_source() -> str:
        return '''"""Evaluate the ATLASS generated baseline checkpoint."""
import argparse
import json
from pathlib import Path

import torch

from src.data import make_loader
from src.model import BaselineClassifier


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/experiment.json")
    parser.add_argument("--checkpoint", default="artifacts/checkpoint.pt")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    model = BaselineClassifier(config["input_dim"], config["hidden_dim"], config["num_classes"])
    model.load_state_dict(checkpoint["state_dict"])
    loader = make_loader(config["eval_samples"], config["input_dim"], config["num_classes"], config["batch_size"], config["seed"] + 1, False)
    correct = total = 0
    model.eval()
    with torch.no_grad():
        for features, labels in loader:
            correct += (model(features).argmax(dim=1) == labels).sum().item()
            total += labels.numel()
    result = {"accuracy": correct / total, "samples": total}
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/metrics.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
'''

    def _readme(self, blueprint: dict) -> str:
        fields = blueprint.get("evidence_map", {})
        return f"""# ATLASS Generated Baseline

This is a constrained PyTorch supervised-learning baseline generated from an approved ATLASS implementation blueprint. It uses synthetic data for a runnable smoke path and is **not** a faithful reproduction claim.

## Run

```bash
pip install -r requirements.txt
python -m src.train --config config/experiment.json
python -m src.evaluate --config config/experiment.json
```

## Paper-grounded design references

The source-to-paper mapping is in `atlass_manifest.json`. The extracted paper fields available at generation time were: {", ".join(sorted(fields))}.
"""
