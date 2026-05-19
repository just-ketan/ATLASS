from .paper_understanding_engine import PaperUnderstandingEngine

class StructuredExtractor:
    def __init__(self, json_path):
        self.engine = PaperUnderstandingEngine(json_path)
    
    def extract(self):
        res = {}
        fields = {
            "problem": "what problem does this paper address in machine learning or transformers",
            "method": "what method is proposed in this paper lora low rank adaptation",
            "dataset": "what datasets or benchmarks are used in this paper experiments",
            "limitations": "what are limitations or drawbacks of this method mentioned in paper",
            "future_work": "what future work or open problems are mentioned in conclusion"
        }
        for k, q in fields.items():
            ans = self.engine.ask(q)
            res[k] = ans
        return res