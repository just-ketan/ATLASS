"""FastAPI entry point for the ATLASS product platform."""

from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum

from .service import ResearchWorkspaceService
from .store import NotFoundError


def _jsonable(value):
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value


def create_app(service: ResearchWorkspaceService | None = None):
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel
    except ImportError as exc:
        raise RuntimeError("Install FastAPI dependencies to run the ATLASS backend API.") from exc

    app = FastAPI(title="ATLASS Backend API", version="0.1.0")
    workspace = service or ResearchWorkspaceService()

    class OAuthLoginRequest(BaseModel):
        provider: str
        subject: str
        email: str
        name: str = ""

    class PaperRequest(BaseModel):
        source_type: str
        source_ref: str
        title: str | None = None

    class ProjectRequest(BaseModel):
        name: str
        description: str = ""

    class NoteRequest(BaseModel):
        title: str
        body: str
        project_id: str | None = None
        paper_id: str | None = None

    class ConversationRequest(BaseModel):
        title: str
        project_id: str | None = None
        paper_id: str | None = None

    class MessageRequest(BaseModel):
        role: str
        content: str
        remember: bool = False

    def handle_not_found(exc: NotFoundError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "atlass"}

    @app.post("/auth/oauth")
    def oauth_login(payload: OAuthLoginRequest):
        user = workspace.login_with_oauth(payload.provider, payload.subject, payload.email, payload.name)
        return _jsonable(user)

    @app.get("/users/{user_id}/dashboard")
    def dashboard(user_id: str):
        try:
            return _jsonable(workspace.dashboard(user_id))
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.get("/users/{user_id}/papers")
    def list_papers(user_id: str):
        try:
            return _jsonable(workspace.list_library(user_id))
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.post("/users/{user_id}/papers")
    def add_paper(user_id: str, payload: PaperRequest):
        try:
            if payload.source_type == "arxiv":
                paper = workspace.add_arxiv_paper(user_id, payload.source_ref, payload.title)
            elif payload.source_type == "doi":
                paper = workspace.add_doi_paper(user_id, payload.source_ref, payload.title)
            elif payload.source_type == "pdf":
                paper = workspace.add_pdf_upload(user_id, payload.source_ref, payload.title)
            else:
                raise HTTPException(status_code=400, detail="source_type must be arxiv, doi, or pdf")
            return _jsonable(paper)
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.post("/users/{user_id}/projects")
    def create_project(user_id: str, payload: ProjectRequest):
        try:
            return _jsonable(workspace.create_project(user_id, payload.name, payload.description))
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.post("/users/{user_id}/notes")
    def add_note(user_id: str, payload: NoteRequest):
        try:
            return _jsonable(
                workspace.add_note(
                    user_id,
                    payload.title,
                    payload.body,
                    project_id=payload.project_id,
                    paper_id=payload.paper_id,
                )
            )
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.post("/users/{user_id}/conversations")
    def start_conversation(user_id: str, payload: ConversationRequest):
        try:
            return _jsonable(
                workspace.start_conversation(
                    user_id,
                    payload.title,
                    project_id=payload.project_id,
                    paper_id=payload.paper_id,
                )
            )
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.post("/users/{user_id}/conversations/{conversation_id}/messages")
    def add_message(user_id: str, conversation_id: str, payload: MessageRequest):
        try:
            return _jsonable(
                workspace.add_message(
                    user_id,
                    conversation_id,
                    payload.role,
                    payload.content,
                    remember=payload.remember,
                )
            )
        except NotFoundError as exc:
            handle_not_found(exc)

    return app


try:
    app = create_app()
except RuntimeError:
    app = None
