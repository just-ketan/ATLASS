"""Generate a constrained, runnable PyTorch baseline from an approved blueprint."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re


GENERATED_PROJECTS_DIR = "data/generated_projects"
SUPPORTED_FAMILIES = {"pytorch_supervised_model", "pytorch_iris_classifier", "pytorch_vision_model"}


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
        files = self._files(blueprint, family)
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
            "run_command": "python -m src.train --config config/experiment.json && python -m src.evaluate --config config/experiment.json",
            "supported_family": family,
            "scope": self._scope(family),
            "source_mapping": {
                "src/model.py": ["model_components", "inputs", "outputs"],
                "src/data.py": ["datasets", "preprocessing", "inputs", "outputs"],
                "src/train.py": ["objective", "training_setup"],
                "src/evaluate.py": ["metrics", "reported_results"],
            },
            "blueprint_evidence": blueprint.get("evidence_map", {}),
            "assumptions": blueprint.get("assumptions", []),
            "data_provenance": self._data_provenance(family),
            "paper_reported_metrics": self._reported_metrics(blueprint),
        }
        manifest_path = project_dir / "atlass_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))
        return manifest

    def _files(self, blueprint: dict, family: str) -> dict[str, str]:
        if family == "pytorch_iris_classifier":
            return self._iris_files(blueprint)
        if family == "pytorch_vision_model":
            return self._vision_files(blueprint)
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
    def _scope(family: str) -> str:
        if family == "pytorch_iris_classifier":
            return (
                "Real-data Iris classification baseline using scikit-learn's packaged public UCI Iris dataset. "
                "This is paper-aligned only when the reviewed specification identifies Iris; architecture and training substitutions remain explicit."
            )
        if family == "pytorch_vision_model":
            return (
                "Real-data vision classification baseline using torchvision's CIFAR-10 dataset. "
                "This is paper-aligned only when the reviewed specification identifies CIFAR-10; architecture and training substitutions remain explicit."
            )
        return "Synthetic-data MLP baseline for development-only smoke testing; not a real-paper reproduction."

    @staticmethod
    def _data_provenance(family: str) -> dict:
        if family == "pytorch_iris_classifier":
            return {
                "kind": "real_public_data",
                "dataset": "UCI Iris",
                "provider": "scikit-learn.datasets.load_iris",
                "source_url": "https://archive.ics.uci.edu/dataset/53/iris",
                "split": "stratified 80/20 train/test split",
                "seed": 7,
                "synthetic": False,
            }
        if family == "pytorch_vision_model":
            return {
                "kind": "real_public_data",
                "dataset": "CIFAR-10",
                "provider": "torchvision.datasets.CIFAR10",
                "source_url": "https://www.cs.toronto.edu/~kriz/cifar.html",
                "split": "official train/test split",
                "seed": 7,
                "synthetic": False,
            }
        return {"kind": "synthetic", "dataset": "generated class-centred vectors", "synthetic": True}

    @staticmethod
    def _reported_metrics(blueprint: dict) -> dict[str, float]:
        """Extract an explicitly written decimal/percentage accuracy only; never invent a paper result."""
        text = " ".join(
            str(blueprint.get("evidence_map", {}).get(name, {}).get("evidence", ""))
            for name in ("reported_results", "metrics")
        )
        # Evidence records do not contain source text in every parser, so also inspect reviewed training detail.
        text += " " + " ".join(str(step.get("detail", "")) for step in blueprint.get("training_plan", []))
        match = re.search(r"(?:accuracy|acc)\s*(?:of|:|=|is)?\s*(0\.\d+|\d{1,3}(?:\.\d+)?%)", text, re.I)
        if not match:
            return {}
        value = match.group(1)
        return {"accuracy": float(value[:-1]) / 100 if value.endswith("%") else float(value)}

    def _iris_files(self, blueprint: dict) -> dict[str, str]:
        return {
            "requirements.txt": "torch\nnumpy\nscikit-learn\n",
            "config/experiment.json": json.dumps({
                "seed": 7,
                "dataset": "uci_iris",
                "dataset_provider": "sklearn.datasets.load_iris",
                "split": "stratified_80_20",
                "input_dim": 4,
                "hidden_dim": 16,
                "num_classes": 3,
                "batch_size": 16,
                "epochs": 40,
                "learning_rate": 0.01,
                "metric": "accuracy",
            }, indent=2) + "\n",
            "src/__init__.py": "",
            "src/model.py": self._model_source(),
            "src/data.py": self._iris_data_source(),
            "src/train.py": self._iris_train_source(),
            "src/evaluate.py": self._iris_evaluate_source(),
            "README.md": self._iris_readme(blueprint),
        }

    def _vision_files(self, blueprint: dict) -> dict[str, str]:
        return {
            "requirements.txt": "torch\ntorchvision\nnumpy\n",
            "config/experiment.json": json.dumps({
                "seed": 7,
                "dataset": "cifar10",
                "dataset_provider": "torchvision.datasets.CIFAR10",
                "split": "official_train_test",
                "num_classes": 10,
                "batch_size": 64,
                "epochs": 10,
                "learning_rate": 0.001,
                "metric": "accuracy",
            }, indent=2) + "\n",
            "src/__init__.py": "",
            "src/model.py": self._vision_model_source(),
            "src/data.py": self._vision_data_source(),
            "src/train.py": self._vision_train_source(),
            "src/evaluate.py": self._vision_evaluate_source(),
            "README.md": self._vision_readme(blueprint),
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
    def _iris_data_source() -> str:
        return '''"""Real public UCI Iris data loaded from scikit-learn's packaged dataset."""
