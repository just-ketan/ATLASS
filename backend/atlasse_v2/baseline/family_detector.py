"""Detect model family from research graph and specification."""

from __future__ import annotations

from atlasse_v2.core.types import ModelFamily
from atlasse_v2.graph.semantic_graph import SemanticPaperGraph


FAMILY_KEYWORDS: dict[ModelFamily, list[str]] = {
    ModelFamily.TRANSFORMER: ["transformer", "self-attention", "multi-head attention"],
    ModelFamily.LORA: ["lora", "low-rank adaptation", "low rank"],
    ModelFamily.PEFT: ["peft", "parameter efficient", "adapter"],
    ModelFamily.CNN: ["convolution", "resnet", "cnn"],
    ModelFamily.VIT: ["vision transformer", "vit"],
    ModelFamily.DIFFUSION: ["diffusion", "denoising", "stable diffusion"],
    ModelFamily.GAN: ["gan", "generative adversarial"],
    ModelFamily.VAE: ["vae", "variational autoencoder"],
    ModelFamily.GNN: ["graph neural", "gnn", "message passing"],
    ModelFamily.RNN: ["rnn", "recurrent"],
    ModelFamily.LSTM: ["lstm"],
    ModelFamily.MLP: ["mlp", "multilayer perceptron", "fully connected"],
    ModelFamily.UNET: ["unet", "u-net"],
    ModelFamily.SEQ2SEQ: ["seq2seq", "sequence to sequence"],
    ModelFamily.ENCODER_DECODER: ["encoder-decoder", "encoder decoder"],
    ModelFamily.NERF: ["nerf", "neural radiance"],
}


class FamilyDetector:
    def __init__(self, graph: SemanticPaperGraph):
        self.graph = graph

    def detect(self) -> tuple[ModelFamily, float]:
        combined_text = " ".join(
            e.text.lower() for e in self.graph.entities.values()
        )
        best_family = ModelFamily.UNKNOWN
        best_score = 0.0
        for family, keywords in FAMILY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined_text)
            if score > best_score:
                best_score = score
                best_family = family
        confidence = min(best_score / 3, 1.0) if best_score > 0 else 0.0
        return best_family, confidence
