import os
import sys
import json
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from atlasse.platform.models import PaperStatus
from atlasse.platform.service import ResearchWorkspaceService
from atlasse.platform.store import NotFoundError


class TestResearchWorkspaceService(unittest.TestCase):

    def setUp(self):
        self.service = ResearchWorkspaceService()
        self.user = self.service.login_with_oauth(
            provider="github",
            subject="user-123",
            email="researcher@example.com",
            name="Researcher",
        )

    def test_oauth_login_is_idempotent(self):
        second_login = self.service.login_with_oauth(
            provider="github",
            subject="user-123",
            email="researcher@example.com",
            name="Researcher Updated",
        )
        self.assertEqual(self.user.id, second_login.id)
        self.assertEqual(second_login.name, "Researcher Updated")

    def test_dashboard_counts_user_workspace(self):
        paper = self.service.add_arxiv_paper(self.user.id, "2106.09685", "LoRA")
        self.service.mark_paper_status(self.user.id, paper.id, PaperStatus.READY)
        project = self.service.create_project(self.user.id, "Parameter efficient tuning")
        self.service.attach_paper_to_project(self.user.id, project.id, paper.id)
        self.service.add_note(self.user.id, "Idea", "Compare LoRA with QLoRA.", project_id=project.id)
        conversation = self.service.start_conversation(self.user.id, "LoRA questions", project_id=project.id)
        self.service.add_message(self.user.id, conversation.id, "user", "Remember this angle.", remember=True)
        self.service.add_citation(self.user.id, paper.id, "Hu et al. (2021). LoRA.")

        dashboard = self.service.dashboard(self.user.id)

        self.assertEqual(dashboard.papers, 1)
        self.assertEqual(dashboard.ready_papers, 1)
        self.assertEqual(dashboard.projects, 1)
        self.assertEqual(dashboard.notes, 1)
        self.assertEqual(dashboard.conversations, 1)
        self.assertEqual(dashboard.memories, 1)
        self.assertEqual(dashboard.citations, 1)

    def test_user_resources_are_isolated(self):
        other = self.service.register_user("other@example.com", "Other")
        paper = self.service.add_arxiv_paper(self.user.id, "2106.09685", "LoRA")

        with self.assertRaises(NotFoundError):
            self.service.attach_paper_to_project(other.id, "missing", paper.id)

        self.assertEqual(self.service.list_library(other.id), [])
        self.assertEqual(len(self.service.list_library(self.user.id)), 1)

    def test_paper_processing_events_track_status_history(self):
        paper = self.service.add_pdf_upload(self.user.id, "paper.pdf", object_key="user/paper.pdf")

        self.service.mark_paper_status(
            self.user.id,
            paper.id,
            PaperStatus.PROCESSING,
            "Processing started.",
            worker="local",
        )
        self.service.mark_paper_status(self.user.id, paper.id, PaperStatus.READY, "Ready for Q&A.")

        events = self.service.list_paper_events(self.user.id, paper.id)

        self.assertEqual([event.status for event in events], [
            PaperStatus.UPLOADED,
            PaperStatus.PROCESSING,
            PaperStatus.READY,
        ])
        self.assertEqual(events[1].message, "Processing started.")
        self.assertEqual(events[1].metadata["worker"], "local")
        self.assertEqual(paper.status, PaperStatus.READY)

    def test_paper_knowledge_can_be_recorded_and_promoted_to_memory(self):
        paper = self.service.add_pdf_upload(self.user.id, "paper.pdf", object_key="user/paper.pdf")
        artifact = {
            "paper_id": paper.id,
            "concepts": [{"label": "fine-tuning", "frequency": 2}],
            "entities": [{"label": "LoRA", "entity_type": "named_entity", "frequency": 3}],
            "summary": {"concepts": 1, "entities": 1, "sections": 1},
        }

        self.service.record_paper_knowledge(self.user.id, paper.id, artifact)
        loaded = self.service.get_paper_knowledge(self.user.id, paper.id)
        first_promotion = self.service.promote_paper_knowledge_to_memory(self.user.id, paper.id)
        second_promotion = self.service.promote_paper_knowledge_to_memory(self.user.id, paper.id)

        self.assertEqual(loaded, artifact)
        self.assertEqual([memory.content for memory in first_promotion], ["concept: fine-tuning", "entity: LoRA"])
        self.assertEqual(second_promotion, [])
        self.assertEqual(self.service.dashboard(self.user.id).memories, 2)

    def test_paper_knowledge_can_load_from_artifact_path(self):
        paper = self.service.add_pdf_upload(self.user.id, "paper.pdf", object_key="user/paper.pdf")
        artifact = {
            "paper_id": paper.id,
            "concepts": [{"label": "attention", "frequency": 1}],
            "entities": [],
            "summary": {"concepts": 1, "entities": 0, "sections": 1},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = os.path.join(tmpdir, "knowledge.json")
            with open(artifact_path, "w") as f:
                json.dump(artifact, f)

            self.service.record_paper_knowledge(self.user.id, paper.id, {}, artifact_path=artifact_path)

            self.assertEqual(self.service.get_paper_knowledge(self.user.id, paper.id), artifact)

    def test_search_knowledge_across_user_library(self):
        lora = self.service.add_arxiv_paper(self.user.id, "2106.09685", "LoRA")
        rag = self.service.add_arxiv_paper(self.user.id, "2005.11401", "RAG")
        self.service.record_paper_knowledge(
            self.user.id,
            lora.id,
            {
                "paper_id": lora.id,
                "concepts": [
                    {"label": "fine-tuning", "frequency": 4, "sections": ["method"], "chunk_ids": [0]},
                    {"label": "transformer", "frequency": 2, "sections": ["abstract"], "chunk_ids": [0]},
                ],
                "entities": [{"label": "LoRA", "entity_type": "acronym", "frequency": 5}],
                "summary": {"concepts": 2, "entities": 1, "sections": 2},
            },
        )
        self.service.record_paper_knowledge(
            self.user.id,
            rag.id,
            {
                "paper_id": rag.id,
                "concepts": [{"label": "retrieval", "frequency": 5, "sections": ["method"], "chunk_ids": [1]}],
                "entities": [{"label": "RAG", "entity_type": "acronym", "frequency": 6}],
                "summary": {"concepts": 1, "entities": 1, "sections": 1},
            },
        )

        all_results = self.service.search_knowledge(self.user.id)
        retrieval_results = self.service.search_knowledge(self.user.id, query="retr")
        entity_results = self.service.search_knowledge(self.user.id, kind="entity")
        lora_results = self.service.search_knowledge(self.user.id, paper_id=lora.id)

        self.assertEqual(len(all_results), 5)
        self.assertEqual(retrieval_results[0]["label"], "retrieval")
        self.assertEqual(retrieval_results[0]["paper_id"], rag.id)
        self.assertEqual({item["kind"] for item in entity_results}, {"entity"})
        self.assertEqual({item["paper_id"] for item in lora_results}, {lora.id})

    def test_search_knowledge_is_user_isolated(self):
        paper = self.service.add_arxiv_paper(self.user.id, "2106.09685", "LoRA")
        other = self.service.register_user("other@example.com", "Other")
        self.service.record_paper_knowledge(
            self.user.id,
            paper.id,
            {
                "paper_id": paper.id,
                "concepts": [{"label": "fine-tuning", "frequency": 1}],
                "entities": [],
                "summary": {"concepts": 1, "entities": 0, "sections": 1},
            },
        )

        self.assertEqual(self.service.search_knowledge(other.id), [])

    def test_relations_are_searchable_and_can_be_promoted(self):
        paper = self.service.add_arxiv_paper(self.user.id, "2106.09685", "LoRA")
        self.service.record_paper_knowledge(
            self.user.id,
            paper.id,
            {
                "paper_id": paper.id,
                "concepts": [],
                "entities": [],
                "relations": [{"source": "lora", "relation": "evaluated_on", "target": "glue", "evidence_count": 2}],
                "summary": {"concepts": 0, "entities": 0, "relations": 1, "sections": 1},
            },
        )

        results = self.service.search_knowledge(self.user.id, query="glue", kind="relation")
        memories = self.service.promote_paper_knowledge_to_memory(
            self.user.id, paper.id, include_concepts=False, include_entities=False, include_relations=True
        )

        self.assertEqual(results[0]["relation"], "evaluated_on")
        self.assertEqual(memories[0].content, "relation: lora evaluated_on glue")


if __name__ == "__main__":
    unittest.main()
