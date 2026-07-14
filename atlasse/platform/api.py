"""FastAPI entry point for the ATLASS product platform."""

from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
import subprocess

from .service import ResearchWorkspaceService
from .store import NotFoundError
from .storage import ObjectStorage
from .jobs import PaperJobPipeline
from .conversation_agent import ConversationAgent


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
        from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel, Field
    except ImportError as exc:
        raise RuntimeError("Install FastAPI dependencies to run the ATLASS backend API.") from exc

    app = FastAPI(title="ATLASS Backend API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    workspace = service or ResearchWorkspaceService()
    storage = ObjectStorage()
    pipeline = PaperJobPipeline(workspace, storage)
    conv_agent = ConversationAgent(workspace)

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

    class DatasetRequest(BaseModel):
        name: str
        url: str
        description: str = ""

    class RepoRequest(BaseModel):
        name: str
        url: str
        description: str = ""

    class AttachResourceRequest(BaseModel):
        resource_id: str

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

    class PromoteKnowledgeRequest(BaseModel):
        include_concepts: bool = True
        include_entities: bool = True
        include_relations: bool = False
        limit: int = 20

    class PaperQuestionRequest(BaseModel):
        question: str
        include_debug: bool = False

    class ComparePapersRequest(BaseModel):
        paper_ids: list[str]
        aspect: str = "method"
        include_debug: bool = False

    class SystemSpecReviewRequest(BaseModel):
        field_updates: dict[str, str | None] = Field(default_factory=dict)
        notes: str | None = None
        approve: bool = False

    class ImplementationBlueprintReviewRequest(BaseModel):
        module_updates: dict[str, str] = Field(default_factory=dict)
        assumptions: list[dict] | None = None
        notes: str | None = None
        approve: bool = False

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

    @app.post("/users/{user_id}/demo-paper")
    def seed_demo_paper(user_id: str):
        try:
            return _jsonable(workspace.seed_demo_paper(user_id))
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.get("/users/{user_id}/knowledge")
    def search_knowledge(
        user_id: str,
        q: str = "",
        kind: str | None = None,
        paper_id: str | None = None,
        limit: int = 25,
    ):
        try:
            return {
                "query": q,
                "results": _jsonable(
                    workspace.search_knowledge(
                        user_id,
                        query=q,
                        kind=kind,
                        paper_id=paper_id,
                        limit=limit,
                    )
                ),
            }
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.get("/users/{user_id}/papers/{paper_id}/events")
    def list_paper_events(user_id: str, paper_id: str):
        try:
            return _jsonable(workspace.list_paper_events(user_id, paper_id))
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.get("/users/{user_id}/papers/{paper_id}/knowledge")
    def get_paper_knowledge(user_id: str, paper_id: str):
        try:
            return _jsonable(workspace.get_paper_knowledge(user_id, paper_id))
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.post("/users/{user_id}/papers/{paper_id}/knowledge/promote")
    def promote_paper_knowledge(user_id: str, paper_id: str, payload: PromoteKnowledgeRequest):
        try:
            memories = workspace.promote_paper_knowledge_to_memory(
                user_id,
                paper_id,
                include_concepts=payload.include_concepts,
                include_entities=payload.include_entities,
                include_relations=payload.include_relations,
                limit=payload.limit,
            )
            return {"promoted": _jsonable(memories), "count": len(memories)}
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.post("/users/{user_id}/papers/{paper_id}/ask")
    def ask_paper(user_id: str, paper_id: str, payload: PaperQuestionRequest):
        try:
            return _jsonable(
                workspace.ask_paper(
                    user_id,
                    paper_id,
                    payload.question,
                    include_debug=payload.include_debug,
                )
            )
        except NotFoundError as exc:
            handle_not_found(exc)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/users/{user_id}/papers/{paper_id}/system-spec")
    def generate_system_spec(user_id: str, paper_id: str):
        try:
            return _jsonable(workspace.generate_system_spec(user_id, paper_id))
        except NotFoundError as exc:
            handle_not_found(exc)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/users/{user_id}/papers/{paper_id}/system-spec")
    def get_system_spec(user_id: str, paper_id: str):
        try:
            return _jsonable(workspace.get_system_spec(user_id, paper_id))
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.patch("/users/{user_id}/papers/{paper_id}/system-spec")
    def review_system_spec(user_id: str, paper_id: str, payload: SystemSpecReviewRequest):
        try:
            return _jsonable(
                workspace.review_system_spec(user_id, paper_id, payload.field_updates, payload.notes, payload.approve)
            )
        except NotFoundError as exc:
            handle_not_found(exc)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/users/{user_id}/papers/{paper_id}/implementation-blueprint")
    def generate_implementation_blueprint(user_id: str, paper_id: str):
        try:
            return _jsonable(workspace.generate_implementation_blueprint(user_id, paper_id))
        except NotFoundError as exc:
            handle_not_found(exc)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/users/{user_id}/papers/{paper_id}/implementation-blueprint")
    def get_implementation_blueprint(user_id: str, paper_id: str):
        try:
            return _jsonable(workspace.get_implementation_blueprint(user_id, paper_id))
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.patch("/users/{user_id}/papers/{paper_id}/implementation-blueprint")
    def review_implementation_blueprint(
        user_id: str,
        paper_id: str,
        payload: ImplementationBlueprintReviewRequest,
    ):
        try:
            return _jsonable(
                workspace.review_implementation_blueprint(
                    user_id,
                    paper_id,
                    payload.module_updates,
                    payload.assumptions,
                    payload.notes,
                    payload.approve,
                )
            )
        except NotFoundError as exc:
            handle_not_found(exc)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/users/{user_id}/papers/{paper_id}/baseline-project")
    def generate_baseline_project(user_id: str, paper_id: str):
        try:
            return _jsonable(workspace.generate_baseline_project(user_id, paper_id))
        except NotFoundError as exc:
            handle_not_found(exc)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/users/{user_id}/papers/{paper_id}/baseline-project")
    def get_baseline_project(user_id: str, paper_id: str):
        try:
            return _jsonable(workspace.get_baseline_project(user_id, paper_id))
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.post("/users/{user_id}/papers/{paper_id}/baseline-project/run")
    def run_baseline_project(user_id: str, paper_id: str):
        try:
            return _jsonable(workspace.run_baseline_smoke(user_id, paper_id))
        except NotFoundError as exc:
            handle_not_found(exc)
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/users/{user_id}/papers/{paper_id}/reproduction-report")
    def get_reproduction_report(user_id: str, paper_id: str):
        try:
            return _jsonable(workspace.get_latest_reproduction_report(user_id, paper_id))
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.post("/users/{user_id}/papers/compare")
    def compare_papers(user_id: str, payload: ComparePapersRequest):
        try:
            return _jsonable(
                workspace.compare_papers(
                    user_id,
                    payload.paper_ids,
                    aspect=payload.aspect,
                    include_debug=payload.include_debug,
                )
            )
        except NotFoundError as exc:
            handle_not_found(exc)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/users/{user_id}/papers")
    def add_paper(user_id: str, payload: PaperRequest, background_tasks: BackgroundTasks):
        try:
            if payload.source_type == "arxiv":
                paper = workspace.add_arxiv_paper(user_id, payload.source_ref, payload.title)
            elif payload.source_type == "doi":
                paper = workspace.add_doi_paper(user_id, payload.source_ref, payload.title)
            elif payload.source_type == "pdf":
                paper = workspace.add_pdf_upload(user_id, payload.source_ref, payload.title)
            else:
                raise HTTPException(status_code=400, detail="source_type must be arxiv, doi, or pdf")
            
            background_tasks.add_task(pipeline.process_paper, user_id, paper.id, paper)
            return _jsonable(paper)
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.post("/users/{user_id}/papers/upload")
    def upload_paper(
        user_id: str,
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        title: str | None = None,
    ):
        try:
            content = file.file.read()
            filename = Path(file.filename or "upload.pdf").name
            object_key = f"{user_id}/{filename}"
            storage.put_bytes(object_key, content)

            paper = workspace.add_pdf_upload(user_id, filename, title=title or filename, object_key=object_key)
            background_tasks.add_task(pipeline.process_paper, user_id, paper.id, paper)
            return _jsonable(paper)
        except NotFoundError as exc:
            handle_not_found(exc)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/users/{user_id}/projects")
    def create_project(user_id: str, payload: ProjectRequest):
        try:
            return _jsonable(workspace.create_project(user_id, payload.name, payload.description))
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.get("/users/{user_id}/projects")
    def list_projects(user_id: str):
        try:
            return _jsonable(workspace.list_projects(user_id))
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.post("/users/{user_id}/projects/{project_id}/papers")
    def attach_paper(user_id: str, project_id: str, payload: AttachResourceRequest):
        try:
            return _jsonable(workspace.attach_paper_to_project(user_id, project_id, payload.resource_id))
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.post("/users/{user_id}/datasets")
    def add_dataset(user_id: str, payload: DatasetRequest):
        try:
            return _jsonable(workspace.add_dataset(user_id, payload.name, payload.url, payload.description))
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.post("/users/{user_id}/projects/{project_id}/datasets")
    def attach_dataset(user_id: str, project_id: str, payload: AttachResourceRequest):
        try:
            return _jsonable(workspace.attach_dataset_to_project(user_id, project_id, payload.resource_id))
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.post("/users/{user_id}/repos")
    def add_repo(user_id: str, payload: RepoRequest):
        try:
            return _jsonable(workspace.add_repo(user_id, payload.name, payload.url, payload.description))
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.post("/users/{user_id}/projects/{project_id}/repos")
    def attach_repo(user_id: str, project_id: str, payload: AttachResourceRequest):
        try:
            return _jsonable(workspace.attach_repo_to_project(user_id, project_id, payload.resource_id))
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.get("/users/{user_id}/projects/{project_id}/timeline")
    def get_timeline(user_id: str, project_id: str):
        try:
            return _jsonable(workspace.get_project_timeline(user_id, project_id))
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

    @app.post("/users/{user_id}/conversations/{conversation_id}/generate_notes")
    def generate_notes(user_id: str, conversation_id: str):
        try:
            notes = conv_agent.generate_notes(user_id, conversation_id)
            return {"notes": notes}
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.post("/users/{user_id}/conversations/{conversation_id}/extract_insights")
    def extract_insights(user_id: str, conversation_id: str):
        try:
            insights = conv_agent.extract_insights(user_id, conversation_id)
            return {"insights": insights}
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except NotFoundError as exc:
            handle_not_found(exc)

    @app.get("/users/{user_id}/conversations/{conversation_id}/follow_ups")
    def get_follow_ups(user_id: str, conversation_id: str):
        try:
            questions = conv_agent.generate_follow_ups(user_id, conversation_id)
            return {"follow_ups": questions}
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except NotFoundError as exc:
            handle_not_found(exc)

    return app


try:
    app = create_app()
except RuntimeError:
    app = None
