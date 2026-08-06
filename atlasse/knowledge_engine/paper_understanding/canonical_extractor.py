from pathlib import Path
import json

from .concept_extractor import ConceptExtractor
from .structured_extractor import StructuredExtractor


class CanonicalExtractor:
    """Consolidates concept and structured extraction into a single canonical knowledge artifact."""

    ARTIFACT_DIR = "data/knowledge_artifacts"

    def __init__(self, paper_id: str | None = None, artifact_dir: str | Path | None = None):
        self.paper_id = paper_id
        self.artifact_dir = Path(artifact_dir or self.ARTIFACT_DIR)
        self.concept_extractor = ConceptExtractor(paper_id=paper_id, artifact_dir=self.artifact_dir)

    def extract(self, json_path: str | Path, chunks: list[dict] | None = None) -> dict:
        # 1. Extract concepts, entities, and relations
        if chunks is None:
            concept_artifact = self.concept_extractor.extract_from_json(json_path)
        else:
            concept_artifact = self.concept_extractor.extract_from_chunks(chunks)

        # 2. Extract structured fields
        structured_extractor = StructuredExtractor(json_path=json_path, paper_id=self.paper_id)
        structured_artifact = structured_extractor.extract()

        # 3. Consolidate into one canonical artifact
        return {
            "paper_id": self.paper_id,
            "concepts": concept_artifact.get("concepts", []),
            "entities": concept_artifact.get("entities", []),
            "relations": concept_artifact.get("relations", []),
            "summary": concept_artifact.get("summary", {}),
            "structured_fields": structured_artifact.get("fields", {}),
            "structured_provenance": structured_artifact.get("provenance", {}),
        }

    def save(self, artifact: dict, directory: str | Path | None = None) -> str:
        paper_id = artifact.get("paper_id") or self.paper_id or "default"
        output_dir = Path(directory) if directory else self.artifact_dir / paper_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / "knowledge.json"
        with open(output_path, "w") as f:
            json.dump(artifact, f, indent=2)
        return str(output_path)
