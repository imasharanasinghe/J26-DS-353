"""Sentences C4 writes itself from C1/C2/C3 data instead of taking them from a model.

A grounded sentence asserts only what the inputs already say: the learner's mastery
(C2), the verified path (C3), or a graph misconception (C1). The generator, the
repair step, and the verifier all build these sentences with the functions below, so
the verifier can recognise one by regenerating it from the same data. A model
sentence that merely resembles one is verified like any other claim.
"""

from __future__ import annotations

from typing import Any

BLOOM_NAMES = {1: "Remember", 2: "Understand", 3: "Apply", 4: "Analyze", 5: "Evaluate", 6: "Create"}

SOURCE_PATH = "C3 verified path"
SOURCE_LEARNER = "C2 learner state"
SOURCE_GRAPH = "C1 knowledge graph"
SOURCE_TASK = "C4 check question at the learner's target Bloom level"
SOURCE_HINT = "C4 scaffold written from the verified path"


def concept_name(kg: dict[str, Any], concept_id: str) -> str:
    concept = kg.get("concepts", {}).get(concept_id, {})
    return concept.get("name", concept_id.replace("_", " ").title())


def path_line(c3_path: dict[str, Any], kg: dict[str, Any]) -> str:
    """One-line diagram of the verified path; the interface renders it as a flow."""
    parts: list[str] = []
    for step in c3_path.get("path", []):
        kind = step.get("kind")
        if kind == "remediate":
            parts.append(f"Fix: {concept_name(kg, step.get('affects', step.get('id', '')))} misconception")
        else:
            name = step.get("name") or concept_name(kg, step.get("id", ""))
            parts.append(name + (" (check)" if kind == "probe" else ""))
    if not parts:
        parts.append(concept_name(kg, c3_path["target"]))
    return "Path: " + " → ".join(parts)


def known_sentence(name: str, mastery: float) -> str:
    return f"You already know {name} well (mastery {mastery:.2f})."


def review_sentence(name: str, mastery: float, threshold: float, target_name: str, relation: str | None) -> str:
    base = f"Review {name} first: your mastery is {mastery:.2f}, below the {threshold:.2f} this path needs"
    if relation == "prerequisite":
        return f"{base}, and it is a prerequisite of {target_name}."
    if relation == "earlier":
        return f"{base}, and it comes earlier on your verified path."
    return f"{base}."


def check_sentence(
    name: str, reason: str, mastery: float | None, uncertainty: float | None, threshold: float
) -> str:
    head = f"Take a quick check on {name} first:"
    if reason == "no_history" or mastery is None:
        return f"{head} there is no learner history for it yet."
    if reason == "uncertain":
        return f"{head} the model is unsure how well you know it (mastery {mastery:.2f}, uncertainty {uncertainty:.2f})."
    return f"{head} your mastery ({mastery:.2f}) is too close to the {threshold:.2f} threshold to call it secure."


def bloom_sentence(level: int, ceiling: int) -> str:
    return (f"This asks for {BLOOM_NAMES.get(level, level)}-level thinking, but your current ceiling is "
            f"{BLOOM_NAMES.get(ceiling, ceiling)}-level, so it is saved for later.")


def misconception_sentence(statement: str) -> str:
    return f'Common mistake: "{statement.rstrip(".")}" is false.'


def prerequisite_sentence(target_name: str, prerequisite_name: str) -> str:
    """Graph-derived statement; verified against C1 like any other claim, not grounded."""
    return f"Before {target_name}, you need {prerequisite_name}."


def next_sentence(name: str) -> str:
    return f"Your next step: {name}."


# One check question per Bloom level. Each assumes nothing about the domain, so it is a task
# for the learner and not a claim. The cue verb in each template must make the pilot Bloom
# estimator (pipeline.BLOOM_CUES) return the same level; tests/test_progressive.py checks it.
TASK_TEMPLATES = {
    1: "Recall: what is {name}, and what is it used for?",
    2: "Can you explain, in your own words, why {name} works the way it does?",
    3: "Can you apply {name} to a small example and trace each step?",
    4: "How would you compare {name} with {other} and analyze where each one fits best?",
    5: "Can you justify when {name} is the better choice and evaluate its trade-offs?",
    6: "Design a new small problem that {name} helps to solve, and write its solution?",
}


def task_sentence(level: int, name: str, other: str = "a simpler structure") -> str:
    return TASK_TEMPLATES[max(1, min(level, 6))].format(name=name, other=other)


def hint_from_known_sentence(name: str, known_name: str) -> str:
    return f"Hint: start from what you already know about {known_name} and connect it to {name}."


def hint_steps_sentence(name: str) -> str:
    return f"Hint: break {name} into its smallest steps and take them one at a time."
