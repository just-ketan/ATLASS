"""Tests for ATLASS v2 parsing and section classification."""

from atlasse_v2.core.types import SectionType
from atlasse_v2.parsing.document_parser import DocumentParser


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
