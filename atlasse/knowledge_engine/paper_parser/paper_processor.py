import json
import os
import re
from .pdf_parser import PDFParser

class PaperProcessor:
    def __init__(self, output_dir="data/processed_papers"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def process(self, pdf_path):
        parser = PDFParser(pdf_path=pdf_path)
        text = parser.extract_text()

        sections = self.extract_sections(text)

        # paper_json = {
        #     "sections" : sections
        # }
        paper_json = {
            "full_text": text,
            "sections": sections
        }
        print("\n[ATLASS] Parsed Sections:\n")
        for s in sections:
            print("-", s["title"])

        filename = os.path.basename(pdf_path).replace(".pdf", ".json")
        output_path = os.path.join(self.output_dir, filename)
        with open(output_path, "w") as f:
            json.dump(paper_json, f, indent=2)
        return output_path

    def extract_sections(self, text):
        pattern = r'\n\s*((?:\d+\s+)?[A-Z][A-Z\s\-&]{3,}|(?:\d+\s+[A-Z][^\n]+))\n'
        # Fix broken OCR section titles
        text = re.sub(r'\n(\d+)\n([A-Z])', r'\n\1 \2', text)

        matches = list(re.finditer(pattern, text))
        sections = []
        seen_titles = set()
        for i in range(len(matches)):
            title = matches[i].group(1).strip()
            # Normalize appendix subsection markers
            title = re.sub(r'^([a-z])\s+', lambda m: m.group(1).upper() + " ", title)
            
            title_lower = title.lower()
            # Reject absurdly long titles
            if len(title.split()) > 12:
                continue

            valid_keywords = [
                # Core paper structure
                "abstract",
                "introduction",
                "background",
                "motivation",
                "problem",

                # Methodology
                "method",
                "approach",
                "architecture",
                "framework",

                # Evaluation
                "experiment",
                "evaluation",
                "results",
                "analysis",
                "ablation",

                # Research discussion
                "discussion",
                "limitation",
                "future",
                "conclusion",
                "related work",

                # Metadata
                "reference",
                "appendix"
            ]

            if not self.is_valid_section_title(title):
                continue

            # keep only meaningful academic sections
            if not any(k in title_lower for k in valid_keywords):
                continue
            # Skip tiny numeric junk
            if len(title.split()) <= 2 and any(c.isdigit() for c in title):
                continue

            start = matches[i].end()
            end = (
                matches[i + 1].start()
                if i + 1 < len(matches)
                else len(text)
            )
            content = text[start:end].strip()

            normalized = title.lower().strip()
            if normalized in seen_titles:
                continue
            seen_titles.add(normalized)

            sections.append({
                "title": title.lower(),
                "level": self.get_section_level(title),
                "text": content
            })
        return sections

    def is_valid_section_title(self, title):
        title = title.strip()

        if "#" in title:
            return False
    
        # Too short
        if len(title) < 5:
            return False
        
        # Reject suspicious lowercase fragments
        if title[0].islower():
            return False
            
        # Too long
        if len(title.split()) > 12:
            return False

        # Too numeric
        digit_ratio = sum(c.isdigit() for c in title) / max(len(title), 1)

        if digit_ratio > 0.25:
            return False

        # Too many symbols
        special_ratio = sum(
            not c.isalnum() and not c.isspace()
            for c in title
        ) / max(len(title), 1)

        if special_ratio > 0.15:
            return False

        # Too many ALLCAPS tokens = often tables
        caps_words = sum(
            w.isupper() for w in title.split()
        )

        if caps_words > 4:
            return False

        # Likely metric/table row
        metric_words = [
            "bleu",
            "rouge",
            "meteor",
            "nist",
            "accuracy",
            "f1",
            "precision",
            "recall"
        ]
        table_like = [
            "& method",
            "trainable",
            "hyperparameters",
        ]   
        if any(t in title.lower() for t in table_like):
            return False
        metric_count = sum(
            w in title.lower()
            for w in metric_words
        )

        if metric_count >= 2:
            return False

        return True

    def get_section_level(self, title):
        title = title.strip()
        if re.match(r'^\d+\s', title):
            return 1
        if re.match(r'^[A-Z]\s+', title):
            return 2
        return 0