import torch
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, TensorDataset


def make_loaders(batch_size: int, seed: int):
    iris = load_iris()
    features = iris.data.astype("float32")
    labels = iris.target.astype("int64")
    x_train, x_test, y_train, y_test = train_test_split(
        features, labels, test_size=0.2, random_state=seed, stratify=labels
    )
    train = TensorDataset(torch.tensor(x_train), torch.tensor(y_train))
    test = TensorDataset(torch.tensor(x_test), torch.tensor(y_test))
    return (
        DataLoader(train, batch_size=batch_size, shuffle=True),
        DataLoader(test, batch_size=batch_size, shuffle=False),
    )
'''

    @staticmethod
    def _iris_train_source() -> str:
        return '''"""Train the reviewed Iris baseline on real public data."""
import argparse
import json
from pathlib import Path

import torch
from torch import nn

from src.data import make_loaders
from src.model import BaselineClassifier


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/experiment.json")
    parser.add_argument("--epochs", type=int, default=None)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    torch.manual_seed(config["seed"])
    train_loader, _ = make_loaders(config["batch_size"], config["seed"])
    model = BaselineClassifier(config["input_dim"], config["hidden_dim"], config["num_classes"])
    optimizer = torch.optim.Adam(model.parameters(), lr=config["learning_rate"])
    loss_fn = nn.CrossEntropyLoss()
    epochs = args.epochs or config["epochs"]
    model.train()
    for _ in range(epochs):
        for features, labels in train_loader:
            optimizer.zero_grad()
            loss_fn(model(features), labels).backward()
            optimizer.step()
    Path("artifacts").mkdir(exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "config": config}, "artifacts/checkpoint.pt")
    print(json.dumps({"status": "trained", "epochs": epochs, "checkpoint": "artifacts/checkpoint.pt", "dataset": config["dataset"]}))


if __name__ == "__main__":
    main()
'''

    @staticmethod
    def _iris_evaluate_source() -> str:
        return '''"""Evaluate the reviewed Iris baseline on the held-out real-data split."""
import argparse
import json
from pathlib import Path

import torch

