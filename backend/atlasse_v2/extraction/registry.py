"""Registry of all dedicated extractors."""

from __future__ import annotations

from atlasse_v2.extraction.extractors.architecture import ArchitectureExtractor
from atlasse_v2.extraction.extractors.baseline import BaselineExtractor
from atlasse_v2.extraction.extractors.contribution import ContributionExtractor
from atlasse_v2.extraction.extractors.dataset import DatasetExtractor
from atlasse_v2.extraction.extractors.evaluation import EvaluationExtractor
from atlasse_v2.extraction.extractors.future_work import FutureWorkExtractor
from atlasse_v2.extraction.extractors.limitation import LimitationExtractor
from atlasse_v2.extraction.extractors.loss import LossExtractor
from atlasse_v2.extraction.extractors.method import MethodExtractor
from atlasse_v2.extraction.extractors.metric import MetricExtractor
from atlasse_v2.extraction.extractors.problem import ProblemExtractor
from atlasse_v2.extraction.extractors.task import TaskExtractor
from atlasse_v2.extraction.extractors.training import TrainingExtractor

EXTRACTORS = {
    "problem": ProblemExtractor,
    "contribution": ContributionExtractor,
    "task": TaskExtractor,
    "dataset": DatasetExtractor,
    "metric": MetricExtractor,
    "method": MethodExtractor,
    "architecture": ArchitectureExtractor,
    "loss": LossExtractor,
    "training": TrainingExtractor,
    "evaluation": EvaluationExtractor,
    "baseline": BaselineExtractor,
    "limitation": LimitationExtractor,
    "future_work": FutureWorkExtractor,
}


def get_extractor(name: str, retriever, llm_client=None):
    cls = EXTRACTORS.get(name)
    if cls is None:
        raise KeyError(f"Unknown extractor: {name}")
    return cls(retriever, llm_client)
