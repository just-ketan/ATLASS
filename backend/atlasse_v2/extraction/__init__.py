"""Phase 3 — Dedicated research information extractors."""

from .base_extractor import BaseExtractor
from .registry import EXTRACTORS, get_extractor

__all__ = ["BaseExtractor", "EXTRACTORS", "get_extractor"]
