import os
import sys
import unittest
from importlib.util import find_spec

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from atlasse.knowledge_engine.retrieval.section_router import (
    detect_intent,
    expand_query,
    get_section_categories,
    section_matches_intent,
    target_categories_for_query,
)


class TestSectionRouter(unittest.TestCase):

    def test_detect_future_work_intent(self):
        intents = detect_intent("what future work is mentioned in conclusion")
        self.assertIn("future_work", intents)

    def test_detect_limitations_intent(self):
        intents = detect_intent("what are limitations of this method")
        self.assertIn("limitations", intents)

    def test_detect_dataset_intent(self):
        intents = detect_intent("what datasets are used in experiments")
        self.assertIn("dataset", intents)

    def test_conclusion_section_category(self):
        cats = get_section_categories("8 conclusion and future work")
        self.assertIn("conclusion", cats)

    def test_appendix_section_category(self):
        cats = get_section_categories("appendix c datasets")
        self.assertIn("appendix", cats)

    def test_future_work_targets_conclusion(self):
        cats = target_categories_for_query("what future work is suggested")
        self.assertIn("conclusion", cats)

    def test_dataset_targets_experiment_and_appendix(self):
        cats = target_categories_for_query("what datasets are used")
        self.assertIn("experiment", cats)
        self.assertIn("appendix", cats)

    def test_section_matches_intent(self):
        self.assertTrue(section_matches_intent("8 conclusion and future work", ["conclusion"]))
        self.assertFalse(section_matches_intent("2 problem statement", ["conclusion"]))

    def test_expand_limitations_query(self):
        subs = expand_query("what are limitations")
        self.assertTrue(len(subs) > 1)

    def test_work_does_not_false_positive_related(self):
        cats = get_section_categories("4 our method")
        self.assertNotIn("related_work", cats)


class TestVectorStorePersistence(unittest.TestCase):

    @unittest.skipIf(
        find_spec("numpy") is None or find_spec("faiss") is None,
        "Vector store persistence requires numpy and faiss",
    )
    def test_save_and_load(self):
        import shutil
        import tempfile
        import numpy as np
        from atlasse.knowledge_engine.paper_embeddings.vector_store import VectorStore

        tmp = tempfile.mkdtemp()
        try:
            store = VectorStore(4)
            emb = np.random.rand(3, 4).astype("float32")
            store.add(emb, [10, 20, 30])
            store.save(tmp)
            loaded = VectorStore.load(tmp)
            self.assertEqual(loaded.ids, [10, 20, 30])
            results = loaded.search(np.random.rand(1, 4), k=1)
            self.assertEqual(len(results), 1)
        finally:
            shutil.rmtree(tmp)


class TestKnowledgeGraph(unittest.TestCase):

    def test_build_and_query(self):
        from atlasse.knowledge_engine.graph.knowledge_graph import KnowledgeGraph

        chunks = {
            0: {"section": "abstract", "text": "We propose LoRA, a method cited by Hu et al., 2021."},
            1: {"section": "experiments", "text": "We evaluate on RoBERTa and GLUE benchmark."},
        }
        graph = KnowledgeGraph(paper_id="test")
        graph.build_from_chunks(chunks)
        summary = graph.summary()
        self.assertGreater(summary.get("entity", 0), 0)
        self.assertGreater(summary.get("chunk", 0), 0)


if __name__ == "__main__":
    unittest.main()
