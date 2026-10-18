"""Mock verified-path builder used until C3's real output is integrated."""

from __future__ import annotations


def build_verified_path(target: str, graph: dict, learner_id: str = "L02_intermediate") -> dict:
    """Prerequisite-ordered learn steps in the C3 ``PlanResult.to_json`` shape."""
    concepts = graph.get("concepts", {})
    if target not in concepts:
        raise ValueError(f"Unknown target concept: {target}")
    ordered: list[str] = []
    visiting: set[str] = set()

    def visit(concept_id: str) -> None:
        if concept_id in ordered:
            return
        if concept_id in visiting:
            raise ValueError(f"Prerequisite cycle includes {concept_id}")
        visiting.add(concept_id)
        for prerequisite in concepts[concept_id].get("prerequisites", []):
            if prerequisite in concepts:
                visit(prerequisite)
        visiting.remove(concept_id)
        ordered.append(concept_id)

    visit(target)
    return {
        "learner_id": learner_id,
        "target": target,
        "verified": True,
        "source": "pilot",
        "path": [
            {
                "step": index,
                "kind": "learn",
                "id": concept_id,
                "name": concepts[concept_id].get("name", concept_id),
                "difficulty": concepts[concept_id].get("difficulty", 1),
                "prerequisites": concepts[concept_id].get("prerequisites", []),
            }
            for index, concept_id in enumerate(ordered, 1)
        ],
    }
