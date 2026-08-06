"""Canonical section classification for parsed documents."""

from atlasse_v2.core.types import SectionType

CANONICAL_SECTIONS = {
    "abstract": SectionType.ABSTRACT,
    "introduction": SectionType.INTRODUCTION,
    "related work": SectionType.RELATED_WORK,
    "method": SectionType.METHOD,
    "methodology": SectionType.METHOD,
    "architecture": SectionType.ARCHITECTURE,
    "experiments": SectionType.EXPERIMENTS,
    "experimental setup": SectionType.EXPERIMENTS,
    "implementation": SectionType.IMPLEMENTATION,
    "datasets": SectionType.DATASETS,
    "results": SectionType.RESULTS,
    "discussion": SectionType.DISCUSSION,
    "limitations": SectionType.LIMITATIONS,
    "future work": SectionType.FUTURE_WORK,
    "conclusion": SectionType.DISCUSSION,
    "appendix": SectionType.APPENDIX,
    "references": SectionType.REFERENCES,
}


def classify_section(title: str) -> SectionType:
    normalized = title.lower().strip()
    for keyword, section_type in CANONICAL_SECTIONS.items():
        if keyword in normalized:
            return section_type
    return SectionType.UNKNOWN
