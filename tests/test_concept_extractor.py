import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from atlasse.knowledge_engine.paper_understanding import ConceptExtractor


class TestConceptExtractor(unittest.TestCase):

    def test_extracts_concepts_entities_and_provenance(self):
        chunks = [
            {
                "id": 0,
                "section": "abstract",
                "text": "LoRA is a fine-tuning method for Transformer language model adaptation.",
            },
            {
                "id": 1,
                "section": "experiments",
                "text": "We evaluate LoRA on GLUE and RoBERTa benchmarks following Hu et al., 2021.",
            },
        ]

        artifact = ConceptExtractor(paper_id="paper_1").extract_from_chunks(chunks)

        concept_labels = {item["label"] for item in artifact["concepts"]}
        entity_labels = {item["label"] for item in artifact["entities"]}

        self.assertEqual(artifact["paper_id"], "paper_1")
        self.assertIn("fine-tuning", concept_labels)
        self.assertIn("transformer", concept_labels)
        self.assertIn("lora", entity_labels)
        self.assertIn("glue", entity_labels)
        self.assertGreaterEqual(artifact["summary"]["sections"], 2)
        lora = next(item for item in artifact["entities"] if item["label"] == "lora")
        self.assertEqual(lora["frequency"], 2)
        self.assertEqual(lora["chunk_ids"], [0, 1])
        relations = {(item["source"], item["relation"], item["target"]) for item in artifact["relations"]}
        self.assertIn(("lora", "evaluated_on", "glue"), relations)
        self.assertIn(("lora", "supported_by_citation", "hu et al., 2021"), relations)

    def test_extracts_from_processed_json_and_saves_artifact(self):
        paper_json = {
            "sections": [
                {
                    "title": "method",
                    "text": "The encoder uses attention and retrieval for model grounding.",
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, "paper.json")
            with open(json_path, "w") as f:
                json.dump(paper_json, f)

            extractor = ConceptExtractor(paper_id="paper_2", artifact_dir=tmpdir)
            artifact = extractor.extract_from_json(json_path)
            output_path = extractor.save(artifact)

            self.assertTrue(os.path.exists(output_path))
            loaded = ConceptExtractor.load(os.path.dirname(output_path))
            self.assertEqual(loaded["paper_id"], "paper_2")
            self.assertIn("attention", {item["label"] for item in loaded["concepts"]})


if __name__ == "__main__":
    unittest.main()
