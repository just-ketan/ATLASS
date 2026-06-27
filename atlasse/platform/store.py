"""Repository boundary for ATLASS product data."""

from collections import defaultdict
from uuid import uuid4

from .models import (
    Citation,
    Conversation,
    Dashboard,
    MemoryItem,
    Message,
    Note,
    PaperProcessingEvent,
    PaperRecord,
    PaperStatus,
    Project,
    User,
    utc_now,
)


class NotFoundError(KeyError):
    """Raised when a workspace resource does not exist or is not owned by a user."""


class InMemoryWorkspaceStore:
    """Small repository used until Postgres is introduced."""

    def __init__(self):
        self.users: dict[str, User] = {}
        self.users_by_identity: dict[tuple[str, str], str] = {}
        self.papers: dict[str, PaperRecord] = {}
        self.paper_events: dict[str, list[PaperProcessingEvent]] = defaultdict(list)
        self.projects: dict[str, Project] = {}
        self.notes: dict[str, Note] = {}
        self.conversations: dict[str, Conversation] = {}
        self.memories: dict[str, MemoryItem] = {}
        self.citations: dict[str, Citation] = {}
        self.user_resources = defaultdict(lambda: defaultdict(list))

    @staticmethod
    def _id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:12]}"

    def upsert_oauth_user(self, provider: str, subject: str, email: str, name: str) -> User:
        key = (provider, subject)
        existing_id = self.users_by_identity.get(key)
        if existing_id:
            user = self.users[existing_id]
            user.email = email or user.email
            user.name = name or user.name
            return user

        user = User(
            id=self._id("user"),
            email=email,
            name=name or email.split("@")[0],
            auth_provider=provider,
            provider_subject=subject,
        )
        self.users[user.id] = user
        self.users_by_identity[key] = user.id
        return user

    def create_user(self, email: str, name: str) -> User:
        user = User(id=self._id("user"), email=email, name=name)
        self.users[user.id] = user
        return user

    def get_user(self, user_id: str) -> User:
        try:
            return self.users[user_id]
        except KeyError as exc:
            raise NotFoundError(f"User {user_id} not found") from exc

    def add_paper(self, user_id: str, title: str, source_type: str, source_ref: str, **metadata) -> PaperRecord:
        self.get_user(user_id)
        paper = PaperRecord(
            id=self._id("paper"),
            user_id=user_id,
            title=title,
            source_type=source_type,
            source_ref=source_ref,
            arxiv_id=metadata.pop("arxiv_id", None),
            doi=metadata.pop("doi", None),
            metadata=metadata,
        )
        self.papers[paper.id] = paper
        self.user_resources[user_id]["papers"].append(paper.id)
        self.add_paper_event(user_id, paper.id, PaperStatus.UPLOADED, "Paper record created.")
        return paper

    def update_paper_status(
        self,
        user_id: str,
        paper_id: str,
        status: PaperStatus,
        message: str | None = None,
        **metadata,
    ) -> PaperRecord:
        paper = self.get_paper(user_id, paper_id)
        paper.status = status
        paper.updated_at = utc_now()
        self.add_paper_event(user_id, paper_id, status, message or status.value.replace("_", " ").title(), **metadata)
        return paper

    def update_paper_metadata(self, user_id: str, paper_id: str, **metadata) -> PaperRecord:
        paper = self.get_paper(user_id, paper_id)
        paper.metadata.update({k: v for k, v in metadata.items() if v is not None})
        paper.updated_at = utc_now()
        return paper

    def add_paper_event(
        self,
        user_id: str,
        paper_id: str,
        status: PaperStatus,
        message: str,
        **metadata,
    ) -> PaperProcessingEvent:
        self.get_paper(user_id, paper_id)
        event = PaperProcessingEvent(
            id=self._id("event"),
            paper_id=paper_id,
            user_id=user_id,
            status=status,
            message=message,
            metadata=metadata,
        )
        self.paper_events[paper_id].append(event)
        return event

    def list_paper_events(self, user_id: str, paper_id: str) -> list[PaperProcessingEvent]:
        self.get_paper(user_id, paper_id)
        return list(self.paper_events[paper_id])

    def get_paper(self, user_id: str, paper_id: str) -> PaperRecord:
        paper = self.papers.get(paper_id)
        if not paper or paper.user_id != user_id:
            raise NotFoundError(f"Paper {paper_id} not found")
        return paper

    def list_papers(self, user_id: str) -> list[PaperRecord]:
        self.get_user(user_id)
        return [self.papers[pid] for pid in self.user_resources[user_id]["papers"]]

    def create_project(self, user_id: str, name: str, description: str = "") -> Project:
        self.get_user(user_id)
        project = Project(id=self._id("project"), user_id=user_id, name=name, description=description)
        self.projects[project.id] = project
        self.user_resources[user_id]["projects"].append(project.id)
        return project

    def add_project_paper(self, user_id: str, project_id: str, paper_id: str) -> Project:
        project = self.get_project(user_id, project_id)
        self.get_paper(user_id, paper_id)
        if paper_id not in project.paper_ids:
            project.paper_ids.append(paper_id)
        return project

    def get_project(self, user_id: str, project_id: str) -> Project:
        project = self.projects.get(project_id)
        if not project or project.user_id != user_id:
            raise NotFoundError(f"Project {project_id} not found")
        return project

    def add_note(
        self,
        user_id: str,
        title: str,
        body: str,
        project_id: str | None = None,
        paper_id: str | None = None,
    ) -> Note:
        self.get_user(user_id)
        if project_id:
            self.get_project(user_id, project_id)
        if paper_id:
            self.get_paper(user_id, paper_id)
        note = Note(id=self._id("note"), user_id=user_id, title=title, body=body, project_id=project_id, paper_id=paper_id)
        self.notes[note.id] = note
        self.user_resources[user_id]["notes"].append(note.id)
        if project_id:
            self.projects[project_id].note_ids.append(note.id)
        return note

    def create_conversation(
        self,
        user_id: str,
        title: str,
        project_id: str | None = None,
        paper_id: str | None = None,
    ) -> Conversation:
        self.get_user(user_id)
        if project_id:
            self.get_project(user_id, project_id)
        if paper_id:
            self.get_paper(user_id, paper_id)
        conversation = Conversation(
            id=self._id("conversation"),
            user_id=user_id,
            title=title,
            project_id=project_id,
            paper_id=paper_id,
        )
        self.conversations[conversation.id] = conversation
        self.user_resources[user_id]["conversations"].append(conversation.id)
        if project_id:
            self.projects[project_id].conversation_ids.append(conversation.id)
        return conversation

    def add_message(self, user_id: str, conversation_id: str, role: str, content: str) -> Conversation:
        conversation = self.conversations.get(conversation_id)
        if not conversation or conversation.user_id != user_id:
            raise NotFoundError(f"Conversation {conversation_id} not found")
        conversation.messages.append(Message(role=role, content=content))
        return conversation

    def remember(
        self,
        user_id: str,
        content: str,
        source_type: str,
        source_id: str | None = None,
        tags: list[str] | None = None,
    ) -> MemoryItem:
        self.get_user(user_id)
        memory = MemoryItem(
            id=self._id("memory"),
            user_id=user_id,
            content=content,
            source_type=source_type,
            source_id=source_id,
            tags=tags or [],
        )
        self.memories[memory.id] = memory
        self.user_resources[user_id]["memories"].append(memory.id)
        return memory

    def add_citation(self, user_id: str, paper_id: str, text: str, style: str = "apa", **metadata) -> Citation:
        self.get_paper(user_id, paper_id)
        citation = Citation(
            id=self._id("citation"),
            user_id=user_id,
            paper_id=paper_id,
            text=text,
            style=style,
            metadata=metadata,
        )
        self.citations[citation.id] = citation
        self.user_resources[user_id]["citations"].append(citation.id)
        return citation

    def dashboard(self, user_id: str) -> Dashboard:
        papers = self.list_papers(user_id)
        resources = self.user_resources[user_id]
        return Dashboard(
            user_id=user_id,
            papers=len(resources["papers"]),
            projects=len(resources["projects"]),
            notes=len(resources["notes"]),
            conversations=len(resources["conversations"]),
            memories=len(resources["memories"]),
            citations=len(resources["citations"]),
            ready_papers=sum(1 for paper in papers if paper.status == PaperStatus.READY),
            processing_papers=sum(
                1
                for paper in papers
                if paper.status in {
                    PaperStatus.PROCESSING,
                    PaperStatus.OCR,
                    PaperStatus.EXTRACTING_TEXT,
                    PaperStatus.CREATING_EMBEDDINGS,
                }
            ),
        )
