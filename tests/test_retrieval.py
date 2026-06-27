import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from atlasse.knowledge_engine.observability.eval_harness import EvalHarness, GOLDEN_QUERIES
from atlasse.knowledge_engine.orchestration.evidence_merger import MergedEvidence, Evidence


class TestEvidenceMerger(unittest.TestCase):

    def test_deduplication(self):
        merged = MergedEvidence()
        merged.items = [
            Evidence("Same sentence here.", 0.9, 1, "p1", "abstract"),
            Evidence("Same sentence here.", 0.8, 2, "p1", "method"),
            Evidence("Different sentence here.", 0.7, 3, "p1", "method"),
        ]
        result = merged.merge()
        self.assertEqual(len(result), 2)

    def test_citations_format(self):
        merged = MergedEvidence()
        merged.items = [
            Evidence("LoRA is efficient.", 0.9, 0, "2106.09685", "abstract"),
        ]
        cites = merged.format_citations()
        self.assertIn("2106.09685", cites)
        self.assertIn("chunk 0", cites)


class TestGoldenQueries(unittest.TestCase):

    def test_golden_queries_defined(self):
        self.assertIn("2106.09685", GOLDEN_QUERIES)
        self.assertGreaterEqual(len(GOLDEN_QUERIES["2106.09685"]), 4)


if __name__ == "__main__":
    unittest.main()
