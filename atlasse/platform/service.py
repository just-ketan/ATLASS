"""Application service for the ATLASS research workspace."""

from .models import PaperStatus
from .store import InMemoryWorkspaceStore


class ResearchWorkspaceService:
    """Coordinates user-owned research library resources."""

    def __init__(self, store: InMemoryWorkspaceStore | None = None):
        self.store = store or InMemoryWorkspaceStore()

    def login_with_oauth(self, provider: str, subject: str, email: str, name: str = ""):
        return self.store.upsert_oauth_user(provider, subject, email, name)

    def register_user(self, email: str, name: str):
        return self.store.create_user(email=email, name=name)

    def dashboard(self, user_id: str):
        return self.store.dashboard(user_id)

    def add_arxiv_paper(self, user_id: str, arxiv_id: str, title: str | None = None):
        return self.store.add_paper(
            user_id=user_id,
            title=title or f"arXiv:{arxiv_id}",
            source_type="arxiv",
            source_ref=arxiv_id,
            arxiv_id=arxiv_id,
        )

    def add_pdf_upload(self, user_id: str, filename: str, title: str | None = None, object_key: str | None = None):
        return self.store.add_paper(
            user_id=user_id,
            title=title or filename,
            source_type="pdf",
            source_ref=object_key or filename,
            filename=filename,
            object_key=object_key,
        )

    def add_doi_paper(self, user_id: str, doi: str, title: str | None = None):
        return self.store.add_paper(
            user_id=user_id,
            title=title or doi,
            source_type="doi",
            source_ref=doi,
            doi=doi,
        )

    def mark_paper_status(self, user_id: str, paper_id: str, status: str | PaperStatus):
        status_value = status if isinstance(status, PaperStatus) else PaperStatus(status)
        return self.store.update_paper_status(user_id, paper_id, status_value)

    def list_library(self, user_id: str):
        return self.store.list_papers(user_id)

    def create_project(self, user_id: str, name: str, description: str = ""):
        return self.store.create_project(user_id, name, description)

    def attach_paper_to_project(self, user_id: str, project_id: str, paper_id: str):
        return self.store.add_project_paper(user_id, project_id, paper_id)

    def add_note(self, user_id: str, title: str, body: str, project_id: str | None = None, paper_id: str | None = None):
        return self.store.add_note(user_id, title, body, project_id=project_id, paper_id=paper_id)

    def start_conversation(
        self,
        user_id: str,
        title: str,
        project_id: str | None = None,
        paper_id: str | None = None,
    ):
        return self.store.create_conversation(user_id, title, project_id=project_id, paper_id=paper_id)

    def add_message(self, user_id: str, conversation_id: str, role: str, content: str, remember: bool = False):
        conversation = self.store.add_message(user_id, conversation_id, role, content)
        if remember and role in {"user", "assistant"}:
            self.store.remember(
                user_id,
                content,
                source_type="conversation",
                source_id=conversation_id,
                tags=["conversation"],
            )
        return conversation

    def remember(self, user_id: str, content: str, source_type: str = "manual", source_id: str | None = None):
        return self.store.remember(user_id, content, source_type=source_type, source_id=source_id)

    def add_citation(self, user_id: str, paper_id: str, text: str, style: str = "apa"):
        return self.store.add_citation(user_id, paper_id, text, style=style)
