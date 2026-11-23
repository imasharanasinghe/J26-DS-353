"""The "Do you need help with any concept?" box.

Flow: attempt first, then tiered hints, then the verified explanation. The box keeps no state:
the client sends what has happened so far (``attempted``, ``hints_used``) and gets the next step.

Rules fixed by the proposal:

* **Asking for help is never mastery evidence.** A help request produces no evidence message.
  Only an *attempt* does, and its weight is lowered when hints were used.
* Help requests are logged as a confusion signal for the lecturer (``confusion_map``).
* The explanation shown is verified: the graph facts for the concept go through the C4 pipeline for
  this learner, so a prerequisite the learner has not mastered is repaired into "review X first".
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from . import grounding
from .paths import build_verified_path
from .pipeline import C4Config, C4Pipeline

STAGES = ("start", "attempt", "hint", "explain")
MAX_HINTS = 3


def hints_for(kg: dict[str, Any], concept_id: str) -> list[str]:
    """Up to three hints of growing strength: a prerequisite nudge, a prerequisite fact, a fact."""
    concepts = kg["concepts"]
    concept = concepts[concept_id]
    name = concept.get("name", concept_id)
    prerequisites = [p for p in concept.get("prerequisites", []) if p in concepts]
    out = []
    if prerequisites:
        out.append(grounding.hint_from_known_sentence(name, concepts[prerequisites[0]].get("name", prerequisites[0])))
        facts = concepts[prerequisites[0]].get("facts", [])
        if facts:
            out.append(f"Remember: {facts[0]}")
    else:
        out.append(grounding.hint_steps_sentence(name))
    facts = concept.get("facts", [])
    if facts:
        out.append(f"Think about this: {facts[0]}")
    return out[:MAX_HINTS]


def attempt_correct(pipeline: C4Pipeline, text: str) -> bool:
    """An attempt counts as correct when it states a graph fact and contradicts none."""
    rows = pipeline.factual_check(text)
    return (any(r["factual_status"] == "ENTAILED" for r in rows)
            and not any(r["factual_status"] == "CONTRADICTED" for r in rows))


def step(kg: dict[str, Any], learner: dict[str, Any], concept_id: str, stage: str = "start",
         attempt: str | None = None, hints_used: int = 0, attempted: bool = False) -> dict[str, Any]:
    if concept_id not in kg["concepts"]:
        raise ValueError(f"Unknown concept: {concept_id}")
    if stage not in STAGES:
        raise ValueError(f"stage must be one of {list(STAGES)}")
    pipeline = C4Pipeline(kg)
    path = build_verified_path(concept_id, kg, learner.get("learner_id", "learner"))
    name = pipeline.concept_name(concept_id)
    base = {"concept": concept_id, "stage": stage, "mastery_evidence": None,
            "note": "asking for help is not mastery evidence; only attempts are"}

    if stage == "start":
        return {**base, "next": "attempt", "prompt": f"Before the explanation, try it yourself: {pipeline.task_for(1, path)}"}

    if stage == "attempt":
        if not attempt or not attempt.strip():
            raise ValueError("an attempt needs some text")
        correct = attempt_correct(pipeline, attempt)
        evidence = {"schema": "c4-evidence/1.0", "concept": concept_id, "bloom": 1,
                    "score": 1.0 if correct else 0.0, "items": 1, "source": "help_attempt",
                    "weight": "low" if hints_used else "medium"}
        return {**base, "next": "done" if correct else "hint", "correct": correct, "mastery_evidence": evidence,
                "feedback": "That matches the graph." if correct else "Not quite yet. Here is a hint."}

    if stage == "hint":
        available = hints_for(kg, concept_id)
        if hints_used >= len(available):
            return {**base, "next": "explain", "hint": None, "hints_left": 0}
        return {**base, "next": "attempt" if hints_used + 1 < len(available) else "explain",
                "hint": available[hints_used], "hints_left": len(available) - hints_used - 1}

    # explain: reachable only after an attempt, so the box does not become an answer lookup
    if not attempted:
        return {**base, "next": "attempt", "refused": True,
                "prompt": "Please make an attempt first, then you can see the explanation."}
    facts = " ".join(kg["concepts"][concept_id].get("facts", []))
    report = pipeline.run(path, learner, facts)
    return {**base, "next": "done", "explanation": report.final_explanation,
            "review_first": report.review_first, "verified_claims": len(report.claims),
            "unresolved": report.unresolved_claims, "heading": f"About {name}"}


class HelpLog:
    """Lecturer's confusion map: how many students asked about each concept, and how far they got."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def record(self, student: str, concept: str, stage: str) -> None:
        self.events.append({"student": student, "concept": concept, "stage": stage})

    def confusion_map(self) -> dict[str, dict[str, Any]]:
        table: dict[str, dict[str, Any]] = defaultdict(lambda: {"requests": 0, "students": set(), "reached_explanation": set()})
        for event in self.events:
            row = table[event["concept"]]
            row["requests"] += 1
            row["students"].add(event["student"])
            if event["stage"] == "explain":
                row["reached_explanation"].add(event["student"])
        return {c: {"requests": r["requests"], "students": len(r["students"]),
                    "reached_explanation": len(r["reached_explanation"])}
                for c, r in sorted(table.items(), key=lambda kv: -len(kv[1]["students"]))}