from src.data import make_loaders
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
    _, loader = make_loaders(config["batch_size"], config["seed"])
    correct = total = 0
    model.eval()
    with torch.no_grad():
        for features, labels in loader:
            correct += (model(features).argmax(dim=1) == labels).sum().item()
            total += labels.numel()
    result = {"accuracy": correct / total, "samples": total, "dataset": config["dataset"]}
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/metrics.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
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

    def _iris_readme(self, blueprint: dict) -> str:
        fields = blueprint.get("evidence_map", {})
        return f"""# ATLASS Generated Real-Data Baseline

This project trains a PyTorch classifier on the real public UCI Iris dataset loaded by `scikit-learn`. It is generated only for an approved blueprint whose reviewed dataset field identifies Iris. The exact split, seed, and dependencies are recorded in `config/experiment.json` and `atlass_manifest.json`.

## Run

```bash
pip install -r requirements.txt
python -m src.train --config config/experiment.json
python -m src.evaluate --config config/experiment.json
```

## Paper-grounded design references

The source-to-paper mapping is in `atlass_manifest.json`. Extracted fields at generation time: {", ".join(sorted(fields))}.
"""

    @staticmethod
    def _vision_model_source() -> str:
        return '''"""ATLASS generated vision baseline model."""
import torch.nn as nn

class BaselineClassifier(nn.Module):
    def __init__(self, num_classes: int = 10):
        super().__init__()
        self.network = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Flatten(),
            nn.Linear(32 * 8 * 8, 128),
            nn.ReLU(),
            nn.Linear(128, num_classes),
        )

    def forward(self, features):
        return self.network(features)
'''

    @staticmethod
    def _vision_data_source() -> str:
        return '''"""Real public CIFAR-10 data loaded from torchvision."""
import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader

def make_loaders(batch_size: int, seed: int):
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])
    train = datasets.CIFAR10(root='./data', train=True, download=True, transform=transform)
    test = datasets.CIFAR10(root='./data', train=False, download=True, transform=transform)
    return (
        DataLoader(train, batch_size=batch_size, shuffle=True),
        DataLoader(test, batch_size=batch_size, shuffle=False),
    )
'''

    @staticmethod
    def _vision_train_source() -> str:
        return '''"""Train the reviewed vision baseline on real public data."""
import argparse
import json
from pathlib import Path

import torch
from torch import nn

from src.data import make_loaders
from src.model import BaselineClassifier

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/experiment.json")
    parser.add_argument("--epochs", type=int, default=None)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    torch.manual_seed(config["seed"])
    train_loader, _ = make_loaders(config["batch_size"], config["seed"])
    model = BaselineClassifier(config["num_classes"])
    optimizer = torch.optim.Adam(model.parameters(), lr=config["learning_rate"])
    loss_fn = nn.CrossEntropyLoss()
    epochs = args.epochs or config["epochs"]
    model.train()
    for _ in range(epochs):
        for features, labels in train_loader:
            optimizer.zero_grad()
            loss_fn(model(features), labels).backward()
            optimizer.step()
    Path("artifacts").mkdir(exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "config": config}, "artifacts/checkpoint.pt")
    print(json.dumps({"status": "trained", "epochs": epochs, "checkpoint": "artifacts/checkpoint.pt", "dataset": config["dataset"]}))

if __name__ == "__main__":
    main()
'''

    @staticmethod
    def _vision_evaluate_source() -> str:
        return '''"""Evaluate the reviewed vision baseline on the held-out real-data split."""
import argparse
import json
from pathlib import Path

import torch

from src.data import make_loaders
from src.model import BaselineClassifier

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/experiment.json")
    parser.add_argument("--checkpoint", default="artifacts/checkpoint.pt")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    model = BaselineClassifier(config["num_classes"])
    model.load_state_dict(checkpoint["state_dict"])
    _, loader = make_loaders(config["batch_size"], config["seed"])
    correct = total = 0
    model.eval()
    with torch.no_grad():
        for features, labels in loader:
            correct += (model(features).argmax(dim=1) == labels).sum().item()
            total += labels.numel()
    result = {"accuracy": correct / total, "samples": total, "dataset": config["dataset"]}
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/metrics.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result))

if __name__ == "__main__":
    main()
'''

    def _vision_readme(self, blueprint: dict) -> str:
        fields = blueprint.get("evidence_map", {})
        return f"""# ATLASS Generated Real-Data Vision Baseline

This project trains a PyTorch classifier on the real public CIFAR-10 dataset loaded by `torchvision`. It is generated only for an approved blueprint whose reviewed dataset field identifies vision datasets. The exact split, seed, and dependencies are recorded in `config/experiment.json` and `atlass_manifest.json`.

## Run

```bash
pip install -r requirements.txt
python -m src.train --config config/experiment.json
python -m src.evaluate --config config/experiment.json
```

## Paper-grounded design references

The source-to-paper mapping is in `atlass_manifest.json`. Extracted fields at generation time: {", ".join(sorted(fields))}.
"""
