"""Tests for ATLASS v2 parsing and section classification."""

from atlasse_v2.core.types import SectionType
from atlasse_v2.parsing.document_parser import DocumentParser
from atlasse_v2.parsing.section_tree import SectionTreeBuilder


def test_classify_abstract():
    assert DocumentParser.classify_section("Abstract") == SectionType.ABSTRACT


def test_classify_introduction():
    assert DocumentParser.classify_section("1 Introduction") == SectionType.INTRODUCTION


def test_classify_experiments():
    assert DocumentParser.classify_section("4 Experiments") == SectionType.EXPERIMENTS


def test_classify_datasets():
    assert DocumentParser.classify_section("3.2 Datasets") == SectionType.DATASETS


def test_classify_unknown():
    assert DocumentParser.classify_section("Acknowledgements") == SectionType.UNKNOWN


def test_section_tree_assigns_unique_paragraph_ids():
    pages = [{"page": 1, "text": "ABSTRACT\n\nWe study adaptation.\n\nINTRODUCTION\n\nWe address fine-tuning cost."}]
    builder = SectionTreeBuilder()
    sections = builder.build(pages)
    paragraphs = builder.collect_paragraphs(sections)
    assert len(paragraphs) >= 2
    assert len(set(paragraphs.keys())) == len(paragraphs)


def test_backend_chain_defaults():
    parser = DocumentParser()
    assert "pymupdf" in parser.backend_chain
    assert "pdfplumber" in parser.backend_chain

