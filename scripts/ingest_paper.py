import argparse
import sys

from atlasse.knowledge_engine.paper_ingestion.arxiv_downloader import ArxivDownloader
from atlasse.knowledge_engine.paper_parser.paper_processor import PaperProcessor


def ingest(arxiv_id):
    import os
    raw_dir = "data/raw_papers"
    os.makedirs(raw_dir, exist_ok=True)
    pdf_path = os.path.join(raw_dir, f"{arxiv_id}.pdf")

    if not os.path.exists(pdf_path):
        print(f"[ATLASS] Downloading {arxiv_id}...")
        downloader = ArxivDownloader()
        pdf_path = downloader.download(arxiv_id)
    else:
        print(f"[ATLASS] Using local PDF: {pdf_path}")

    processor = PaperProcessor()
    json_path = processor.process(pdf_path)
    print(f"[ATLASS] Paper processed: {json_path}")
    return json_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("paper_id", nargs="?", default="2106.09685")
    args = parser.parse_args()
    ingest(args.paper_id)
