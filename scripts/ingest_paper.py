#ingest paper

from atlasse.knowledge_engine.paper_ingestion.arxiv_downloader import ArxivDownloader
from atlasse.knowledge_engine.paper_parser.paper_processor import PaperProcessor

def ingest(arxiv_id):
    downloader = ArxivDownloader()
    pdf_path = downloader.download(arxiv_id)
    processor = PaperProcessor()
    json_path = processor.process(pdf_path)
    print("paper processed: ", json_path)

if __name__ == "__main__":
    ingest("2106.09685") # test