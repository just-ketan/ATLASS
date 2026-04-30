# parse papers downloaded via arxiv

import fitz

class PDFParser:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
    
    def extract_text(self):
        doc = fitz.open(self.pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        
        return full_text