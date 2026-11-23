"""Knowledge-restricted AI novices for the teach-back exam.

A novice sees ONLY the student's text and takes the hidden test (``c4.testbank``). It may answer
"I don't know" (``None``). Two backends share one interface:

* ``LexicalNovice``: deterministic reference reader. It derives an option only when the text states
  every statement that option needs, so it cannot know anything the text does not say (zero leakage
  by construction), has no run-to-run variance, and is blind to word order and paraphrase. It is a
  control and a lower bound, not the candidate instrument.
* ``OllamaNovice``: a local LLM told to answer only from the text. This is the candidate
  instrument. Prompting alone does not remove the model's own knowledge, so ``c4.instrument``
  measures its leakage, discrimination and run-to-run reliability before any score is used.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .pipeline import C4Pipeline

LETTERS = "ABCDEF"
NOT_PREFIX = "NOT: "
RECALL_MIN = 0.75
CONFLICT_OVERLAP = 0.5


class Novice(Protocol):
    name: str

    def answer(self, text: str, item: dict[str, Any]) -> int | None:
        """Index of the chosen option, or None for 'I don't know'."""


# ---------------------------------------------------------------- text evidence


def split_statements(text: str) -> list[str]:
    """Sentences, bullet lines and 'term: meaning' lines, plus comma/semicolon clauses."""
    pieces: list[str] = []
    for line in re.split(r"[\n\r]+", text):
        line = re.sub(r"^\s*([-*•]|\d+[.)])\s*", "", line).strip()
        if not line:
            continue
        # Concept-list input ("Heap: complete binary tree; stored in array"): each part is read
        # with its term as subject, so a short list is not marked down for dropping full sentences.
        listed = re.match(r"^([^:.;]{2,40}):\s*(.+)$", line)
        if listed:
            pieces.extend(f"{listed.group(1)} {part.strip()}" for part in listed.group(2).split(";") if part.strip())
            continue
        pieces.extend(part.strip() for part in re.split(r"(?<=[.!?])\s+", line) if part.strip())
    return pieces


class TextEvidence:
    """What a piece of student text states, checked against graph statements.

    ``universe`` is every graph statement with its truth value (facts are true, known-false
    statements are false). A statement counts as stated only when the text is closer to it than to a
    conflicting statement of the opposite truth value, so 'first-in-first-out' cannot pass for
    'last-in-first-out'.
    """

    def __init__(self, text: str, universe: dict[str, bool]) -> None:
        self.sentences = split_statements(text)
        self.universe = universe
        self._words = [C4Pipeline._content_words(sentence) for sentence in self.sentences]
        self._negated = [C4Pipeline._negated(sentence) for sentence in self.sentences]
        self._cache: dict[str, bool] = {}

    def _conflicts(self, statement: str) -> list[str]:
        words = C4Pipeline._content_words(statement)
        truth = self.universe.get(statement)
        return [other for other, value in self.universe.items()
                if other != statement and value != truth
                and C4Pipeline._jaccard(words, C4Pipeline._content_words(other)) >= CONFLICT_OVERLAP]

    def states(self, statement: str) -> bool:
        """True when some sentence asserts this statement (with matching polarity)."""
        if statement in self._cache:
            return self._cache[statement]
        if statement.startswith(NOT_PREFIX):
            result = self._denies(statement[len(NOT_PREFIX):])
        else:
            result = self._asserts(statement)
        self._cache[statement] = result
        return result

    def _asserts(self, statement: str) -> bool:
        target = C4Pipeline._content_words(statement)
        if not target:
            return False
        polarity = C4Pipeline._negated(statement)
        rivals = [(C4Pipeline._content_words(item)) for item in self._conflicts(statement)]
        for words, negated in zip(self._words, self._negated):
            if negated != polarity or len(target & words) / len(target) < RECALL_MIN:
                continue
            score = C4Pipeline._jaccard(target, words)
            if all(score > C4Pipeline._jaccard(rival, words) for rival in rivals):
                return True
        return False

    def _denies(self, statement: str) -> bool:
        target = C4Pipeline._content_words(statement)
        if not target:
            return False
        for words, negated in zip(self._words, self._negated):
            if negated and len(target & words) / len(target) >= RECALL_MIN:
                return True
        return False


def graph_universe(kg: dict[str, Any]) -> dict[str, bool]:
    universe: dict[str, bool] = {}
    for concept in kg.get("concepts", {}).values():
        for fact in concept.get("facts", []):
            universe[fact] = True
        for statement in concept.get("known_false", []):
            universe[statement] = False
    return universe


# ------------------------------------------------------------------ backends


