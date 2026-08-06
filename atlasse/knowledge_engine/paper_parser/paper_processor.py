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
        text = re.sub(r'\n(\d+)\n([A-Z])', r'\n\1 \2', text)
        matches = list(re.finditer(pattern, text))
        
        sections = []
        seen_titles = set()
        
        preface_end = matches[0].start() if matches else len(text)
        current_section = {
            "title": "preface",
            "canonical_class": "abstract",
            "level": 1,
            "text": text[0:preface_end].strip()
        }
        sections.append(current_section)

        for i in range(len(matches)):
            title = matches[i].group(1).strip()
            title = re.sub(r'^([a-z])\s+', lambda m: m.group(1).upper() + " ", title)
            title_lower = title.lower()

            start = matches[i].end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()

            valid_keywords = [
                "abstract", "introduction", "background", "motivation", "problem",
                "method", "approach", "architecture", "framework",
                "experiment", "evaluation", "results", "analysis", "ablation",
                "discussion", "limitation", "future", "conclusion", "related work",
                "reference", "appendix"
            ]

            is_valid = self.is_valid_section_title(title)
            has_keyword = any(k in title_lower for k in valid_keywords)
            # Accept if valid and (has a keyword OR doesn't look like a tiny numeric fragment)
            is_meaningful = is_valid and (has_keyword or (len(title.split()) > 1 and not any(c.isdigit() for c in title)))
            
            # Reject absurdly long titles
            if len(title.split()) > 12:
                is_meaningful = False

            normalized = title.lower().strip()
            
            if is_meaningful and normalized not in seen_titles:
                seen_titles.add(normalized)
                current_section = {
                    "title": title.lower(),
                    "canonical_class": self.get_canonical_class(title),
                    "level": self.get_section_level(title),
                    "text": content
                }
                sections.append(current_section)
            else:
                current_section["text"] += f"\n\n{title}\n\n{content}"

        return [s for s in sections if len(s["text"]) > 50]

    def get_canonical_class(self, title):
        title = title.lower()
        if "abstract" in title: return "abstract"
        if any(k in title for k in ["introduction", "background", "motivation", "preliminar"]): return "introduction"
        if "problem" in title or "statement" in title: return "problem"
        if any(k in title for k in ["method", "approach", "architecture", "framework", "design", "model"]): return "methodology"
        if any(k in title for k in ["experiment", "evaluation", "result", "analysis", "ablation", "setup", "empirical", "dataset"]): return "evaluation"
        if "related work" in title or ("related" in title and "work" in title) or "literature review" in title: return "related_work"
        if any(k in title for k in ["conclusion", "discussion", "limit", "future"]): return "conclusion"
        if any(k in title for k in ["appendix", "annex"]): return "appendix"
        return "general"

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