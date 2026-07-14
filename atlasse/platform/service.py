"""Application service for the ATLASS research workspace."""

import json
from datetime import datetime, timezone
from pathlib import Path

from .models import PaperStatus
from .store import InMemoryWorkspaceStore, NotFoundError


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

    def mark_paper_status(
        self,
        user_id: str,
        paper_id: str,
        status: str | PaperStatus,
        message: str | None = None,
        **metadata,
    ):
        status_value = status if isinstance(status, PaperStatus) else PaperStatus(status)
        return self.store.update_paper_status(user_id, paper_id, status_value, message, **metadata)

    def list_paper_events(self, user_id: str, paper_id: str):
        return self.store.list_paper_events(user_id, paper_id)

    def record_paper_knowledge(
        self,
        user_id: str,
        paper_id: str,
        artifact: dict,
        artifact_path: str | None = None,
    ):
        return self.store.update_paper_metadata(
            user_id,
            paper_id,
            knowledge_artifact=artifact,
            knowledge_path=artifact_path,
        )

    def record_paper_processing_artifacts(
        self,
        user_id: str,
        paper_id: str,
        pdf_path: str | None = None,
        processed_json_path: str | None = None,
        memory_index_path: str | None = None,
    ):
        """Persist local artifact locations behind the storage abstraction boundary."""
        return self.store.update_paper_metadata(
            user_id,
            paper_id,
            pdf_path=pdf_path,
            processed_json_path=processed_json_path,
            memory_index_path=memory_index_path,
        )

    def generate_system_spec(self, user_id: str, paper_id: str) -> dict:
        paper = self.store.get_paper(user_id, paper_id)
        if paper.status != PaperStatus.READY:
            raise ValueError(f"Paper {paper_id} is not ready for system specification (status: {paper.status.value}).")
        json_path = paper.metadata.get("processed_json_path")
        if not json_path or not Path(json_path).exists():
            raise NotFoundError(f"Processed text for paper {paper_id} not found")

        from atlasse.knowledge_engine.paper_understanding.system_spec import SystemSpecExtractor

        extractor = SystemSpecExtractor(paper_id)
        spec = extractor.extract(json_path)
        spec_path = extractor.save(spec)
        self.store.update_paper_metadata(
            user_id,
            paper_id,
            system_spec=spec,
            system_spec_path=spec_path,
        )
        return spec

    def get_system_spec(self, user_id: str, paper_id: str) -> dict:
        paper = self.store.get_paper(user_id, paper_id)
        spec = paper.metadata.get("system_spec")
        if spec:
            return spec
        spec_path = paper.metadata.get("system_spec_path")
        if spec_path and Path(spec_path).exists():
            with open(spec_path) as file:
                spec = json.load(file)
            self.store.update_paper_metadata(user_id, paper_id, system_spec=spec)
            return spec
        raise NotFoundError(f"System specification for paper {paper_id} not found")

    def review_system_spec(
        self,
        user_id: str,
        paper_id: str,
        field_updates: dict[str, str | None],
        notes: str | None = None,
        approve: bool = False,
    ) -> dict:
        spec = self.get_system_spec(user_id, paper_id)
        fields = spec.get("fields", {})
        unknown_fields = sorted(set(field_updates).difference(fields))
        if unknown_fields:
            raise ValueError(f"Unknown system specification fields: {', '.join(unknown_fields)}")

        for name, value in field_updates.items():
            field = fields[name]
            field["value"] = value.strip() if isinstance(value, str) and value.strip() else None
            field["status"] = "confirmed" if field["value"] else "missing"
            field["assumption"] = "Manually reviewed or supplied by the user."

        review = spec.setdefault("review", {})
        review["status"] = "approved" if approve else ("reviewed" if field_updates else review.get("status", "needs_review"))
        review["notes"] = notes if notes is not None else review.get("notes", "")
        review["version"] = int(review.get("version", 1)) + 1
        review["updated_at"] = datetime.now(timezone.utc).isoformat()

        spec_path = self.store.get_paper(user_id, paper_id).metadata.get("system_spec_path")
        if spec_path:
            with open(spec_path, "w") as file:
                json.dump(spec, file, indent=2)
        self.store.update_paper_metadata(user_id, paper_id, system_spec=spec)
        return spec

    def generate_implementation_blueprint(self, user_id: str, paper_id: str) -> dict:
        spec = self.get_system_spec(user_id, paper_id)
        if spec.get("review", {}).get("status") != "approved":
            raise ValueError("Approve the system specification before generating an implementation blueprint.")

        from atlasse.knowledge_engine.paper_understanding.implementation_blueprint import ImplementationBlueprintGenerator

        generator = ImplementationBlueprintGenerator(paper_id)
        blueprint = generator.generate(spec)
        blueprint_path = generator.save(blueprint)
        self.store.update_paper_metadata(
            user_id,
            paper_id,
            implementation_blueprint=blueprint,
            implementation_blueprint_path=blueprint_path,
        )
        return blueprint

    def get_implementation_blueprint(self, user_id: str, paper_id: str) -> dict:
        paper = self.store.get_paper(user_id, paper_id)
        blueprint = paper.metadata.get("implementation_blueprint")
        if blueprint:
            return blueprint
        path = paper.metadata.get("implementation_blueprint_path")
        if path and Path(path).exists():
            with open(path) as file:
                blueprint = json.load(file)
            self.store.update_paper_metadata(user_id, paper_id, implementation_blueprint=blueprint)
            return blueprint
        raise NotFoundError(f"Implementation blueprint for paper {paper_id} not found")

    def review_implementation_blueprint(
        self,
        user_id: str,
        paper_id: str,
        module_updates: dict[str, str],
        assumptions: list[dict] | None = None,
        notes: str | None = None,
        approve: bool = False,
    ) -> dict:
        blueprint = self.get_implementation_blueprint(user_id, paper_id)
        modules = {module["path"]: module for module in blueprint.get("modules", [])}
        unknown_modules = sorted(set(module_updates).difference(modules))
        if unknown_modules:
            raise ValueError(f"Unknown blueprint modules: {', '.join(unknown_modules)}")
        for path, responsibility in module_updates.items():
            modules[path]["responsibility"] = responsibility
            modules[path]["reviewed"] = True
        if assumptions is not None:
            blueprint["assumptions"] = assumptions

        review = blueprint.setdefault("review", {})
        review["status"] = "approved" if approve else ("reviewed" if module_updates or assumptions is not None else review.get("status", "needs_review"))
        review["notes"] = notes if notes is not None else review.get("notes", "")
        review["version"] = int(review.get("version", 1)) + 1
        review["updated_at"] = datetime.now(timezone.utc).isoformat()

        path = self.store.get_paper(user_id, paper_id).metadata.get("implementation_blueprint_path")
        if path:
            with open(path, "w") as file:
                json.dump(blueprint, file, indent=2)
        self.store.update_paper_metadata(user_id, paper_id, implementation_blueprint=blueprint)
        return blueprint

    def generate_baseline_project(self, user_id: str, paper_id: str) -> dict:
        blueprint = self.get_implementation_blueprint(user_id, paper_id)
        from atlasse.knowledge_engine.paper_understanding.baseline_project import BaselineProjectGenerator

        manifest = BaselineProjectGenerator(paper_id).generate(blueprint)
        self.store.update_paper_metadata(
            user_id,
            paper_id,
            baseline_project=manifest,
            baseline_project_path=manifest["project_dir"],
        )
        return manifest

    def get_baseline_project(self, user_id: str, paper_id: str) -> dict:
        paper = self.store.get_paper(user_id, paper_id)
        manifest = paper.metadata.get("baseline_project")
        if manifest:
            return manifest
        path = paper.metadata.get("baseline_project_path")
        manifest_path = Path(path) / "atlass_manifest.json" if path else None
        if manifest_path and manifest_path.exists():
            with open(manifest_path) as file:
                manifest = json.load(file)
            self.store.update_paper_metadata(user_id, paper_id, baseline_project=manifest)
            return manifest
        raise NotFoundError(f"Generated baseline project for paper {paper_id} not found")

    def run_baseline_smoke(self, user_id: str, paper_id: str) -> dict:
        manifest = self.get_baseline_project(user_id, paper_id)
        system_spec = self.get_system_spec(user_id, paper_id)
        from .reproduction_runner import ReproductionRunner

        report, report_path = ReproductionRunner().run_smoke(manifest, system_spec)
        self.store.update_paper_metadata(
            user_id,
            paper_id,
            latest_reproduction_report=report,
            latest_reproduction_report_path=report_path,
        )
        return report

    def get_latest_reproduction_report(self, user_id: str, paper_id: str) -> dict:
        paper = self.store.get_paper(user_id, paper_id)
        report = paper.metadata.get("latest_reproduction_report")
        if report:
            return report
        path = paper.metadata.get("latest_reproduction_report_path")
        if path and Path(path).exists():
            with open(path) as file:
                report = json.load(file)
            self.store.update_paper_metadata(user_id, paper_id, latest_reproduction_report=report)
            return report
        raise NotFoundError(f"No reproduction report for paper {paper_id} found")

    def seed_demo_paper(self, user_id: str):
        from .demo_seed import DemoWorkspaceSeeder

        return DemoWorkspaceSeeder(self).seed_paper(user_id)

    def ask_paper(self, user_id: str, paper_id: str, question: str, include_debug: bool = False) -> dict:
        """Retrieve an evidence-grounded answer for a paper owned by the user."""
        if not question or not question.strip():
            raise ValueError("A question is required.")

        paper = self.store.get_paper(user_id, paper_id)
        if paper.status != PaperStatus.READY:
            raise ValueError(f"Paper {paper_id} is not ready for questions (status: {paper.status.value}).")

        processed_json_path = paper.metadata.get("processed_json_path")
        if not processed_json_path or not Path(processed_json_path).exists():
            raise NotFoundError(f"Processed text for paper {paper_id} not found")

        from atlasse.knowledge_engine.paper_understanding.paper_understanding_engine import PaperUnderstandingEngine

        engine = PaperUnderstandingEngine(processed_json_path, paper_id=paper_id)
        result = engine.ask_with_provenance(question.strip())
        response = {
            **result,
            "paper_id": paper.id,
            "paper_title": paper.title,
        }
        if include_debug:
            response["retrieval_debug"] = engine.memory.last_trace
        return response

    def compare_papers(
        self,
        user_id: str,
        paper_ids: list[str],
        aspect: str = "method",
        include_debug: bool = False,
    ) -> dict:
        """Compare workspace papers using the shared retrieval layer and citations."""
        selected_ids = list(dict.fromkeys(paper_ids))
        if len(selected_ids) < 2:
            raise ValueError("Select at least two papers to compare.")

        papers = [self.store.get_paper(user_id, paper_id) for paper_id in selected_ids]
        unavailable = [paper.id for paper in papers if paper.status != PaperStatus.READY]
        if unavailable:
            raise ValueError(f"Papers are not ready for comparison: {', '.join(unavailable)}")

        from atlasse.knowledge_engine.corpus.corpus_memory import CorpusMemory
        from atlasse.knowledge_engine.orchestration.query_orchestrator import QueryOrchestrator

        query = self._comparison_query(aspect)
        corpus = CorpusMemory()
        for paper in papers:
            processed_json_path = paper.metadata.get("processed_json_path")
            if not processed_json_path or not Path(processed_json_path).exists():
                raise NotFoundError(f"Processed text for paper {paper.id} not found")
            corpus.add_paper(processed_json_path, paper_id=paper.id)

        comparisons = {}
        for paper in papers:
            result = QueryOrchestrator(corpus.papers[paper.id]).ask_with_provenance(query)
            comparisons[paper.id] = {"paper_title": paper.title, **result}
            if include_debug:
                comparisons[paper.id]["retrieval_debug"] = corpus.papers[paper.id].last_trace

        return {
            "aspect": aspect,
            "query": query,
            "papers": selected_ids,
            "comparisons": comparisons,
            "synthesis": self._comparison_synthesis(comparisons, aspect),
        }

    @staticmethod
    def _comparison_query(aspect: str) -> str:
        return {
            "method": "what method is proposed",
            "problem": "what problem does this paper address",
            "limitations": "what are the limitations",
            "results": "what are the main experimental results",
        }.get(aspect.lower().strip(), aspect)

    @staticmethod
    def _comparison_synthesis(comparisons: dict[str, dict], aspect: str) -> str:
        """MVP synthesis stays extractive so every statement retains source evidence."""
        summaries = [
            f"{item['paper_title']}: {item.get('answer', 'No evidence found.')}"
            for item in comparisons.values()
        ]
        return f"Comparison by {aspect}: " + " ".join(summaries)

    def get_paper_knowledge(self, user_id: str, paper_id: str) -> dict:
        paper = self.store.get_paper(user_id, paper_id)
        artifact = paper.metadata.get("knowledge_artifact")
        if artifact:
            return artifact

        artifact_path = paper.metadata.get("knowledge_path")
        if artifact_path and Path(artifact_path).exists():
            with open(artifact_path) as f:
                artifact = json.load(f)
            self.store.update_paper_metadata(user_id, paper_id, knowledge_artifact=artifact)
            return artifact

        raise NotFoundError(f"Knowledge artifact for paper {paper_id} not found")

    def promote_paper_knowledge_to_memory(
        self,
        user_id: str,
        paper_id: str,
        include_concepts: bool = True,
        include_entities: bool = True,
        include_relations: bool = False,
        limit: int = 20,
    ):
        artifact = self.get_paper_knowledge(user_id, paper_id)
        promoted = []
        selected = []
        if include_concepts:
            selected.extend(("concept", item) for item in artifact.get("concepts", []))
        if include_entities:
            selected.extend(("entity", item) for item in artifact.get("entities", []))
        if include_relations:
            selected.extend(("relation", item) for item in artifact.get("relations", []))

        existing = {
            (memory.source_type, memory.source_id, memory.content)
            for memory in self.store.list_memories(user_id)
        }
        for kind, item in selected[:limit]:
            label = item.get("label")
            if kind == "relation":
                label = f"{item.get('source', '')} {item.get('relation', '')} {item.get('target', '')}".strip()
            if not label:
                continue
            content = f"{kind}: {label}"
            key = ("paper_knowledge", paper_id, content)
            if key in existing:
                continue
            memory = self.store.remember(
                user_id,
                content,
                source_type="paper_knowledge",
                source_id=paper_id,
                tags=["paper", "knowledge", kind],
            )
            existing.add(key)
            promoted.append(memory)
        return promoted

    def search_knowledge(
        self,
        user_id: str,
        query: str = "",
        kind: str | None = None,
        paper_id: str | None = None,
        limit: int = 25,
    ) -> list[dict]:
        self.store.get_user(user_id)
        query_normalized = query.lower().strip()
        kind_normalized = kind.lower().strip() if kind else None
        results = []

        papers = [self.store.get_paper(user_id, paper_id)] if paper_id else self.store.list_papers(user_id)
        for paper in papers:
            try:
                artifact = self.get_paper_knowledge(user_id, paper.id)
            except NotFoundError:
                continue

            for item_kind, collection in (("concept", "concepts"), ("entity", "entities"), ("relation", "relations")):
                if kind_normalized and item_kind != kind_normalized:
                    continue
                for item in artifact.get(collection, []):
                    label = item.get("label", "")
                    if item_kind == "relation":
                        label = " ".join(filter(None, [item.get("source"), item.get("relation"), item.get("target")]))
                    if not label:
                        continue
                    score = self._knowledge_match_score(query_normalized, label)
                    if query_normalized and score == 0:
                        continue
                    results.append({
                        "paper_id": paper.id,
                        "paper_title": paper.title,
                        "kind": item_kind,
                        "label": label,
                        "frequency": item.get("frequency", item.get("evidence_count", 0)),
                        "sections": item.get("sections", []),
                        "chunk_ids": item.get("chunk_ids", []),
                        "entity_type": item.get("entity_type"),
                        "relation": item.get("relation"),
                        "source": item.get("source"),
                        "target": item.get("target"),
                        "score": score,
                    })

        results.sort(key=lambda item: (-item["score"], -item["frequency"], item["label"].lower()))
        return results[:limit]

    @staticmethod
    def _knowledge_match_score(query: str, label: str) -> int:
        if not query:
            return 1
        label_normalized = label.lower()
        if label_normalized == query:
            return 100
        if label_normalized.startswith(query):
            return 75
        if query in label_normalized:
            return 50
        query_terms = [term for term in query.split() if term]
        if query_terms and all(term in label_normalized for term in query_terms):
            return 25
        return 0

    def list_library(self, user_id: str):
        return self.store.list_papers(user_id)

    def create_project(self, user_id: str, name: str, description: str = ""):
        return self.store.create_project(user_id, name, description)

    def list_projects(self, user_id: str):
        return self.store.list_projects(user_id)

    def attach_paper_to_project(self, user_id: str, project_id: str, paper_id: str):
        return self.store.add_project_paper(user_id, project_id, paper_id)

    def add_dataset(self, user_id: str, name: str, url: str, description: str = ""):
        return self.store.add_dataset(user_id, name, url, description)

    def attach_dataset_to_project(self, user_id: str, project_id: str, dataset_id: str):
        return self.store.add_project_dataset(user_id, project_id, dataset_id)

    def add_repo(self, user_id: str, name: str, url: str, description: str = ""):
        return self.store.add_repo(user_id, name, url, description)

    def attach_repo_to_project(self, user_id: str, project_id: str, repo_id: str):
        return self.store.add_project_repo(user_id, project_id, repo_id)

    def get_project_timeline(self, user_id: str, project_id: str):
        return self.store.list_project_timeline(user_id, project_id)

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

    def list_memories(self, user_id: str):
        return self.store.list_memories(user_id)

    def add_citation(self, user_id: str, paper_id: str, text: str, style: str = "apa"):
        return self.store.add_citation(user_id, paper_id, text, style=style)
