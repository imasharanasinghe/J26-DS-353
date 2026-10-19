"""Replaceable explanation-generation boundary for C4."""

from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Any

from . import grounding
from .pipeline import C4Config, C4Pipeline


# Sections of the draft kept at each scaffold level (first word of the section title).
FADING_SECTIONS = {
    "full": {"About", "Before", "Where", "Refresher", "Common"},
    "partial": {"About", "Before", "Where"},
    "minimal": {"About", "Where"},
}

GENERATION_OPTIONS = {"temperature": 0.2, "num_predict": 200, "repeat_penalty": 1.1}


def compose_explanation(
    c3_path: dict[str, Any],
    learner_state: dict[str, Any],
    knowledge_graph: dict[str, Any],
    body: list[str] | None = None,
    config: C4Config | None = None,
) -> str:
    """Structured draft: path diagram, the concept, prerequisites, learner status, mistakes.

    ``body`` holds the sentences that explain the target concept (from a language model);
    without it the graph facts are used. The draft is unverified: it deliberately lists
    everything relevant to the path, and C4 then removes or rewrites whatever this learner
    should not be given yet.
    """
    pipeline = C4Pipeline(knowledge_graph, config)
    concepts = knowledge_graph.get("concepts", {})
    target = c3_path["target"]
    name = pipeline.concept_name(target)
    earlier = pipeline.path_concepts(c3_path)
    prerequisites = [item for item in concepts.get(target, {}).get("prerequisites", []) if item in concepts]
    status_ids = earlier + [item for item in prerequisites if item not in earlier]

    sections: list[tuple[str, list[str]]] = [
        (f"About {name}", body or list(concepts.get(target, {}).get("facts", []))),
        ("Before you start", pipeline.prerequisite_sentences(target)),
        ("Where you stand", [pipeline.status_sentence(item, c3_path, learner_state) for item in status_ids]
         + [pipeline.next_sentence(c3_path, learner_state)]),
        ("Refresher on earlier concepts",
         [fact for item in status_ids for fact in concepts.get(item, {}).get("facts", [])]),
        ("Common mistakes",
         pipeline.misconception_sentences(target) + [
             sentence for item in earlier if pipeline._mastery_state(item, learner_state) == "MASTERED"
             for sentence in pipeline.misconception_sentences(item)]),
    ]
    check: list[str] = []
    if pipeline.config.progressive:
        # Contingent scaffolding: detail fades with demonstrated success and returns after a
        # failure, and the draft ends with a check question at the learner's target level.
        decision = pipeline.progression_decision(c3_path, learner_state)
        keep = FADING_SECTIONS[decision.scaffold]
        sections = [(title, bullets) for title, bullets in sections if title.split(" ")[0] in keep]
        if decision.scaffold == "minimal":
            sections = [(title, bullets[:1] if title.startswith("About") else bullets)
                        for title, bullets in sections]
        check = pipeline.check_section(c3_path, learner_state, decision)
    lines = [f"## {name}: your next step", "", grounding.path_line(c3_path, knowledge_graph)]
    for title, bullets in sections + ([("Check yourself", check)] if check else []):
        bullets = list(dict.fromkeys(bullets))
        if bullets:
            lines += ["", f"### {title}"] + [f"- {item}" for item in bullets]
    return "\n".join(lines)


class TemplateExplanationGenerator:
    """Offline, deterministic generator used until the team selects an LLM."""

    def generate_body(
        self,
        c3_path: dict[str, Any],
        learner_state: dict[str, Any],
        knowledge_graph: dict[str, Any],
    ) -> str:
        facts = knowledge_graph.get("concepts", {}).get(c3_path["target"], {}).get("facts", [])
        return " ".join(facts)

    def generate(
        self,
        c3_path: dict[str, Any],
        learner_state: dict[str, Any],
        knowledge_graph: dict[str, Any],
        config: C4Config | None = None,
    ) -> str:
        return compose_explanation(c3_path, learner_state, knowledge_graph, config=config)

    def build_prompt(self, *_: Any) -> None:
        return None


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
        lines = [f"Explain {name} to a student in 3 or 4 short sentences."]
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
        config: C4Config | None = None,
    ) -> str:
        """Structured draft whose concept explanation is written by the local model."""
        body = self.generate_body(c3_path, learner_state, knowledge_graph)
        sentences = [item for item in re.split(r"(?<=[.!?])\s+", body) if item.strip()]
        return compose_explanation(c3_path, learner_state, knowledge_graph, sentences, config)

    def generate_body(
        self,
        c3_path: dict[str, Any],
        learner_state: dict[str, Any],
        knowledge_graph: dict[str, Any],
    ) -> str:
        """Raw model explanation of the concept (what the natural-generation cache stores)."""
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
