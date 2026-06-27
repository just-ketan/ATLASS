import os
import sys

from atlasse.knowledge_engine.paper_ingestion.arxiv_downloader import ArxivDownloader
from atlasse.knowledge_engine.paper_parser.paper_processor import PaperProcessor


class PaperLoader:
    def __init__(self):
        self.processed_dir = "data/processed_papers"
        self.downloader = ArxivDownloader()
        self.processor = PaperProcessor()

    def load(self, arxiv_id):
        json_path = os.path.join(self.processed_dir, f"{arxiv_id}.json")
        if os.path.exists(json_path):
            print(f"[ATLASS] Using cached paper: {json_path}", file=sys.stderr)
            return json_path
        print("[ATLASS] Paper not found locally. Downloading...", file=sys.stderr)
        pdf_path = self.downloader.download(arxiv_id)
        json_path = self.processor.process(pdf_path)
        return json_path