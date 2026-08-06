"""Family-specific baseline template sources."""

LORA_PY = '''"""LoRA adapter layers — generated from paper evidence."""
import torch
import torch.nn as nn


class LoRALayer(nn.Module):
    """Low-rank adaptation layer. Rank and alpha from spec or assumptions."""

    def __init__(self, in_features: int, out_features: int, rank: int = {rank}, alpha: float = {alpha}):
        super().__init__()
        self.rank = rank
        self.alpha = alpha
        self.lora_a = nn.Linear(in_features, rank, bias=False)
        self.lora_b = nn.Linear(rank, out_features, bias=False)
        nn.init.kaiming_uniform_(self.lora_a.weight)
        nn.init.zeros_(self.lora_b.weight)

    def forward(self, x: torch.Tensor, base_out: torch.Tensor) -> torch.Tensor:
        return base_out + (self.alpha / self.rank) * self.lora_b(self.lora_a(x))
'''

BASE_MODEL_PY = '''"""Base model wrapper — pretrained backbone from paper evidence."""
from transformers import AutoModel


def load_base_model(model_name: str = "{model_name}"):
    return AutoModel.from_pretrained(model_name)
'''

TRANSFORMER_PY = '''"""Transformer stack — generated from architecture evidence."""
import torch.nn as nn


class TransformerBlock(nn.Module):
    def __init__(self, d_model: int = {d_model}, n_heads: int = {n_heads}):
        super().__init__()
        self.attention = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        self.ff = nn.Sequential(
            nn.Linear(d_model, 4 * d_model),
            nn.GELU(),
            nn.Linear(4 * d_model, d_model),
        )
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)

    def forward(self, x):
        attn_out, _ = self.attention(x, x, x)
        x = self.norm1(x + attn_out)
        x = self.norm2(x + self.ff(x))
        return x
'''

ATTENTION_PY = '''"""Attention module — evidence-linked stub."""
import torch.nn as nn


class Attention(nn.Module):
    def __init__(self, d_model: int = {d_model}, n_heads: int = {n_heads}):
        super().__init__()
        self.attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)

    def forward(self, x):
        out, _ = self.attn(x, x, x)
        return out
'''

TRAIN_PY = '''"""Training loop — hyperparameters from spec or labeled assumptions."""
import torch


def train_epoch(model, dataloader, optimizer, loss_fn, device="cpu"):
    model.train()
    total_loss = 0.0
    for batch in dataloader:
        optimizer.zero_grad()
        outputs = model(batch["input_ids"])
        loss = loss_fn(outputs, batch["labels"])
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / max(len(dataloader), 1)
'''

EVALUATE_PY = '''"""Evaluation — metrics from paper evidence."""
import torch


def evaluate(model, dataloader, metric_fn, device="cpu"):
    model.eval()
    scores = []
    with torch.no_grad():
        for batch in dataloader:
            outputs = model(batch["input_ids"])
            scores.append(metric_fn(outputs, batch["labels"]))
    return sum(scores) / max(len(scores), 1)
'''

DATASET_PY = '''"""Dataset adapter — dataset from paper experiments section."""
from torch.utils.data import Dataset


class PaperDataset(Dataset):
    def __init__(self, dataset_name: str = "{dataset_name}"):
        self.dataset_name = dataset_name

    def __len__(self):
        return 0  # Replace with real public dataset loader

    def __getitem__(self, idx):
        raise NotImplementedError("Wire public dataset: " + self.dataset_name)
'''

CONFIG_YAML = '''# Generated baseline config — values from spec or assumptions
model_name: "{model_name}"
dataset: "{dataset_name}"
learning_rate: {learning_rate}
batch_size: {batch_size}
epochs: {epochs}
lora_rank: {rank}
lora_alpha: {alpha}
'''

README_MD = '''# ATLASS v2 Generated Baseline

Paper ID: {paper_id}
Model family: {family}

## Evidence
{evidence_note}

## Assumptions
{assumptions}

## Run
```bash
pip install -r requirements.txt
python src/train.py
python src/evaluate.py
```
'''

TEMPLATES = {
    "lora": LORA_PY,
    "base_model": BASE_MODEL_PY,
    "transformer": TRANSFORMER_PY,
    "attention": ATTENTION_PY,
    "train": TRAIN_PY,
    "evaluate": EVALUATE_PY,
    "dataset": DATASET_PY,
    "config": CONFIG_YAML,
    "readme": README_MD,
}
