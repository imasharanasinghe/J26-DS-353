"""Pilot Bloom-level estimator and its evaluation against a labelled item set.

The estimator is a verb-cue matcher: it returns the highest revised-taxonomy level whose cue
word appears in the sentence, and 1 (Remember) when none does. It is deliberately simple and
inspectable; ``score_estimator`` measures how often it agrees with human-assigned levels
(``c4/data/bloom_items.json``) so the claim "this sentence is at level N" is backed by a number.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Sequence

# Cue verbs per level (highest level checked first). V1 is the original PP1 lexicon.
CUES_V1: tuple[tuple[int, tuple[str, ...]], ...] = (
    (6, ("design", "create", "construct", "develop")),
    (5, ("evaluate", "justify", "critique", "assess")),
    (4, ("analyze", "analyse", "compare", "differentiate", "examine")),
    (3, ("implement", "apply", "solve", "compute")),
    (2, ("explain", "describe", "why", "summarize")),
)


# V2 lexicon: standard revised-taxonomy verb lists, applied only to learner tasks (a question
# or an instruction). A declarative sentence ("A heap can be used to build queues") is
# a statement and stays at Remember, so ordinary explanation text is not mistaken for a
# demanding task. Extended after reading errors on the dev split only.
CUES_V2: tuple[tuple[int, tuple[str, ...]], ...] = (
    (6, ("design", "create", "construct", "develop", "propose", "invent", "compose",
         "formulate", "devise", "build", "generate", "plan")),
    (5, ("evaluate", "justify", "critique", "assess", "judge", "defend", "recommend",
         "argue", "decide", "appraise", "tradeoffs", "tradeoff")),
    (4, ("analyze", "analyse", "compare", "contrast", "differentiate", "distinguish",
         "examine", "difference", "differences", "break")),
    (3, ("implement", "apply", "solve", "compute", "calculate", "execute", "demonstrate",
         "trace", "write", "convert", "determine", "perform", "carry")),
    (2, ("explain", "describe", "why", "summarize", "interpret", "paraphrase", "classify",
         "discuss", "illustrate", "example")),
)
PHRASE_CUES: tuple[tuple[int, str], ...] = (
    (2, "own words"),
    (4, "which part"),
    (5, "trade-off"),
)
POLITE_FRAMES = ("can you", "could you", "how would you", "would you", "please")
IMPERATIVE_STARTS = frozenset(
    {"recall", "define", "list", "name", "state", "identify", "give", "use", "show"}
    | {verb for _, verbs in CUES_V2 for verb in verbs}
)


def estimate_level(sentence: str, cues: Sequence[tuple[int, tuple[str, ...]]] = CUES_V1) -> int:
    """V1: highest cue level anywhere in the sentence; Remember when none matches."""
    words = set(re.findall(r"[a-z]+", sentence.lower()))
    for level, level_cues in cues:
        if words & set(level_cues):
            return level
    return 1


def is_task(sentence: str) -> bool:
    """True for a question or an instruction (it starts with a verb), false for a statement."""
    text = sentence.strip().lower()
    if text.endswith("?"):
        return True
    for frame in POLITE_FRAMES:
        if text.startswith(frame + " "):
            text = text[len(frame) + 1:]
    first = re.findall(r"[a-z]+", text)[:1]
    return bool(first) and first[0] in IMPERATIVE_STARTS


def estimate_level_v2(sentence: str) -> int:
    """Highest cue level in a learner task; statements are Remember."""
    if not is_task(sentence):
        return 1
    text = sentence.lower().replace("trade-offs", "tradeoffs").replace("trade-off", "tradeoff")
    level = estimate_level(text, CUES_V2)
    for phrase_level, phrase in PHRASE_CUES:
        if phrase in text:
            level = max(level, phrase_level)
    return level


def score_estimator(
    items: Sequence[dict[str, Any]], estimator: Callable[[str], int], levels: Sequence[int] = (1, 2, 3, 4, 5, 6)
) -> dict[str, Any]:
    """Accuracy, within-one accuracy, mean absolute error, per-level P/R/F1, macro-F1, confusion."""
    pairs = [(int(item["level"]), int(estimator(item["text"]))) for item in items]
    total = len(pairs)
    confusion = {truth: {pred: 0 for pred in levels} for truth in levels}
    for truth, pred in pairs:
        confusion[truth][pred] += 1
    per_level: dict[int, dict[str, float | None]] = {}
    for level in levels:
        tp = confusion[level][level]
        predicted = sum(confusion[truth][level] for truth in levels)
        actual = sum(confusion[level].values())
        precision = tp / predicted if predicted else None
        recall = tp / actual if actual else None
        f1 = (2 * precision * recall / (precision + recall)
              if precision is not None and recall is not None and precision + recall else 0.0 if actual else None)
        per_level[level] = {
            "support": actual,
            "precision": None if precision is None else round(precision, 3),
            "recall": None if recall is None else round(recall, 3),
            "f1": None if f1 is None else round(f1, 3),
        }
    f1s = [row["f1"] for row in per_level.values() if row["f1"] is not None]
    return {
        "items": total,
        "accuracy": round(100 * sum(t == p for t, p in pairs) / total, 1) if total else None,
        "within_one": round(100 * sum(abs(t - p) <= 1 for t, p in pairs) / total, 1) if total else None,
        "mean_abs_error": round(sum(abs(t - p) for t, p in pairs) / total, 3) if total else None,
        "macro_f1": round(sum(f1s) / len(f1s), 3) if f1s else None,
        "per_level": per_level,
        "confusion": {str(t): {str(p): n for p, n in row.items()} for t, row in confusion.items()},
    }
