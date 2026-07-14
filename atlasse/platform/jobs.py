"""Background job pipeline for processing papers."""

import logging
import traceback
from typing import Any

from .models import PaperStatus
from .service import ResearchWorkspaceService
from .storage import ObjectStorage

logger = logging.getLogger(__name__)


class PaperJobPipeline:
    def __init__(self, workspace: ResearchWorkspaceService, storage: ObjectStorage):
        self.workspace = workspace
        self.storage = storage

    def process_paper(self, user_id: str, paper_id: str, paper_record: dict | Any):
        """Main pipeline to process a paper."""
        try:
            self._update_status(user_id, paper_id, PaperStatus.PROCESSING, "Paper processing started.")

            source_type = getattr(
                paper_record,
                "source_type",
                paper_record.get("source_type") if isinstance(paper_record, dict) else "",
            )
            source_ref = getattr(
                paper_record,
                "source_ref",
                paper_record.get("source_ref") if isinstance(paper_record, dict) else "",
            )

            pdf_path = None

            if source_type == "arxiv":
                from atlasse.knowledge_engine.paper_ingestion.arxiv_downloader import ArxivDownloader

                downloader = ArxivDownloader()
                pdf_path = downloader.download(source_ref)
            elif source_type == "pdf":
                pdf_path = self.storage.get_file_path(source_ref)
            elif source_type == "doi":
                raise NotImplementedError("DOI processing not yet implemented")
            else:
                raise ValueError(f"Unknown source type {source_type}")

            if not pdf_path:
                raise ValueError("PDF path could not be resolved.")

            self._update_status(
                user_id,
                paper_id,
                PaperStatus.EXTRACTING_TEXT,
                "Extracting paper text.",
                pdf_path=pdf_path,
            )
            from atlasse.knowledge_engine.paper_parser.paper_processor import PaperProcessor

            processor = PaperProcessor()
            json_path = processor.process(pdf_path)
            self.workspace.record_paper_processing_artifacts(
                user_id,
                paper_id,
                pdf_path=pdf_path,
                processed_json_path=json_path,
            )

            self._update_status(
                user_id,
                paper_id,
                PaperStatus.CREATING_EMBEDDINGS,
                "Creating paper embeddings and retrieval memory.",
                processed_json_path=json_path,
            )
            from atlasse.knowledge_engine.paper_embeddings.memory_builder import PaperMemory

            memory = PaperMemory(paper_id=paper_id)
            memory.build(json_path)
            self.workspace.record_paper_processing_artifacts(
                user_id,
                paper_id,
                memory_index_path=memory._index_path(),
            )

            from atlasse.knowledge_engine.paper_understanding.concept_extractor import ConceptExtractor

            extractor = ConceptExtractor(paper_id=paper_id)
            knowledge_artifact = extractor.extract_from_chunks(list(memory.chunk_metadata.values()))
            knowledge_path = extractor.save(knowledge_artifact)
            self.workspace.record_paper_knowledge(user_id, paper_id, knowledge_artifact, knowledge_path)
            self._update_status(
                user_id,
                paper_id,
                PaperStatus.CREATING_EMBEDDINGS,
                "Extracted concepts and entities.",
                knowledge_path=knowledge_path,
                concepts=knowledge_artifact["summary"]["concepts"],
                entities=knowledge_artifact["summary"]["entities"],
            )

            # System specifications are generated on demand through the API so
            # ingestion remains fast and a user can review a stable paper first.

            logger.info(f"Building knowledge graph for {paper_id}")
            from atlasse.knowledge_engine.graph.knowledge_graph import KnowledgeGraph

            graph = KnowledgeGraph(paper_id=paper_id)
            graph.build_from_chunks(memory.chunk_metadata)
            graph.save()

            self._update_status(user_id, paper_id, PaperStatus.READY, "Paper is ready for research.")
            logger.info(f"Successfully processed paper {paper_id}")

        except Exception as e:
            logger.error(f"Failed to process paper {paper_id}: {e}")
            logger.error(traceback.format_exc())
            self._update_status(user_id, paper_id, PaperStatus.FAILED, str(e), error_type=type(e).__name__)

    def _update_status(
        self,
        user_id: str,
        paper_id: str,
        status: PaperStatus,
        message: str | None = None,
        **metadata,
    ):
        self.workspace.mark_paper_status(user_id, paper_id, status, message, **metadata)
