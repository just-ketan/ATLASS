"""Section-aware routing for hierarchical retrieval."""

INTENT_SECTION_MAP = {
    "definition": ["abstract", "introduction"],
    "problem": ["abstract", "introduction", "method"],
    "method": ["method", "abstract"],
    "dataset": ["experiment", "appendix"],
    "limitations": ["conclusion", "discussion"],
    "future_work": ["conclusion"],
    "experiment": ["experiment", "appendix"],
    "related_work": ["related_work"],
}


def detect_intent(query: str) -> list[str]:
    q = query.lower()
    intents = []

    if any(w in q for w in ["definition", "what is", "define", "meaning of"]):
        intents.append("definition")
    if any(w in q for w in ["problem", "address", "motivation", "challenge", "goal", "objective"]):
        intents.append("problem")
    if any(w in q for w in ["method", "how does", "architecture", "framework", "design", "propose", "proposed"]):
        intents.append("method")
    if any(w in q for w in ["dataset", "benchmark", "experiment", "evaluation", "result", "test", "metric", "accuracy"]):
        intents.append("dataset")
    if any(w in q for w in ["limit", "drawback", "weakness", "disadvantage", "fail", "negative"]):
        intents.append("limitations")
    if any(w in q for w in ["future", "open problem", "next step", "extension"]):
        intents.append("future_work")
    if any(w in q for w in ["related work", "prior work", "literature"]):
        intents.append("related_work")

    return intents


def get_section_categories(title: str) -> list[str]:
    title = title.lower()
    categories = []

    if "abstract" in title:
        categories.append("abstract")
    if any(k in title for k in ["introduction", "background", "motivation", "preliminar"]):
        categories.append("introduction")
    if "problem" in title or "statement" in title:
        categories.extend(["introduction", "method"])
    if any(k in title for k in ["method", "approach", "architecture", "framework", "design"]):
        categories.append("method")
    if any(k in title for k in ["experiment", "evaluation", "result", "analysis", "ablation", "setup", "empirical"]):
        categories.append("experiment")
    if "related work" in title or ("related" in title and "work" in title) or "literature review" in title:
        categories.append("related_work")
    if any(k in title for k in ["conclusion", "discussion", "limit", "future"]):
        categories.append("conclusion")
    if any(k in title for k in ["appendix", "annex"]) or title.strip() in ("f", "a", "b", "c", "d", "e"):
        categories.append("appendix")

    return categories or ["general"]


def target_categories_for_query(query: str) -> list[str]:
    intents = detect_intent(query)
    if not intents:
        return ["general"]
    cats = set()
    for intent in intents:
        cats.update(INTENT_SECTION_MAP.get(intent, ["general"]))
    return list(cats)


def section_matches_intent(section_title: str, target_categories: list[str]) -> bool:
    if not target_categories or target_categories == ["general"]:
        return True
    sec_cats = get_section_categories(section_title)
    return bool(set(sec_cats).intersection(target_categories))


def expand_query(query: str) -> list[str]:
    q = query.lower()
    sub_queries = [query]

    expansions = {
        "limit": [
            "limitations of the method",
            "drawbacks and disadvantages",
            "weaknesses or negative results",
        ],
        "method": [
            "proposed method architecture",
            "how does the model work",
            "design and implementation details",
        ],
        "dataset": [
            "datasets and benchmarks used in experiments",
            "evaluation setup and baseline models",
            "experimental results and task performance",
        ],
        "problem": [
            "problem statement and motivation",
            "challenges addressed by the paper",
        ],
        "future": [
            "future work and open questions",
            "conclusion and future research directions",
        ],
    }

    if any(w in q for w in ["limit", "drawback", "weakness"]):
        sub_queries.extend(expansions["limit"])
    if any(w in q for w in ["method", "how does", "architecture", "proposed", "lora"]):
        sub_queries.extend(expansions["method"])
    if any(w in q for w in ["dataset", "benchmark", "experiment", "evaluation"]):
        sub_queries.extend(expansions["dataset"])
    if any(w in q for w in ["problem", "address", "motivation"]):
        sub_queries.extend(expansions["problem"])
    if any(w in q for w in ["future", "open problem"]):
        sub_queries.extend(expansions["future"])

    return list(dict.fromkeys(sub_queries))
