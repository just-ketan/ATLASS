import os
import sys
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


if __name__ == "__main__":
    unittest.main()
