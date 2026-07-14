"""Deterministic concept and entity extraction for processed paper JSON."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


_STOPWORDS = {
    "about",
    "after",
    "also",
    "among",
    "based",
    "been",
    "between",
    "both",
    "can",
    "does",
    "during",
    "each",
    "from",
    "into",
    "more",
    "most",
    "only",
    "other",
    "over",
    "paper",
    "propose",
    "proposed",
    "results",
    "show",
    "shown",
    "such",
    "than",
    "that",
    "their",
    "there",
    "these",
    "this",
    "through",
    "using",
    "were",
    "when",
    "where",
    "which",
    "while",
    "with",
}

_KNOWN_TECHNICAL_TERMS = {
    "attention",
    "benchmark",
    "classification",
    "dataset",
    "decoder",
    "embedding",
    "encoder",
    "evaluation",
    "fine-tuning",
    "gradient",
    "inference",
    "language model",
    "learning",
    "loss",
    "model",
    "pretraining",
    "retrieval",
    "transformer",
}

_KNOWN_DATASETS = {"glue", "superglue", "squad", "imagenet", "cifar", "wikitext", "c4"}
_KNOWN_METHODS = {"lora", "qlora", "rag", "bert", "roberta", "gpt", "t5"}
_RELATION_CUES = (
    ("evaluated_on", re.compile(r"\b(evaluate|evaluated|evaluation|benchmark|experiment)\b", re.I)),
    ("compared_with", re.compile(r"\b(compare|compared|comparison|versus|\bvs\.?\b)\b", re.I)),
    ("uses", re.compile(r"\b(use|uses|used|using|apply|applied|employ|employed)\b", re.I)),
)


@dataclass
class ExtractedConcept:
    label: str
    frequency: int
    sections: list[str] = field(default_factory=list)
    chunk_ids: list[int] = field(default_factory=list)


@dataclass
class ExtractedEntity:
    label: str
    entity_type: str
    frequency: int
    sections: list[str] = field(default_factory=list)
    chunk_ids: list[int] = field(default_factory=list)


@dataclass
class ExtractedRelation:
    source: str
    target: str
    relation: str
    evidence_count: int
    sections: list[str] = field(default_factory=list)
    chunk_ids: list[int] = field(default_factory=list)


class ConceptExtractor:
    """Extract a lightweight semantic artifact without paid models."""

    ARTIFACT_DIR = "data/knowledge_artifacts"

    def __init__(self, paper_id: str | None = None, artifact_dir: str | Path | None = None):
        self.paper_id = paper_id
        self.artifact_dir = Path(artifact_dir or self.ARTIFACT_DIR)

    def extract_from_json(self, json_path: str | Path, max_concepts: int = 25, max_entities: int = 40) -> dict:
        with open(json_path) as f:
            data = json.load(f)

        sections = data.get("sections", [])
        chunks = []
        for idx, section in enumerate(sections):
            chunks.append({
                "id": idx,
                "section": section.get("title", "unknown"),
                "text": section.get("text", ""),
            })

        return self.extract_from_chunks(chunks, max_concepts=max_concepts, max_entities=max_entities)

    def extract_from_chunks(
        self,
        chunks: list[dict],
        max_concepts: int = 25,
        max_entities: int = 40,
    ) -> dict:
        concept_hits = self._collect_hits(chunks, self._extract_concepts)
        entity_hits = self._collect_hits(chunks, self._extract_entities)

        concepts = [
            asdict(item)
            for item in self._rank_concepts(concept_hits)[:max_concepts]
        ]
        entities = [
            asdict(item)
            for item in self._rank_entities(entity_hits)[:max_entities]
        ]
        relations = [
            asdict(item)
            for item in self._extract_relations(chunks, concepts, entities)
        ]

        return {
            "paper_id": self.paper_id,
            "concepts": concepts,
            "entities": entities,
            "relations": relations,
            "summary": {
                "concepts": len(concepts),
                "entities": len(entities),
                "relations": len(relations),
                "sections": len({chunk.get("section", "unknown") for chunk in chunks}),
            },
        }

    def save(self, artifact: dict, directory: str | Path | None = None) -> str:
        paper_id = artifact.get("paper_id") or self.paper_id or "default"
        output_dir = Path(directory) if directory else self.artifact_dir / paper_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "knowledge.json"
        with open(output_path, "w") as f:
            json.dump(artifact, f, indent=2)
        return str(output_path)

    @staticmethod
    def load(directory: str | Path) -> dict:
        with open(Path(directory) / "knowledge.json") as f:
            return json.load(f)

    @staticmethod
    def _collect_hits(chunks: list[dict], extractor):
        hits = defaultdict(lambda: {"count": 0, "sections": set(), "chunk_ids": set(), "type": None})
        for chunk in chunks:
            text = chunk.get("text", "")
            section = chunk.get("section", "unknown")
            chunk_id = chunk.get("id", 0)
            for label, kind in extractor(text):
                key = label.lower()
                hits[key]["count"] += 1
                hits[key]["sections"].add(section)
                hits[key]["chunk_ids"].add(chunk_id)
                hits[key]["type"] = kind
        return hits

    @staticmethod
    def _extract_concepts(text: str):
        candidates = []
        lower = text.lower()

        for term in _KNOWN_TECHNICAL_TERMS:
            if term in lower:
                candidates.append((term, "concept"))

        for match in re.finditer(r"\b([a-z][a-z\-]+(?:\s+[a-z][a-z\-]+){1,2})\b", lower):
            phrase = match.group(1)
            words = phrase.split()
            if any(word in _STOPWORDS for word in words):
                continue
            if len("".join(words)) < 8:
                continue
            candidates.append((phrase, "concept"))

        return candidates

    @staticmethod
    def _extract_entities(text: str):
        entities = []
        acronym_counts = Counter(re.findall(r"\b[A-Z][A-Z0-9\-]{1,}\b", text))
        for label, count in acronym_counts.items():
            if len(label) > 1 and label.lower() not in _STOPWORDS:
                entities.extend([(label, ConceptExtractor._entity_type(label, text))] * count)

        proper_terms = re.findall(r"\b[A-Z][A-Za-z0-9\-]{2,}(?:\s+[A-Z][A-Za-z0-9\-]{2,}){0,2}\b", text)
        for label in proper_terms:
            if label.lower() not in {"the", "this", "we", "our"}:
                entities.append((label, "named_entity"))

        citations = re.findall(r"\b([A-Z][a-z]+ et al\.?,? \d{4})\b", text)
        for label in citations:
            entities.append((label, "citation"))

        return entities

    @staticmethod
    def _entity_type(label: str, text: str) -> str:
        """Assign useful local roles without depending on a hosted NER model."""
        normalized = label.lower()
        if normalized in _KNOWN_DATASETS:
            return "dataset"
        if normalized in _KNOWN_METHODS:
            return "method"

        match = re.search(re.escape(label), text, re.I)
        if match:
            window = text[max(0, match.start() - 50):match.end() + 50].lower()
            if re.search(r"\b(dataset|benchmark|corpus|test set|training set)\b", window):
                return "dataset"
            if re.search(r"\b(method|model|architecture|approach|framework|algorithm)\b", window):
                return "method"
        return "acronym"

    @staticmethod
    def _rank_concepts(hits) -> list[ExtractedConcept]:
        concepts = [
            ExtractedConcept(
                label=label,
                frequency=data["count"],
                sections=sorted(data["sections"]),
                chunk_ids=sorted(data["chunk_ids"]),
            )
            for label, data in hits.items()
        ]
        return sorted(concepts, key=lambda item: (-item.frequency, item.label))

    @staticmethod
    def _rank_entities(hits) -> list[ExtractedEntity]:
        entities = [
            ExtractedEntity(
                label=label,
                entity_type=data["type"] or "entity",
                frequency=data["count"],
                sections=sorted(data["sections"]),
                chunk_ids=sorted(data["chunk_ids"]),
            )
            for label, data in hits.items()
        ]
        return sorted(entities, key=lambda item: (-item.frequency, item.label))

    @classmethod
    def _extract_relations(cls, chunks: list[dict], concepts: list[dict], entities: list[dict]) -> list[ExtractedRelation]:
        concept_labels = [item["label"] for item in concepts]
        entity_labels = [item["label"] for item in entities]
        entity_types = {item["label"].lower(): item.get("entity_type", "entity") for item in entities}
        hits = defaultdict(lambda: {"count": 0, "sections": set(), "chunk_ids": set()})

        for chunk in chunks:
            text = chunk.get("text", "")
            section = chunk.get("section", "unknown")
            chunk_id = chunk.get("id", 0)
            for sentence in cls._sentences(text):
                present_concepts = cls._labels_present(sentence, concept_labels)
                present_entities = cls._labels_present(sentence, entity_labels)
                nodes = present_concepts + present_entities
                citations = [label for label in present_entities if entity_types.get(label.lower()) == "citation"]
                datasets = [label for label in present_entities if entity_types.get(label.lower()) == "dataset"]
                non_citations = [label for label in nodes if label not in citations]

                for source in non_citations:
                    for citation in citations:
                        cls._record_relation(hits, source, citation, "supported_by_citation", section, chunk_id)

                cue_relations = [relation for relation, pattern in _RELATION_CUES if pattern.search(sentence)]
                for relation in cue_relations:
                    targets = datasets if relation == "evaluated_on" and datasets else non_citations
                    for source in non_citations:
                        for target in targets:
                            if source != target:
                                cls._record_relation(hits, source, target, relation, section, chunk_id)

                for left_index, source in enumerate(non_citations):
                    for target in non_citations[left_index + 1:]:
                        cls._record_relation(hits, source, target, "co_occurs_with", section, chunk_id)

        relations = [
            ExtractedRelation(
                source=source,
                target=target,
                relation=relation,
                evidence_count=data["count"],
                sections=sorted(data["sections"]),
                chunk_ids=sorted(data["chunk_ids"]),
            )
            for (source, target, relation), data in hits.items()
        ]
        return sorted(relations, key=lambda item: (-item.evidence_count, item.relation, item.source, item.target))

    @staticmethod
    def _sentences(text: str) -> list[str]:
        return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]

    @staticmethod
    def _record_relation(hits, source: str, target: str, relation: str, section: str, chunk_id: int):
        key = (source, target, relation)
        hits[key]["count"] += 1
        hits[key]["sections"].add(section)
        hits[key]["chunk_ids"].add(chunk_id)

    @staticmethod
    def _labels_present(text: str, labels: list[str]) -> list[str]:
        lower = text.lower()
        present = []
        for label in labels:
            if re.search(rf"(?<![a-z0-9\-]){re.escape(label.lower())}(?![a-z0-9\-])", lower):
                present.append(label)
        return present
