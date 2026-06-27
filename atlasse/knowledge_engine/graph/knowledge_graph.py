"""Phase 9: lightweight knowledge graph over paper chunks."""

import json
import os
import re
from collections import defaultdict


class KnowledgeGraph:
    GRAPH_DIR = "data/knowledge_graphs"

    def __init__(self, paper_id=None):
        self.paper_id = paper_id
        self.nodes = {}
        self.edges = []
        self._node_counter = 0

    def _add_node(self, node_type, label, metadata=None):
        for nid, node in self.nodes.items():
            if node["type"] == node_type and node["label"].lower() == label.lower():
                return nid
        nid = self._node_counter
        self._node_counter += 1
        self.nodes[nid] = {
            "id": nid,
            "type": node_type,
            "label": label,
            "metadata": metadata or {},
        }
        return nid

    def _add_edge(self, src, dst, relation, metadata=None):
        self.edges.append({
            "source": src,
            "target": dst,
            "relation": relation,
            "metadata": metadata or {},
        })

    @staticmethod
    def _extract_entities(text):
        patterns = [
            r"\b([A-Z][A-Za-z0-9\-]{2,}(?:-[A-Z][A-Za-z0-9]+)*)\b",
            r"\b(LoRA|GPT-\d+|RoBERTa|DeBERTa|BERT|Transformer|WikiSQL|GLUE|SuperGLUE)\b",
        ]
        found = set()
        for pat in patterns:
            for m in re.finditer(pat, text):
                term = m.group(1)
                if len(term) > 2 and term.lower() not in {"the", "we", "our", "this"}:
                    found.add(term)
        return list(found)[:10]

    @staticmethod
    def _extract_citations(text):
        return re.findall(r"([A-Z][a-z]+ et al\.?, \d{4})", text)

    def build_from_chunks(self, chunk_metadata: dict):
        paper_node = self._add_node("paper", self.paper_id or "unknown")

        for chunk_id, chunk in chunk_metadata.items():
            section = chunk.get("section", "unknown")
            section_node = self._add_node("section", section)
            chunk_node = self._add_node("chunk", f"chunk_{chunk_id}", {"chunk_id": chunk_id})
            self._add_edge(paper_node, section_node, "has_section")
            self._add_edge(section_node, chunk_node, "contains")

            text = chunk.get("text", "")
            for entity in self._extract_entities(text):
                entity_node = self._add_node("entity", entity)
                self._add_edge(chunk_node, entity_node, "mentions")

            for citation in self._extract_citations(text):
                cite_node = self._add_node("citation", citation)
                self._add_edge(chunk_node, cite_node, "cites")

        return self

    def query_entities(self, entity_name):
        entity_name_lower = entity_name.lower()
        matching = [
            nid for nid, n in self.nodes.items()
            if n["type"] == "entity" and entity_name_lower in n["label"].lower()
        ]
        chunks = []
        for eid in matching:
            for edge in self.edges:
                if edge["target"] == eid and edge["relation"] == "mentions":
                    chunk_node = self.nodes.get(edge["source"], {})
                    cid = chunk_node.get("metadata", {}).get("chunk_id")
                    if cid is not None:
                        chunks.append(cid)
        return chunks

    def get_relations(self, node_id):
        return [
            e for e in self.edges
            if e["source"] == node_id or e["target"] == node_id
        ]

    def save(self, directory=None):
        directory = directory or os.path.join(self.GRAPH_DIR, self.paper_id or "default")
        os.makedirs(directory, exist_ok=True)
        with open(os.path.join(directory, "graph.json"), "w") as f:
            json.dump({"nodes": self.nodes, "edges": self.edges}, f, indent=2)

    @classmethod
    def load(cls, directory):
        with open(os.path.join(directory, "graph.json")) as f:
            data = json.load(f)
        graph = cls()
        graph.nodes = {int(k): v for k, v in data["nodes"].items()}
        graph.edges = data["edges"]
        graph._node_counter = max(graph.nodes.keys(), default=-1) + 1
        return graph

    def summary(self):
        by_type = defaultdict(int)
        for n in self.nodes.values():
            by_type[n["type"]] += 1
        return dict(by_type)
