"""Integration test: ingest a synthetic LoRA-style PDF through the full pipeline."""

from pathlib import Path

import pytest

from atlasse_v2.pipeline import PaperPipeline


def _make_lora_pdf(path: Path) -> None:
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    text = (
        "ABSTRACT\n\n"
        "We study parameter-efficient fine-tuning of large language models.\n\n"
        "INTRODUCTION\n\n"
        "Fine-tuning all parameters is expensive. We address adaptation cost.\n\n"
        "METHOD\n\n"
        "We propose LoRA: Low-Rank Adaptation with rank decomposition matrices.\n\n"
        "The objective is cross-entropy loss for next-token prediction.\n\n"
        "EXPERIMENTS\n\n"
        "We evaluate on GLUE benchmark with RoBERTa base.\n\n"
        "Metrics include accuracy and F1 score.\n\n"
        "Figure 1: LoRA architecture diagram.\n\n"
        "Table 1: GLUE benchmark results."
    )
    page.insert_text((72, 72), text, fontsize=11)
    doc.save(path)
    doc.close()


@pytest.fixture
def lora_pdf(tmp_path):
    pdf_path = tmp_path / "2106.09685.pdf"
    _make_lora_pdf(pdf_path)
    return pdf_path


def test_ingest_lora_pdf_full_pipeline(lora_pdf, tmp_path):
    pipeline = PaperPipeline(data_dir=str(tmp_path))
    result = pipeline.ingest(lora_pdf, paper_id="2106.09685")

    assert result["paper_id"] == "2106.09685"
    assert result["chunk_count"] >= 6
    assert result["entity_count"] >= 3
    assert result["edge_count"] >= 1
    assert result["baseline_family"] in ("lora", "transformer", "unknown", "mlp")

    status = pipeline.get_status("2106.09685")
    assert status["parsed"]
    assert status["has_spec"]
    assert status["has_blueprint"]
    assert status["has_baseline"]
    assert status["has_reproduction_report"]

    repro = pipeline.get_reproduction_report("2106.09685")
    assert repro is not None
    assert repro.get("comparability_verdict")
    assert repro.get("level")

    spec = pipeline.get_spec("2106.09685")
    assert spec is not None
    assert spec["fields"]["dataset"]["value"]
    assert "GLUE" in spec["fields"]["dataset"]["value"]
    assert spec["fields"]["problem"]["value"] != spec["fields"]["dataset"]["value"]

    graph = pipeline.get_graph("2106.09685")
    assert len(graph.entities) >= 3
    assert len(graph.edges) >= 1

    baseline_path = tmp_path / "baselines" / "2106.09685" / "project" / "src" / "model" / "lora.py"
    assert baseline_path.exists()
    assert pipeline.get_blueprint("2106.09685")["data_flow"]
