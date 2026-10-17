"""Small, local path edits — one per violation type.

Used by the mock proposer's repair, and as the "suggested fix" text the LLM sees.
Each edit touches only the steps named in the violation; everything else keeps its order.
"""
from __future__ import annotations

from .kg import KnowledgeGraph
from .schemas import Step, Violation

FIX_HINTS = {
    "MissingPrerequisite": "insert 'learn:{needs}' immediately before '{concept}' (or move it there if it appears later)",
    "CognitiveLoadJump": "insert the missing easier prerequisite immediately before '{concept}'",
    "BloomJump": "insert a topic at an in-between thinking level immediately before '{concept}'",
    "LateStep": "move '{concept}' to immediately before '{after}' (it is needed by it)",
    "AlreadyKnown": "remove the step '{concept}' (the learner already knows it)",
    "UnknownStep": "remove the step '{concept}' (it does not exist in the knowledge graph)",
    "DuplicateStep": "remove the second '{concept}'",
    "OffPath": "remove '{concept}' (it is not needed for the target)",
    "TargetMissing": "add 'learn:{concept}' as the last step",
    "TargetNotLast": "move 'learn:{concept}' to the very end",
    "MissingProbe": "insert 'probe:{concept}' immediately before '{before}'",
    "UnremediatedMisconception": "insert 'remediate:{concept}' immediately before '{before}'",
}


def hint(v: Violation) -> str:
    return FIX_HINTS.get(v.type, "fix this step").format(concept=v.concept, **v.detail)


def _first_learn(path, c):
    for i, s in enumerate(path):
        if s == Step("learn", c):
            return i
    return None


def _insert_before(path, new: Step, before_concept: str):
    path = [s for s in path if s != new]  # move rather than duplicate
    i = _first_learn(path, before_concept)
    if i is None:
        i = len(path)
    return path[:i] + [new] + path[i:]


def apply_fix(path: list[Step], v: Violation, kg: KnowledgeGraph, known: set) -> list[Step]:
    t, c, d = v.type, v.concept, v.detail
    if t == "MissingPrerequisite":
        return _insert_before(path, Step("learn", d["needs"]), c)
    if t == "LateStep":
        return _insert_before(path, Step("learn", c), d["after"])
    if t in ("CognitiveLoadJump", "BloomJump"):
        learned = known | {s.ref for s in path[: _first_learn(path, c) or 0] if s.kind == "learn"}
        missing = [p for p in kg.ancestors(c) if p not in learned]
        if not missing:
            return path
        key = kg.difficulty if t == "CognitiveLoadJump" else kg.bloom_rank
        bridge = max(missing, key=lambda p: (key(p), kg.difficulty(p)))
        return _insert_before(path, Step("learn", bridge), c)
    if t in ("AlreadyKnown", "OffPath"):
        return [s for s in path if s != Step("learn", c)]
    if t == "UnknownStep":
        return [s for s in path if str(s) != c]
    if t == "DuplicateStep":
        out, seen = [], set()
        for s in path:
            if str(s) == c and s in seen:
                continue
            seen.add(s)
            out.append(s)
        return out
    if t in ("TargetMissing", "TargetNotLast"):
        return [s for s in path if s != Step("learn", c)] + [Step("learn", c)]
    if t == "MissingProbe":
        return _insert_before(path, Step("probe", c), d["before"])
    if t == "UnremediatedMisconception":
        return _insert_before(path, Step("remediate", c), d["before"])
    return path


def apply_all(path, violations, kg, known):
    for v in violations:
        path = apply_fix(path, v, kg, known)
    return path
