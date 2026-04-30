import json
import os

from .pdf_parser import PDFParser
from .section_extractor import SectionExtractor

class PaperProcessor:
    def __init__(self, output_dir="data/processed_papers"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def process(self, pdf_path):
        parser = PDFParser(pdf_path=pdf_path)
        text = parser.extract_text()

        extractor = SectionExtractor()
        # sections = extractor.extract(text)

        # paper_json = {
        #     "sections" : sections
        # }
        paper_json = {
            "full_text": text
        }

        filename = os.path.basename(pdf_path).replace(".pdf", ".json")
        output_path = os.path.join(self.output_dir, filename)
        with open(output_path, "w") as f:
            json.dump(paper_json, f, indent=2)
        return output_path