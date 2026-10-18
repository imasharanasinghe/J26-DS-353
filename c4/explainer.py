"""Replaceable explanation-generation boundary for C4."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
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


class OllamaExplanationGenerator:
    """Generate explanations with a locally running Ollama model."""

    def __init__(
        self,
        model: str = "qwen3:4b",
        endpoint: str = "http://localhost:11434/api/generate",
        timeout: float = 300.0,
    ) -> None:
        self.model = model
        self.endpoint = endpoint
        self.timeout = timeout

    def build_prompt(
        self,
        c3_path: dict[str, Any],
        learner_state: dict[str, Any],
        knowledge_graph: dict[str, Any],
    ) -> str:
        target = c3_path["target"]
        concept = knowledge_graph.get("concepts", {}).get(target, {})
        prerequisites = concept.get("prerequisites", [])
        facts = concept.get("facts", [])
        path = [step.get("id") for step in c3_path.get("path", [])]
        mastery = learner_state.get("mastery", {})
        return (
            "Write exactly 2 or 3 concise sentences for one learner. "
            "Use only the supplied facts; do not invent facts or repeat sentences. "
            "Return plain text with no preamble.\n\n"
            f"Target concept: {target}\n"
            f"Verified learning path: {path}\n"
            f"Prerequisites: {prerequisites}\n"
            f"Known graph facts: {facts}\n"
            f"Learner mastery: {mastery}\n"
        )

    def generate(
        self,
        c3_path: dict[str, Any],
        learner_state: dict[str, Any],
        knowledge_graph: dict[str, Any],
    ) -> str:
        payload = json.dumps({
            "model": self.model,
            "prompt": self.build_prompt(c3_path, learner_state, knowledge_graph),
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 120,
                "repeat_penalty": 1.15,
            },
        }).encode("utf-8")
        request = Request(
            self.endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                result = json.load(response)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(
                "Ollama is unavailable. Start it with `ollama serve` and "
                f"confirm that model `{self.model}` is installed."
            ) from exc
        text = result.get("response", "").strip()
        if not text:
            raise RuntimeError("Ollama returned an empty explanation")
        return text
