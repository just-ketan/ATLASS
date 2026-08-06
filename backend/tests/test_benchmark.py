"""Tests for benchmark harness and score tracking."""

from atlasse_v2.evaluation.benchmark import BenchmarkSuite
from atlasse_v2.evaluation.fixtures import make_lora_sample_document
from atlasse_v2.evaluation.score_store import ScoreStore


def test_extraction_eval_passes_on_sample(tmp_path):
    store = ScoreStore(path=str(tmp_path / "scores.json"))
    suite = BenchmarkSuite(score_store=store)
    result = suite.run_extraction_eval(make_lora_sample_document)
    assert result["dataset_extraction_ok"]
    assert result["problem_extraction_ok"]
    assert result["fields_distinct"]
    assert result["hallucination_rate"] == 0.0
    assert result["explicit_field_reuse_rate"] >= 0
    assert result["passed"]


def test_smoke_regression_records_scores(tmp_path):
    store = ScoreStore(path=str(tmp_path / "scores.json"))
    suite = BenchmarkSuite(score_store=store)
    result = suite.run_smoke_regression(make_lora_sample_document)
    assert result["passed"]
    assert result["elapsed_seconds"] < 60
    latest = store.latest()
    assert latest is not None
    assert latest["suite"] == "smoke"
