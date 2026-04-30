import os
from atlasse.knowledge_engine.paper_ingestion.arxiv_downloader import ArxivDownloader
from atlasse.knowledge_engine.paper_parser.paper_processor  import PaperProcessor

class PaperLoader:
    def __init__(self):
        self.processed_dir = "/data/processed_papers"
        self.downloader = ArxivDownloader()
        self.processor = PaperProcessor()

    def load(self, arxiv_id):
        json_path = os.path.join(self.processed_dir, f"{arxiv_id}.json")
        # if already exists
        if os.path.exists(json_path):
            print("[ATLASS using cached paper:", json_path)
            return json_path
        # fresh download
        print("[ATLASS] Paper not found locally, Downloading...")
        pdf_path = self.downloader.download(arxiv_id)
        json_path = self.processor.process(pdf_path)
        return json_path