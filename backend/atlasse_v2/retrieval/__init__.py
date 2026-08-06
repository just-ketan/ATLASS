"""Phase 4 — Multi-signal evidence ranking."""

__all__ = ["EvidenceRanker"]


def __getattr__(name: str):
    if name == "EvidenceRanker":
        from atlasse_v2.retrieval.evidence_ranker import EvidenceRanker
        return EvidenceRanker
    raise AttributeError(name)
