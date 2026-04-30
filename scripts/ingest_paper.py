# ingest_paper.py

import os

from atlasse.knowledge_engine.paper_ingestion.arxiv_downloader import ArxivDownloader
from atlasse.knowledge_engine.paper_parser.paper_processor import PaperProcessor


def ingest(arxiv_id):

    raw_dir = "data/raw_papers"
    os.makedirs(raw_dir, exist_ok=True)

    pdf_path = os.path.join(raw_dir, f"{arxiv_id}.pdf")

    # PDF already exists locally
    if os.path.exists(pdf_path):
        print(f"[ATLASS] Using local PDF: {pdf_path}")

    # Need to download
    else:
        print(f"[ATLASS] PDF not found locally. Downloading {arxiv_id}...")
        downloader = ArxivDownloader()
        pdf_path = downloader.download(arxiv_id)

    # Process PDF → JSON
    processor = PaperProcessor()
    json_path = processor.process(pdf_path)

    print("[ATLASS] Paper processed:", json_path)

    return json_path


if __name__ == "__main__":
    ingest("2106.09685")  # test