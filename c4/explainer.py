"""Replaceable explanation-generation boundary for C4."""

from __future__ import annotations

from typing import Any


class TemplateExplanationGenerator:
    """Offline, deterministic generator used until the team selects an LLM."""

    def generate(
        self,
        c3_path: dict[str, Any],
        learner_state: dict[str, Any],
        knowledge_graph: dict[str, Any],
    ) -> str:
        target = c3_path["target"]
        concept = knowledge_graph.get("concepts", {}).get(target, {})
        name = concept.get("name", target.replace("_", " ").title())
        prerequisites = concept.get("prerequisites", [])
        prerequisite_names = [
            knowledge_graph.get("concepts", {}).get(item, {}).get(
                "name", item.replace("_", " ").title()
            )
            for item in prerequisites
        ]
        path_context = " -> ".join(
            step.get("name", step.get("id", "")) for step in c3_path.get("path", [])
        )
        learner_id = learner_state.get("learner_id", c3_path["learner_id"])
        text = f"For learner {learner_id}, {name} is introduced through the verified path"
        if path_context:
            text += f" ({path_context})"
        if prerequisite_names:
            text += f" after considering {', '.join(prerequisite_names)}"
        return text + "."
