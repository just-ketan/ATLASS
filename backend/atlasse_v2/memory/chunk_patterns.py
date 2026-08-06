"""Extract structured chunks (captions, tables, equations) from section text."""

from __future__ import annotations

import re

FIGURE_CAPTION = re.compile(
    r"(?:Figure|Fig\.?)\s+(\d+)[:\.]?\s*(.+?)(?=(?:Figure|Fig\.?|Table|Tab\.?)\s+\d+|$)",
    re.IGNORECASE | re.DOTALL,
)
TABLE_BLOCK = re.compile(
    r"(?:Table|Tab\.?)\s+(\d+)[:\.]?\s*(.+?)(?=(?:Figure|Fig\.?|Table|Tab\.?)\s+\d+|$)",
    re.IGNORECASE | re.DOTALL,
)
EQUATION_LINE = re.compile(r"^\s*([A-Za-z].*?=.+)$", re.MULTILINE)
ALGORITHM_BLOCK = re.compile(
    r"(?:Algorithm\s+\d+)[:\.]?\s*(.+?)(?=(?:Algorithm\s+\d+|Figure|Table|$))",
    re.IGNORECASE | re.DOTALL,
)


def extract_algorithms(text: str) -> list[str]:
    return [m.group(1).strip()[:500] for m in ALGORITHM_BLOCK.finditer(text)]


def extract_captions(text: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2).strip()[:500]) for m in FIGURE_CAPTION.finditer(text)]


def extract_tables(text: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2).strip()[:500]) for m in TABLE_BLOCK.finditer(text)]


def extract_equations(text: str) -> list[str]:
    lines = []
    for m in EQUATION_LINE.finditer(text):
        line = m.group(1).strip()
        if len(line) > 10 and len(line) < 300:
            lines.append(line)
    return lines[:5]
