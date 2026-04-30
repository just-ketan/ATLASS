# extract sections
import re
class SectionExtractor:
    SECTION_PATTERN=r"\n\d+\s+[A-Z][^\n]+"

    def extract(self, text):
        matches = list(re.finditer(self.SECTION_PATTERN, text))
        sections = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i+1].start() if i+1 < len(matches) else len(text)
            title = match.group().strip()
            section_text = text[start:end]
            sections.append({
                "title" : title,
                "text" : section_text
            })
        return sections