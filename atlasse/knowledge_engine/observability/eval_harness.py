"""Retrieval evaluation harness with golden queries."""

GOLDEN_QUERIES = {
    "2106.09685": [
        {
            "query": "what is LoRA",
            "intents": ["definition", "method"],
            "expected_sections": ["abstract", "method", "introduction"],
            "min_confidence": 0.3,
            "must_contain": ["lora", "rank"],
        },
        {
            "query": "what datasets are used in experiments",
            "intents": ["dataset"],
            "expected_sections": ["experiment", "appendix", "empirical"],
            "min_confidence": 0.2,
            "must_contain": ["dataset", "roberta", "experiment", "benchmark", "appendix"],
        },
        {
            "query": "what are limitations of this method",
            "intents": ["limitations"],
            "expected_sections": ["conclusion", "discussion"],
            "min_confidence": 0.3,
            "must_contain": ["limit", "unclear", "drawback", "weakness", "fail", "mechanism"],
        },
        {
            "query": "what future work is mentioned",
            "intents": ["future_work"],
            "expected_sections": ["conclusion", "future"],
            "min_confidence": 0.2,
            "must_contain": ["future", "open", "extend", "investigate", "work", "question"],
        },
        {
            "query": "what powers does Pikachu have",
            "intents": [],
            "expected_sections": [],
            "min_confidence": 0.0,
            "max_confidence": 0.15,
            "must_contain": [],
        },
    ],
}


class EvalHarness:

    def __init__(self, memory):
        self.memory = memory

    def _section_hit(self, trace, expected_sections):
        if not expected_sections:
            return True
        sections = [c["section"] for c in trace.get("top_candidates", [])]
        return any(
            any(exp in sec for exp in expected_sections)
            for sec in sections
        )

    def _content_hit(self, trace, must_contain):
        if not must_contain:
            return True
        text = " ".join(
            s.get("text", "") for s in trace.get("ranked_sentences", [])
        ).lower()
        return any(term in text for term in must_contain)

    def evaluate_query(self, spec):
        self.memory.query(spec["query"])
        trace = self.memory.last_trace
        confidence = trace.get("confidence_score", 0.0)

        checks = {
            "confidence_ok": confidence >= spec.get("min_confidence", 0.0),
            "section_routing_ok": self._section_hit(trace, spec.get("expected_sections", [])),
            "content_ok": self._content_hit(trace, spec.get("must_contain", [])),
        }

        if "max_confidence" in spec:
            checks["confidence_ok"] = confidence <= spec["max_confidence"]

        passed = all(checks.values())
        return {
            "query": spec["query"],
            "passed": passed,
            "confidence": confidence,
            "checks": checks,
            "top_section": trace.get("top_candidates", [{}])[0].get("section"),
        }

    def run(self, paper_id="2106.09685"):
        specs = GOLDEN_QUERIES.get(paper_id, [])
        results = [self.evaluate_query(s) for s in specs]
        passed = sum(1 for r in results if r["passed"])
        return {
            "paper_id": paper_id,
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "pass_rate": passed / len(results) if results else 0.0,
            "results": results,
        }
