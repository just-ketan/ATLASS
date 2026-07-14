"""Evidence-backed specification of a paper's proposed system."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from atlasse.knowledge_engine.orchestration.query_orchestrator import QueryOrchestrator
from atlasse.knowledge_engine.paper_embeddings.memory_builder import PaperMemory


SYSTEM_SPEC_VERSION = "1.0"
SYSTEM_SPEC_DIR = "data/system_specs"

# The questions are deliberately implementation-focused.  Their answers remain
# extractive retrieval evidence, rather than silently filling missing details.
SPEC_QUERIES = {
    "problem_statement": "what problem does this paper address and why is it important",
    "contribution": "what contribution or new method does this paper propose",
    "task_definition": "what task is the proposed system designed to solve",
    "inputs": "what inputs does the proposed model or system take",
    "outputs": "what outputs or predictions does the proposed model produce",
    "model_components": "what model architecture components or modules are proposed",
    "objective": "what loss objective or optimization target is used for training",
    "training_setup": "what optimizer training procedure and hyperparameters are used",
    "datasets": "what datasets benchmarks or corpora are used in experiments",
    "preprocessing": "what data preprocessing tokenization or input preparation is used",
    "metrics": "what evaluation metrics are reported",
    "baselines": "what baselines or comparison methods are used",
    "reported_results": "what main experimental results are reported",
    "limitations": "what limitations drawbacks or failure cases are mentioned",
}


class SystemSpecExtractor:
    """Create a reviewable implementation contract from paper retrieval evidence."""

    def __init__(self, paper_id: str, output_dir: str | Path = SYSTEM_SPEC_DIR):
        self.paper_id = paper_id
        self.output_dir = Path(output_dir)

    def extract(self, json_path: str | Path) -> dict:
        memory = PaperMemory(paper_id=self.paper_id)
        memory.build(str(json_path), paper_id=self.paper_id)
        orchestrator = QueryOrchestrator(memory)
        fields = {}

        for name, query in SPEC_QUERIES.items():
            response = orchestrator.ask_with_provenance(query)
            evidence = response.get("provenance", [])
            value = response.get("answer", "").strip()
            confidence = float(response.get("confidence", 0.0))
            supported = bool(evidence) and confidence >= 0.05 and bool(value)
            fields[name] = {
                "value": value if supported else None,
                "status": "extracted" if supported else "missing",
                "confidence": confidence if supported else 0.0,
                "citations": response.get("citations", ""),
                "evidence": evidence,
                "assumption": None,
            }

        return {
            "schema_version": SYSTEM_SPEC_VERSION,
            "paper_id": self.paper_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generation": {
                "strategy": "hybrid_retrieval_extract",
                "note": "Fields without adequate paper evidence are marked missing; they are not inferred.",
            },
            "fields": fields,
            "review": {"status": "needs_review", "notes": "", "version": 1},
        }

    def save(self, spec: dict) -> str:
        output_dir = self.output_dir / self.paper_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "system_spec.json"
        with open(output_path, "w") as file:
            json.dump(spec, file, indent=2)
        return str(output_path)

    @staticmethod
    def load(path: str | Path) -> dict:
        with open(path) as file:
            return json.load(file)
