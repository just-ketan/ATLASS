"""Golden paper acceptance — synthetic PDFs and criteria checks."""

from __future__ import annotations

from pathlib import Path

from atlasse_v2.evaluation.benchmark import GOLDEN_PAPERS
from atlasse_v2.pipeline import PaperPipeline


GOLDEN_PROFILES = {
    "2106.09685": {
        "name": "LoRA",
        "family": "lora",
        "abstract": "Parameter-efficient fine-tuning with low-rank adaptation.",
        "method": "LoRA injects trainable low-rank matrices into attention layers.",
        "experiments": "We evaluate on GLUE benchmark with RoBERTa. Metrics: accuracy and F1.",
    },
    "1512.03385": {
        "name": "ResNet",
        "family": "cnn",
        "abstract": "Deep residual learning for image recognition.",
        "method": "ResNet uses convolution layers with skip connections and residual blocks.",
        "experiments": "ImageNet classification. Metrics: top-1 accuracy.",
    },
    "1706.03762": {
        "name": "Transformer",
        "family": "transformer",
        "abstract": "Attention is all you need for sequence transduction.",
        "method": "Transformer encoder-decoder with multi-head self-attention.",
        "experiments": "WMT translation benchmark. Metrics: BLEU score.",
    },
    "1810.04805": {
        "name": "BERT",
        "family": "transformer",
        "abstract": "Bidirectional encoder representations from transformers.",
        "method": "BERT uses transformer encoder with masked language modeling.",
        "experiments": "GLUE and SQuAD benchmarks. Metrics: accuracy and F1.",
    },
    "2103.00020": {
        "name": "CLIP",
        "family": "transformer",
        "abstract": "Learning transferable visual models from natural language supervision.",
        "method": "CLIP uses transformer-based image encoder and text encoder with contrastive loss.",
        "experiments": "Zero-shot ImageNet. Metrics: accuracy.",
    },
    "2304.02643": {
        "name": "SAM",
        "family": "transformer",
        "abstract": "Segment anything model for image segmentation.",
        "method": "SAM uses vision transformer and prompt encoder for segmentation.",
        "experiments": "SA-1B segmentation dataset. Metrics: mIoU.",
    },
    "2010.11929": {
        "name": "ViT",
        "family": "vision_transformer",
        "abstract": "An image is worth 16x16 words — vision transformer.",
        "method": "Vision Transformer applies transformer blocks to image patches.",
        "experiments": "ImageNet classification. Metrics: accuracy.",
    },
    "1506.02640": {
        "name": "YOLO",
        "family": "cnn",
        "abstract": "You only look once for real-time object detection.",
        "method": "YOLO uses convolutional network for single-shot detection.",
        "experiments": "PASCAL VOC and COCO. Metrics: mAP.",
    },
    "2104.14294": {
        "name": "DINO",
        "family": "vision_transformer",
        "abstract": "Self-supervised vision transformer training.",
        "method": "DINO uses self-distillation with no labels for ViT training.",
        "experiments": "ImageNet linear probe. Metrics: accuracy.",
    },
    "2112.10752": {
        "name": "Stable Diffusion",
        "family": "diffusion",
        "abstract": "Latent diffusion models for high-resolution image synthesis.",
        "method": "Stable Diffusion uses UNet denoising in latent space with diffusion process.",
        "experiments": "Image generation benchmarks. Metrics: FID score.",
    },
}


def make_golden_pdf(path: Path, profile: dict) -> None:
    import fitz
    path.parent.mkdir(parents=True, exist_ok=True)
    text = (
        f"ABSTRACT\n\n{profile['abstract']}\n\n"
        f"INTRODUCTION\n\nWe address limitations in prior work.\n\n"
        f"METHOD\n\n{profile['method']}\n\n"
        f"EXPERIMENTS\n\n{profile['experiments']}"
    )
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text, fontsize=11)
    doc.save(path)
    doc.close()


def run_acceptance(paper_id: str, data_dir: str, pdf_dir: Path) -> dict:
    profile = GOLDEN_PROFILES.get(paper_id)
    if profile is None:
        return {"paper_id": paper_id, "passed": False, "reason": "unknown_golden_paper"}

    pdf_path = pdf_dir / f"{paper_id}.pdf"
    make_golden_pdf(pdf_path, profile)

    pipeline = PaperPipeline(data_dir=data_dir)
    result = pipeline.ingest(pdf_path, paper_id=paper_id)
    spec = pipeline.get_spec(paper_id)
    blueprint = pipeline.get_blueprint(paper_id)
    baseline = pipeline.get_baseline(paper_id)
    expected_family = profile["family"]

    baseline_ok = False
    if baseline:
        actual = baseline.get("family")
        if baseline.get("supported"):
            baseline_ok = actual != "mlp" and (
                actual == expected_family
                or (expected_family in ("vision_transformer", "vit") and actual in ("vision_transformer", "transformer"))
                or (expected_family == "cnn" and actual in ("cnn", "transformer"))
            )
        else:
            baseline_ok = False

    checks = {
        "ingested": result.get("chunk_count", 0) > 0,
        "fields_distinct": (
            spec
            and spec["fields"].get("dataset", {}).get("value")
            != spec["fields"].get("problem", {}).get("value")
        ),
        "dataset_has_evidence": bool(spec and spec["fields"].get("dataset", {}).get("value")),
        "blueprint_has_modules": bool(
            blueprint and any(m.get("evidence_entity_id") for m in blueprint.get("modules", []))
        ),
        "baseline_ok": baseline_ok,
        "no_contradictory_missing": all(
            not (f.get("value") and f.get("missing"))
            for f in (spec or {}).get("fields", {}).values()
        ),
    }
    passed = all(checks.values())
    return {
        "paper_id": paper_id,
        "name": profile["name"],
        "expected_family": profile["family"],
        "actual_family": baseline.get("family") if baseline else None,
        "checks": checks,
        "passed": passed,
    }


def run_all_acceptance(data_dir: str, work_dir: Path) -> dict:
    work_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for entry in GOLDEN_PAPERS:
        pid = entry["id"]
        results.append(run_acceptance(pid, data_dir, work_dir))
    passed = sum(1 for r in results if r["passed"])
    return {
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "all_passed": passed == len(results),
        "papers": results,
    }
