"""Create a clearly labelled local paper-to-baseline demonstration workspace."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from atlasse.knowledge_engine.paper_understanding.baseline_project import BaselineProjectGenerator
from atlasse.knowledge_engine.paper_understanding.implementation_blueprint import ImplementationBlueprintGenerator
from atlasse.knowledge_engine.paper_understanding.system_spec import SystemSpecExtractor
from .models import PaperStatus


DEMO_PAPER_TITLE = "ATLASS Demonstration: Prototype Classifier"


class DemoWorkspaceSeeder:
    """Seed one transparent synthetic example; never represent it as a real paper."""

    def __init__(self, workspace):
        self.workspace = workspace

    def seed_paper(self, user_id: str) -> dict:
        existing = [
            paper for paper in self.workspace.list_library(user_id)
            if paper.metadata.get("demo_fixture") == "prototype_classifier"
        ]
        if existing:
            return existing[0]

        paper = self.workspace.store.add_paper(
            user_id=user_id,
            title=DEMO_PAPER_TITLE,
            source_type="demo",
            source_ref="prototype-classifier",
            demo_fixture="prototype_classifier",
            disclaimer="Synthetic ATLASS fixture; not a published research paper.",
        )
        json_path = self._write_processed_paper(paper.id)
        self.workspace.record_paper_processing_artifacts(user_id, paper.id, processed_json_path=json_path)
        self.workspace.mark_paper_status(user_id, paper.id, PaperStatus.READY, "Synthetic demo paper is ready.")

        spec = self._system_spec(paper.id)
        spec_path = SystemSpecExtractor(paper.id).save(spec)
        self.workspace.store.update_paper_metadata(user_id, paper.id, system_spec=spec, system_spec_path=spec_path)

        blueprint = ImplementationBlueprintGenerator(paper.id).generate(spec)
        blueprint["review"] = {
            "status": "approved",
            "notes": "Pre-approved synthetic fixture for the local demonstration.",
            "version": 1,
        }
        blueprint_path = ImplementationBlueprintGenerator(paper.id).save(blueprint)
        self.workspace.store.update_paper_metadata(
            user_id,
            paper.id,
            implementation_blueprint=blueprint,
            implementation_blueprint_path=blueprint_path,
        )

        manifest = BaselineProjectGenerator(paper.id).generate(blueprint)
        self.workspace.store.update_paper_metadata(
            user_id,
            paper.id,
            baseline_project=manifest,
            baseline_project_path=manifest["project_dir"],
        )
        return paper

    @staticmethod
    def _write_processed_paper(paper_id: str) -> str:
        output_dir = Path("data/demo_papers")
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{paper_id}.json"
        document = {
            "full_text": "Synthetic demonstration document created by ATLASS.",
            "sections": [
                {"title": "abstract", "level": 1, "text": "We present a prototype classifier for a binary supervised learning task. The system demonstrates ATLASS paper-to-baseline workflow; it is not a published result."},
                {"title": "method", "level": 1, "text": "The proposed baseline maps 32-dimensional feature vectors through a linear hidden layer with ReLU activation and a two-class output layer. Cross-entropy loss trains the classifier with Adam optimization."},
                {"title": "experiments", "level": 1, "text": "Experiments use deterministic synthetic two-class data. Each example contains a 32-dimensional input vector and a binary target. Accuracy is the evaluation metric. A five-epoch smoke run validates that training and evaluation execute."},
                {"title": "limitations", "level": 1, "text": "Synthetic metrics cannot be compared to an external paper benchmark. This artifact validates the implementation path only."},
            ],
        }
        path.write_text(json.dumps(document, indent=2))
        return str(path)

    @staticmethod
    def _system_spec(paper_id: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        citations = "[1] (synthetic demo § method, chunk 0)"

        def field(value, section):
            return {
                "value": value,
                "status": "confirmed",
                "confidence": 1.0,
                "citations": citations,
                "evidence": [{"paper_id": paper_id, "chunk_id": 0, "section": section, "score": 1.0, "source_query": "demo seed"}],
                "assumption": "Synthetic fixture for local UI demonstration.",
            }

        return {
            "schema_version": "1.0",
            "paper_id": paper_id,
            "generated_at": now,
            "generation": {"strategy": "demo_fixture", "note": "Not a published paper; all values are transparent fixture data."},
            "fields": {
                "problem_statement": field("Demonstrate a complete paper-to-baseline workflow.", "abstract"),
                "contribution": field("A simple deterministic prototype classifier.", "abstract"),
                "task_definition": field("Binary supervised classification.", "abstract"),
                "inputs": field("32-dimensional floating-point feature vector.", "method"),
                "outputs": field("Two-class prediction logits and a binary class label.", "method"),
                "model_components": field("Linear input layer, ReLU hidden layer, linear two-class output layer.", "method"),
                "objective": field("Cross-entropy loss optimized with Adam.", "method"),
                "training_setup": field("Five epochs, configurable seed, Adam learning rate 0.001.", "method"),
                "datasets": field("Deterministic synthetic two-class dataset.", "experiments"),
                "preprocessing": field("Generate class-centered feature vectors with Gaussian noise.", "experiments"),
                "metrics": field("Classification accuracy.", "experiments"),
                "baselines": field("No external baseline; this is an implementation smoke fixture.", "experiments"),
                "reported_results": field("Smoke execution validates training and evaluation only.", "experiments"),
                "limitations": field("Synthetic accuracy is not comparable to research-paper benchmarks.", "limitations"),
            },
            "review": {"status": "approved", "notes": "Synthetic fixture; pre-approved for the demo.", "version": 1},
        }
