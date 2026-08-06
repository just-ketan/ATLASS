"""Synthetic documents for benchmark regression (not acceptance evidence)."""

from atlasse_v2.core.models import ParsedDocument
from atlasse_v2.core.types import SectionType
from atlasse_v2.parsing.section_tree import SectionTreeBuilder


def make_lora_sample_document() -> ParsedDocument:
    pages = [{
        "page": 1,
        "text": (
            "ABSTRACT\n\nLarge language models are expensive to fine-tune.\n\n"
            "INTRODUCTION\n\nWe address the problem of parameter-efficient adaptation.\n\n"
            "METHOD\n\nWe propose Low-Rank Adaptation (LoRA) which injects trainable rank decomposition matrices.\n\n"
            "The loss function is cross-entropy over next-token prediction.\n\n"
            "EXPERIMENTS\n\nWe evaluate on GLUE benchmark using RoBERTa base.\n\n"
            "Metrics include accuracy and F1 score."
        ),
    }]
    builder = SectionTreeBuilder()
    section_tree = builder.build(pages)
    paragraphs = builder.collect_paragraphs(section_tree)
    return ParsedDocument(
        paper_id="lora_sample",
        title="LoRA: Low-Rank Adaptation",
        section_tree=section_tree,
        paragraphs=paragraphs,
    )
