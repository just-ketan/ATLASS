"""Parser backend protocol."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class ParserBackend(Protocol):
    def extract_pages(self, pdf_path: Path) -> list[dict]: ...
