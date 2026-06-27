from .paper_understanding_engine import PaperUnderstandingEngine

FIELD_QUERIES = {
    "problem": "what problem does this paper address in machine learning or transformers",
    "method": "what method is proposed in this paper",
    "dataset": "what datasets or benchmarks are used in this paper experiments",
    "limitations": "what are limitations or drawbacks of this method mentioned in paper",
    "future_work": "what future work or open problems are mentioned in conclusion",
}


class StructuredExtractor:

    def __init__(self, json_path, paper_id=None, force_rebuild=False):
        self.engine = PaperUnderstandingEngine(json_path, paper_id=paper_id, force_rebuild=force_rebuild)
        self.paper_id = self.engine.paper_id

    def extract(self):
        result = {}
        provenance = {}
        for field, query in FIELD_QUERIES.items():
            response = self.engine.ask_with_provenance(query)
            result[field] = response["answer"]
            provenance[field] = {
                "citations": response.get("citations", ""),
                "provenance": response.get("provenance", []),
                "confidence": response.get("confidence", 0.0),
            }
        return {"fields": result, "provenance": provenance, "paper_id": self.paper_id}

    def extract_fields_only(self):
        return self.extract()["fields"]
