"""Replaceable explanation-generation boundary for C4."""

from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Any


GENERATION_OPTIONS = {"temperature": 0.2, "num_predict": 200, "repeat_penalty": 1.1}


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
        endpoint: str = "http://localhost:11434/api/chat",
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
        mastery_threshold: float = 0.7,
    ) -> str:
        """Short, direct prompt: small models echo long structured prompts back."""
        concepts = knowledge_graph.get("concepts", {})
        target = c3_path["target"]
        concept = concepts.get(target, {})
        name = concept.get("name", target)
        facts = concept.get("facts", [])
        path = [step["id"] for step in c3_path.get("path", []) if step.get("kind") != "remediate" and step.get("id")]
        mastery = learner_state.get("mastery", {})
        known = [c for c in path if c != target and float(mastery.get(c, 0.0)) >= mastery_threshold]
        unknown = [c for c in path if c != target and c not in known]
        lines = [f"Explain {name} to a student in exactly 2 short sentences."]
        lines.append("Only use these facts:")
        lines += [f"- {fact}" for fact in facts]
        lines.append(f"Learning path (verified): {' -> '.join(path)}")
        lines.append(f"Concepts the student already knows: {', '.join(known) or 'none'}")
        lines.append(f"Concepts the student has not mastered yet: {', '.join(unknown) or 'none'}")
        lines.append("Write the explanation now, with no preamble.")
        return "\n".join(lines)

    def generate(
        self,
        c3_path: dict[str, Any],
        learner_state: dict[str, Any],
        knowledge_graph: dict[str, Any],
    ) -> str:
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a concise educational explanation writer. "
                        "Reply as JSON with a single field `explanation`."
                    ),
                },
                {
                    "role": "user",
                    "content": self.build_prompt(
                        c3_path, learner_state, knowledge_graph
                    ),
                },
            ],
            "stream": False,
            "think": False,
            # Schema-constrained output stops the 4B model echoing its planning text.
            "format": {
                "type": "object",
                "properties": {"explanation": {"type": "string"}},
                "required": ["explanation"],
            },
            "options": GENERATION_OPTIONS,
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
        content = result.get("message", {}).get("content", "")
        try:
            content = json.loads(content).get("explanation", "")
        except (ValueError, AttributeError):
            pass  # fall back to cleaning free text
        text = self._clean_response(content)
        if not text:
            raise RuntimeError("Ollama returned an empty explanation")
        return text

    @staticmethod
    def _clean_response(text: str) -> str:
        ignored_prefixes = (
            "we are given", "we must", "step ", "example:", "the only fact",
            "return only", "write exactly", "use only", "- ", "constraints", "target concept",
            "known graph", "learner mastery", "prerequisites:", "explain ", "only use",
            "learning path", "concepts the student", "write the explanation",
        )
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        cleaned: list[str] = []
        for sentence in sentences:
            normalized = sentence.strip()
            if not normalized:
                continue
            if normalized.lower().startswith(ignored_prefixes):
                continue
            if normalized not in cleaned:
                cleaned.append(normalized)
        return " ".join(cleaned)
