"""Tests for research memory chunking."""

from tests.conftest import make_sample_document

from atlasse_v2.core.types import SectionType
from atlasse_v2.memory.research_memory import ResearchMemory


def test_build_creates_paragraph_chunks():
    doc = make_sample_document()
    memory = ResearchMemory("lora_sample").build_from_document(doc)
    assert len(memory.chunks) >= 4


def test_chunk_metadata_complete():
    doc = make_sample_document()
    memory = ResearchMemory("lora_sample").build_from_document(doc)
    for chunk in memory.chunks.values():
        assert chunk.chunk_id
        assert chunk.paragraph_id
        assert chunk.text.strip()
        assert chunk.section in (
            SectionType.ABSTRACT,
            SectionType.INTRODUCTION,
            SectionType.METHOD,
            SectionType.EXPERIMENTS,
        )


def test_get_by_sections():
    doc = make_sample_document()
    memory = ResearchMemory("lora_sample").build_from_document(doc)
    exp_chunks = memory.get_by_sections([SectionType.EXPERIMENTS])
    assert len(exp_chunks) >= 1
    assert all(c.section == SectionType.EXPERIMENTS for c in exp_chunks)


def test_save_and_load_roundtrip(tmp_path):
    doc = make_sample_document()
    memory = ResearchMemory("lora_sample").build_from_document(doc)
    memory.save(base_dir=str(tmp_path))
    loaded = ResearchMemory.load("lora_sample", base_dir=str(tmp_path))
    assert len(loaded.chunks) == len(memory.chunks)
