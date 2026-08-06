"""Golden paper acceptance — all 10 synthetic profiles."""

from pathlib import Path

from atlasse_v2.evaluation.golden_acceptance import run_acceptance, run_all_acceptance


def test_lora_golden_acceptance(tmp_path):
    result = run_acceptance("2106.09685", str(tmp_path), tmp_path / "pdfs")
    assert result["passed"]
    assert result["checks"]["fields_distinct"]
    assert result["checks"]["baseline_ok"]


def test_all_golden_papers_acceptance(tmp_path):
    work = tmp_path / "golden_work"
    report = run_all_acceptance(str(tmp_path), work)
    assert report["total"] == 10
    assert report["passed"] == 10
    assert report["all_passed"]
    for paper in report["papers"]:
        assert paper["passed"], f"{paper['paper_id']} failed: {paper.get('checks')}"
