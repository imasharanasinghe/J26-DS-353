"""Synthetic student explanations with a known content gap, for validating the novice instrument.

Each variant is built from the graph, so the true understanding behind it is known:

* ``complete``     every fact of each concept, plus an explicit denial of each known-false statement
* ``missing_one``  the complete text with a single fact sentence left out (a missing step)
* ``half``         only the first fact per concept (no denials)
* ``wrong``        the first fact replaced by a known-false statement (a subtle misconception)
* ``garbled``      the complete text with the words of each sentence shuffled (content kept, sense lost)
* ``paraphrased``  the complete text with some words swapped for synonyms (same sense, new words)
* ``empty``        nothing

Expected ordering for a valid instrument: complete > missing_one > half > empty, wrong below
missing_one on net score, garbled below complete, paraphrased close to complete.
"""

from __future__ import annotations

import random
import re
from typing import Any

VARIANTS = ("complete", "missing_one", "half", "wrong", "garbled", "paraphrased", "empty")

SYNONYMS = {
    "hierarchical": "layered", "contiguous": "adjacent", "stores": "keeps", "solves": "handles",
    "smaller": "reduced", "implemented": "built", "traversed": "walked", "accessed": "reached",
    "complete": "fully filled", "stop": "finish", "follows": "obeys", "children": "child nodes",
}


def _denial(statement: str) -> str:
    """Deny a known-false statement. A statement that already holds a negation ("never") is turned
    into its affirmative opposite instead, because a double negation reads as the original claim."""
    if re.search(r"\bnever\b", statement):
        return re.sub(r"\bnever\b", "always", statement)
    body = statement[0].lower() + statement[1:]
    return "It is not true that " + body


def explain(kg: dict[str, Any], variant: str, seed: int = 0,
            concepts: list[str] | None = None) -> str:
    """A student's explanation of ``concepts`` (default: all) for one variant."""
    rng = random.Random(f"{variant}:{seed}")
    ids = concepts if concepts is not None else list(kg["concepts"])
    if variant == "empty":
        return ""
    sentences: list[str] = []
    for concept_id in ids:
        concept = kg["concepts"][concept_id]
        facts = list(concept.get("facts", []))
        false = list(concept.get("known_false", []))
        if variant in ("complete", "garbled", "paraphrased"):
            sentences += facts + [_denial(statement) for statement in false]
        elif variant == "missing_one":
            sentences += facts + [_denial(statement) for statement in false]
        elif variant == "half":
            sentences += facts[:1]
        elif variant == "wrong":
            sentences += ([false[0]] if false else []) + facts[1:]
        else:
            raise ValueError(f"unknown variant {variant}")
    if variant == "missing_one" and sentences:
        facts_at = [i for i, sentence in enumerate(sentences) if not sentence.startswith("It is not true")]
        del sentences[rng.choice(facts_at)]
    if variant == "garbled":
        sentences = [shuffle_words(sentence, rng) for sentence in sentences]
    if variant == "paraphrased":
        sentences = [paraphrase(sentence) for sentence in sentences]
    return " ".join(sentences)


def shuffle_words(sentence: str, rng: random.Random) -> str:
    words = sentence.rstrip(".").split()
    rng.shuffle(words)
    return " ".join(words) + "."


def paraphrase(sentence: str) -> str:
    def swap(match: re.Match[str]) -> str:
        word = match.group(0)
        return SYNONYMS.get(word.lower(), word)
    return re.sub(r"[A-Za-z]+", swap, sentence)


def weaker_writer(text: str, level: float, seed: int = 0) -> str:
    """Same content, weaker English: drop articles, swap letters in long words.

    ``level`` in [0, 1] is the share of eligible tokens altered. Used to measure whether the
    score depends on writing quality rather than on what was understood.
    """
    rng = random.Random(f"writer:{seed}")
    out: list[str] = []
    for token in text.split():
        bare = token.strip(".,;:")
        tail = token[len(bare):] if token.startswith(bare) else ""
        if bare.lower() in ("a", "an", "the") and rng.random() < level:
            continue
        if len(bare) > 4 and rng.random() < level * 0.5:
            i = rng.randrange(1, len(bare) - 2)
            bare = bare[:i] + bare[i + 1] + bare[i] + bare[i + 2:]
        out.append(bare + tail)
    return " ".join(out)


def as_concept_list(kg: dict[str, Any], concepts: list[str] | None = None) -> str:
    """The same facts as a terse concept list (the structured input option): subject, article and
    linking verb removed, e.g. ``- Heaps: complete binary tree; stored in array``."""
    ids = concepts if concepts is not None else list(kg["concepts"])
    lines = []
    for concept_id in ids:
        concept = kg["concepts"][concept_id]
        parts = []
        for fact in concept.get("facts", []):
            body = fact.rstrip(".")
            body = re.sub(r"^(A|An|The)\s+\w+(\s+\w+)?\s+(is|are|has|can be|can|follows|solves|needs|stores)\s+", "", body, count=1)
            body = re.sub(r"^(a|an|the)\s+", "", body, count=1)
            parts.append(body)
        lines.append(f"- {concept.get('name', concept_id)}: " + "; ".join(parts))
    return "\n".join(lines)
