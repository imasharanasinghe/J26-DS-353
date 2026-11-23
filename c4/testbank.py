"""Hidden test for the teach-back exam.

Every answer key comes from the knowledge graph (facts, known-false statements, prerequisite
edges), never from an LLM's opinion. Recognition items (Bloom 1 and 2) are generated from the
graph; Apply and Analyze items (Bloom 3 and 4) are hand-written in ``data/teachback_items.json``
and carry the graph facts a reader needs in order to answer them.

An item is a dict::

    {"id", "concept", "bloom", "stem", "options": [{"text", "supports": [...]}], "answer": int,
     "requires": [...]}

``supports`` lists the statements that must be present in a text for that option to be
derivable from it. For the correct option these are the graph facts the item ``requires``; for a
distractor they are the false belief that would make it look right (so a student who writes a
false statement pulls the novice toward the matching distractor). ``"NOT: <statement>"`` means
the text must deny a known-false statement.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

DATA = Path(__file__).resolve().parent / "data"
HAND_ITEMS = DATA / "teachback_items.json"
OPTIONS_PER_ITEM = 4

# Recognition item for fact i of a concept is tagged Remember (first fact) or Understand (later).
RECOGNITION_LEVELS = (1, 2)


def _stable_order(seed_text: str, count: int) -> list[int]:
    """Deterministic shuffle so generated items do not always put the key first."""
    digest = hashlib.sha256(seed_text.encode()).digest()
    keyed = sorted(range(count), key=lambda index: digest[index % len(digest)] * 31 + index)
    return keyed


def recognition_items(kg: dict[str, Any]) -> list[dict[str, Any]]:
    concepts = kg.get("concepts", {})
    items: list[dict[str, Any]] = []
    for concept_id, concept in concepts.items():
        name = concept.get("name", concept_id)
        facts = concept.get("facts", [])
        own_false = list(concept.get("known_false", []))
        others = [fact for other_id, other in concepts.items() if other_id != concept_id
                  for fact in other.get("facts", [])]
        for index, fact in enumerate(facts):
            level = RECOGNITION_LEVELS[min(index, len(RECOGNITION_LEVELS) - 1)]
            options = [{"text": fact, "supports": [fact]}]
            for statement in own_false[:2]:
                options.append({"text": statement, "supports": [statement]})
            pool = [item for item in others if item not in facts]
            seed = f"{concept_id}:{index}"
            order = _stable_order(seed, max(len(pool), 1))
            for pick in order:
                if len(options) >= OPTIONS_PER_ITEM or not pool:
                    break
                options.append({"text": pool[pick], "supports": []})
            ordering = _stable_order(f"{seed}:opts", len(options))
            shuffled = [options[i] for i in ordering]
            items.append({
                "id": f"{concept_id}-recognise-{index + 1}",
                "concept": concept_id,
                "bloom": level,
                "stem": f"Which statement about {name} is true?",
                "options": shuffled,
                "answer": next(i for i, option in enumerate(shuffled) if option["text"] == fact),
                "requires": [fact],
            })
    return items


def hand_items(kg: dict[str, Any], path: Path = HAND_ITEMS) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))["items"]
    concepts = kg.get("concepts", {})
    items = []
    for entry in raw:
        if entry["concept"] not in concepts:
            continue
        item = dict(entry)
        item["requires"] = list(item["options"][item["answer"]]["supports"])
        items.append(item)
    return items


def build_test(kg: dict[str, Any], concepts: list[str] | None = None) -> list[dict[str, Any]]:
    """The hidden test, optionally limited to some concepts. Validates each item."""
    items = recognition_items(kg) + hand_items(kg)
    if concepts is not None:
        wanted = set(concepts)
        items = [item for item in items if item["concept"] in wanted]
    for item in items:
        validate_item(item)
    return items


def validate_item(item: dict[str, Any]) -> None:
    options = item["options"]
    if not 2 <= len(options) <= 6:
        raise ValueError(f"{item['id']}: needs 2 to 6 options")
    if not 0 <= item["answer"] < len(options):
        raise ValueError(f"{item['id']}: answer index out of range")
    texts = [option["text"] for option in options]
    if len(set(texts)) != len(texts):
        raise ValueError(f"{item['id']}: duplicate options")
    if item["bloom"] not in (1, 2, 3, 4, 5, 6):
        raise ValueError(f"{item['id']}: bad Bloom level")


def concept_levels(items: list[dict[str, Any]]) -> dict[str, list[int]]:
    table: dict[str, set[int]] = {}
    for item in items:
        table.setdefault(item["concept"], set()).add(item["bloom"])
    return {key: sorted(value) for key, value in table.items()}
