"""Core product models for user-owned research workspaces."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PaperStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    OCR = "ocr"
    EXTRACTING_TEXT = "extracting_text"
    CREATING_EMBEDDINGS = "creating_embeddings"
    READY = "ready"
    FAILED = "failed"


@dataclass
class User:
    id: str
    email: str
    name: str
    auth_provider: str = "local"
    provider_subject: str | None = None
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class PaperRecord:
    id: str
    user_id: str
    title: str
    source_type: str
    source_ref: str
    status: PaperStatus = PaperStatus.UPLOADED
    arxiv_id: str | None = None
    doi: str | None = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass
class PaperProcessingEvent:
    id: str
    paper_id: str
    user_id: str
    status: PaperStatus
    message: str
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class Project:
    id: str
    user_id: str
    name: str
    description: str = ""
    paper_ids: list[str] = field(default_factory=list)
    note_ids: list[str] = field(default_factory=list)
    conversation_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class Note:
    id: str
    user_id: str
    title: str
    body: str
    project_id: str | None = None
    paper_id: str | None = None
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class Message:
    role: str
    content: str
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class Conversation:
    id: str
    user_id: str
    title: str
    project_id: str | None = None
    paper_id: str | None = None
    messages: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class MemoryItem:
    id: str
    user_id: str
    content: str
    source_type: str
    source_id: str | None = None
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class Citation:
    id: str
    user_id: str
    paper_id: str
    text: str
    style: str = "apa"
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class Dashboard:
    user_id: str
    papers: int
    projects: int
    notes: int
    conversations: int
    memories: int
    citations: int
    ready_papers: int
    processing_papers: int
