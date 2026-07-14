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
    Dataset,
    Repo,
    TimelineEvent,
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
        self.datasets: dict[str, Dataset] = {}
        self.repos: dict[str, Repo] = {}
        self.timeline_events: dict[str, TimelineEvent] = {}
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

    def list_projects(self, user_id: str) -> list[Project]:
        self.get_user(user_id)
        return [self.projects[project_id] for project_id in self.user_resources[user_id]["projects"]]

    def add_project_paper(self, user_id: str, project_id: str, paper_id: str) -> Project:
        project = self.get_project(user_id, project_id)
        self.get_paper(user_id, paper_id)
        if paper_id not in project.paper_ids:
            project.paper_ids.append(paper_id)
        self.add_timeline_event(user_id, project_id, "paper_added", f"Paper {paper_id} attached to project.")
        return project

    def get_project(self, user_id: str, project_id: str) -> Project:
        project = self.projects.get(project_id)
        if not project or project.user_id != user_id:
            raise NotFoundError(f"Project {project_id} not found")
        return project

    def add_dataset(self, user_id: str, name: str, url: str, description: str = "") -> Dataset:
        self.get_user(user_id)
        dataset = Dataset(id=self._id("dataset"), user_id=user_id, name=name, url=url, description=description)
        self.datasets[dataset.id] = dataset
        self.user_resources[user_id]["datasets"].append(dataset.id)
        return dataset

    def get_dataset(self, user_id: str, dataset_id: str) -> Dataset:
        dataset = self.datasets.get(dataset_id)
        if not dataset or dataset.user_id != user_id:
            raise NotFoundError(f"Dataset {dataset_id} not found")
        return dataset

    def add_project_dataset(self, user_id: str, project_id: str, dataset_id: str) -> Project:
        project = self.get_project(user_id, project_id)
        self.get_dataset(user_id, dataset_id)
        if dataset_id not in project.dataset_ids:
            project.dataset_ids.append(dataset_id)
        self.add_timeline_event(user_id, project_id, "dataset_added", f"Dataset {dataset_id} added to project.")
        return project

    def add_repo(self, user_id: str, name: str, url: str, description: str = "") -> Repo:
        self.get_user(user_id)
        repo = Repo(id=self._id("repo"), user_id=user_id, name=name, url=url, description=description)
        self.repos[repo.id] = repo
        self.user_resources[user_id]["repos"].append(repo.id)
        return repo

    def get_repo(self, user_id: str, repo_id: str) -> Repo:
        repo = self.repos.get(repo_id)
        if not repo or repo.user_id != user_id:
            raise NotFoundError(f"Repo {repo_id} not found")
        return repo

    def add_project_repo(self, user_id: str, project_id: str, repo_id: str) -> Project:
        project = self.get_project(user_id, project_id)
        self.get_repo(user_id, repo_id)
        if repo_id not in project.repo_ids:
            project.repo_ids.append(repo_id)
        self.add_timeline_event(user_id, project_id, "repo_added", f"Repo {repo_id} added to project.")
        return project

    def add_timeline_event(self, user_id: str, project_id: str, event_type: str, description: str) -> TimelineEvent:
        self.get_project(user_id, project_id)
        event = TimelineEvent(
            id=self._id("event"),
            user_id=user_id,
            project_id=project_id,
            event_type=event_type,
            description=description,
        )
        self.timeline_events[event.id] = event
        self.user_resources[user_id]["timeline_events"].append(event.id)
        return event

    def list_project_timeline(self, user_id: str, project_id: str) -> list[TimelineEvent]:
        self.get_project(user_id, project_id)
        events = [
            self.timeline_events[eid] for eid in self.user_resources[user_id]["timeline_events"]
            if self.timeline_events[eid].project_id == project_id
        ]
        return sorted(events, key=lambda e: e.created_at)

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

    def list_memories(self, user_id: str) -> list[MemoryItem]:
        self.get_user(user_id)
        return [self.memories[mid] for mid in self.user_resources[user_id]["memories"]]

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
            datasets=len(resources["datasets"]),
            repos=len(resources["repos"]),
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
