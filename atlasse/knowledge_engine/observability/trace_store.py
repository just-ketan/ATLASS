import json
import os
import uuid
from datetime import datetime, timezone

TRACE_DIR = "data/traces"


class TraceStore:

    def __init__(self, trace_dir=TRACE_DIR):
        self.trace_dir = trace_dir
        os.makedirs(trace_dir, exist_ok=True)

    def save(self, trace: dict) -> str:
        trace_id = trace.get("trace_id") or str(uuid.uuid4())[:8]
        trace["trace_id"] = trace_id
        trace["timestamp"] = datetime.now(timezone.utc).isoformat()

        paper_id = trace.get("paper_id", "unknown")
        paper_dir = os.path.join(self.trace_dir, paper_id)
        os.makedirs(paper_dir, exist_ok=True)

        path = os.path.join(paper_dir, f"{trace_id}.json")
        with open(path, "w") as f:
            json.dump(trace, f, indent=2)
        return path

    def load(self, paper_id: str, trace_id: str) -> dict:
        path = os.path.join(self.trace_dir, paper_id, f"{trace_id}.json")
        with open(path) as f:
            return json.load(f)

    def list_traces(self, paper_id: str) -> list[str]:
        paper_dir = os.path.join(self.trace_dir, paper_id)
        if not os.path.isdir(paper_dir):
            return []
        return sorted(f.replace(".json", "") for f in os.listdir(paper_dir) if f.endswith(".json"))