class LexicalNovice:
    name = "lexical"

    def __init__(self, kg: dict[str, Any]) -> None:
        self.universe = graph_universe(kg)

    def answer(self, text: str, item: dict[str, Any]) -> int | None:
        evidence = TextEvidence(text, self.universe)
        derivable = [
            index for index, option in enumerate(item["options"])
            if option["supports"] and all(evidence.states(statement) for statement in option["supports"])
        ]
        # Exactly one derivable option: take it. None, or a contradiction in the text: don't know.
        return derivable[0] if len(derivable) == 1 else None


def render_prompt(text: str, item: dict[str, Any]) -> tuple[str, str]:
    system = (
        "You are a student who knows NOTHING about this subject except what is written in the TEXT. "
        "Answer only from the TEXT. Do not use any outside knowledge. If the TEXT does not give you "
        "what you need, answer UNKNOWN. Never guess."
    )
    options = "\n".join(f"{LETTERS[i]}) {option['text']}" for i, option in enumerate(item["options"]))
    shown = text.strip() or "(the text is empty)"
    user = (f"TEXT:\n<<<\n{shown}\n>>>\n\nQUESTION: {item['stem']}\n{options}\n\n"
            "Reply as JSON with one field `answer`: a single option letter, or UNKNOWN.")
    return system, user


def parse_answer(content: str, option_count: int) -> int | None:
    try:
        value = str(json.loads(content).get("answer", "")).strip().upper()
    except (ValueError, AttributeError):
        match = re.search(r"\b([A-F]|UNKNOWN)\b", content.upper())
        value = match.group(1) if match else ""
    if value and value[0] in LETTERS[:option_count] and value != "UNKNOWN":
        return LETTERS.index(value[0])
    return None


class OllamaNovice:
    """A local LLM that is told to answer only from the student's text."""

    def __init__(self, model: str = "qwen3:4b", endpoint: str = "http://localhost:11434/api/chat",
                 temperature: float = 0.0, seed: int | None = None, timeout: float = 120.0,
                 transport: Callable[[dict[str, Any]], dict[str, Any]] | None = None) -> None:
        self.model = model
        self.endpoint = endpoint
        self.temperature = temperature
        self.seed = seed
        self.timeout = timeout
        self.transport = transport or self._post
        self.name = f"ollama:{model}"

    def with_seed(self, seed: int, temperature: float | None = None) -> "OllamaNovice":
        return OllamaNovice(self.model, self.endpoint,
                            self.temperature if temperature is None else temperature,
                            seed, self.timeout, self.transport)

    def answer(self, text: str, item: dict[str, Any]) -> int | None:
        system, user = render_prompt(text, item)
        options: dict[str, Any] = {"temperature": self.temperature, "num_predict": 40}
        if self.seed is not None:
            options["seed"] = self.seed
        payload = {
            "model": self.model, "stream": False, "think": False,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "format": {"type": "object", "properties": {"answer": {"type": "string"}}, "required": ["answer"]},
            "options": options,
        }
        reply = self.transport(payload)
        return parse_answer(reply.get("message", {}).get("content", ""), len(item["options"]))

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(self.endpoint, data=json.dumps(payload).encode(),
                          headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError("Ollama is unavailable; start `ollama serve`.") from exc


# ------------------------------------------------------------------- scoring


def take_test(novice: Novice, text: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for item in items:
        chosen = novice.answer(text, item)
        results.append({
            "id": item["id"], "concept": item["concept"], "bloom": item["bloom"],
            "chosen": chosen, "correct": chosen == item["answer"], "abstained": chosen is None,
            "options": len(item["options"]),
        })
    return results


def traceability(text: str, item: dict[str, Any], universe: dict[str, bool]) -> float:
    """Share of the statements an item requires that the student's text actually states.

    Depth check: a correct novice answer whose required facts are absent from the text came from
    the novice's own reasoning or memory, not from what the student taught.
    """
    required = item.get("requires", [])
    if not required:
        return 0.0
    evidence = TextEvidence(text, universe)
    return sum(evidence.states(statement) for statement in required) / len(required)


def summarise(results: list[dict[str, Any]], key: str | None = None) -> dict[Any, dict[str, float]]:
    """Proportion correct, abstained and net (right minus wrong/(k-1)) per group, or overall."""
    groups: dict[Any, list[dict[str, Any]]] = {}
    for row in results:
        label = "all" if key is None else (row[key] if key != "concept_bloom" else (row["concept"], row["bloom"]))
        groups.setdefault(label, []).append(row)
    table: dict[Any, dict[str, float]] = {}
    for label, rows in groups.items():
        count = len(rows)
        right = sum(row["correct"] for row in rows)
        wrong = sum((not row["correct"]) and (not row["abstained"]) for row in rows)
        penalty = sum(1 / (row["options"] - 1) for row in rows if (not row["correct"]) and (not row["abstained"]))
        table[label] = {
            "items": count, "score": right / count, "wrong": wrong / count,
            "abstained": sum(row["abstained"] for row in rows) / count,
            "net": (right - penalty) / count,
        }
    return table
