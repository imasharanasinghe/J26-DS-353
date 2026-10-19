"""Transport-independent service layer used by the C4 web workbench.

Everything the frontend needs is a plain function over JSON-compatible dicts so it
can be tested without a server. Invalid input raises ``ValueError`` (client error);
an unavailable generator raises ``RuntimeError``.
"""

from __future__ import annotations

import json
from dataclasses import fields, replace
from pathlib import Path
from typing import Any

from .adapters import load_c2_learner, load_json, validate_c3_path
from .evaluation import PROFILES, make_learner
from .explainer import OllamaExplanationGenerator, TemplateExplanationGenerator
from .paths import build_verified_path
from .pipeline import C4Config, C4Pipeline
from .progression import LearnerProgress

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "c4" / "data"
RESULTS = ROOT / "c4" / "results"

MAX_EXPLANATION_CHARS = 20000
SCENARIOS = ("mixed", "valid", "factual", "cognitive")

# Config keys a client may override, with their expected type and allowed range.
CONFIG_LIMITS: dict[str, tuple[type, float, float]] = {
    "mastery_threshold": (float, 0.0, 1.0),
    "uncertainty_threshold": (float, 0.0, 1.0),
    "threshold_margin": (float, 0.0, 0.5),
    "max_rewrite_attempts": (int, 0, 5),
    "entail_similarity": (float, 0.0, 1.0),
    "default_bloom_ceiling": (int, 1, 6),
    "mastered_bloom_ceiling": (int, 1, 6),
}
CONFIG_FLAGS = ("check_factual", "check_cognitive", "rewrite", "progressive", "check_stagnation")


def scenario_text(pipeline: C4Pipeline, target: str, scenario: str, default_text: str = "") -> str:
    """Target-aware demo sentences; the learner state is never edited to fake a result."""
    concept = pipeline.kg["concepts"][target]
    name = concept.get("name", target)
    facts = concept.get("facts", [])
    known_false = concept.get("known_false", [f"{name} is always fully sorted."])
    if scenario == "valid":
        return facts[-1] if facts else f"{name} is introduced."
    if scenario == "factual":
        return known_false[0]
    if scenario == "cognitive":
        # A true graph fact that depends on a concept the learner has not mastered.
        for fact in facts:
            if pipeline._mentioned_concepts(fact) not in ((), (target,)):
                return fact
        return facts[0] if facts else f"{name} is introduced."
    if default_text:
        return default_text
    parts = [facts[-1] if facts else "", known_false[0], facts[0] if facts else ""]
    return " ".join(dict.fromkeys(part for part in parts if part))


class Workbench:
    """Loads the pilot fixtures once and answers frontend requests."""

    def __init__(self, data_dir: Path = DATA, results_dir: Path = RESULTS) -> None:
        self.data_dir = Path(data_dir)
        self.results_dir = Path(results_dir)
        self.kg = load_json(self.data_dir / "knowledge_graph.json")
        self.fixture_learner = load_c2_learner(load_json(self.data_dir / "learner_state.json"))
        self.default_text = (self.data_dir / "explanation.txt").read_text(encoding="utf-8").strip()

    # ------------------------------------------------------------------ meta

    def meta(self) -> dict[str, Any]:
        """Static description of targets, learner presets, scenarios, and defaults."""
        pipeline = C4Pipeline(self.kg)
        concepts = self.kg["concepts"]
        targets = []
        for target_id, concept in concepts.items():
            presets = {"demo_learner": self._learner_payload(self.fixture_learner, target_id)}
            for profile in PROFILES:
                learner, _ = make_learner(self.kg, target_id, profile)
                presets[profile] = self._learner_payload(learner, target_id)
            path = build_verified_path(target_id, self.kg, self.fixture_learner["learner_id"])
            targets.append({
                "id": target_id,
                "path": path,
                "graph_context": [
                    {
                        "id": step["id"],
                        "name": step["name"],
                        "difficulty": step["difficulty"],
                        "prerequisites": step["prerequisites"],
                        "facts": concepts[step["id"]].get("facts", []),
                        "known_false": concepts[step["id"]].get("known_false", []),
                    }
                    for step in path["path"]
                ],
                "name": concept.get("name", target_id),
                "prerequisites": concept.get("prerequisites", []),
                "facts": concept.get("facts", []),
                "scenarios": {
                    name: scenario_text(pipeline, target_id, name, self.default_text if target_id == "heap" else "")
                    for name in SCENARIOS
                },
                "learner_presets": presets,
            })
        defaults = {
            field.name: getattr(C4Config(), field.name)
            for field in fields(C4Config)
        }
        return {
            "concepts": {key: value.get("name", key) for key, value in concepts.items()},
            "targets": targets,
            "config_defaults": defaults,
            "config_limits": {key: list(value[1:]) for key, value in CONFIG_LIMITS.items()},
            "generators": ["template", "ollama"],
            "schema_version": "c4-report/1.2",
        }

    def _learner_payload(self, learner: dict[str, Any], seed_target: str | None = None) -> dict[str, Any]:
        """Learner state restricted to concepts present in the graph (C2 may know more).

        ``bloom`` is the C4-maintained demonstrated-level record. When a preset has none and
        ``seed_target`` is given, the target starts at Remember with one passing attempt so
        the progression view has a history to show (a demo seed, not learner data).
        """
        known = self.kg["concepts"]
        payload = {
            "learner_id": learner.get("learner_id", "custom"),
            "mastery": {k: v for k, v in learner.get("mastery", {}).items() if k in known},
            "uncertainty": {k: v for k, v in learner.get("uncertainty", {}).items() if k in known},
        }
        bloom = {k: v for k, v in (learner.get("bloom") or {}).items() if k in known}
        if not bloom and seed_target:
            bloom = LearnerProgress().with_attempt(seed_target, 1, 1, 0.85).to_state()
        if bloom:
            payload["bloom"] = bloom
        return payload

    # ---------------------------------------------------------------- verify

    def verify(self, payload: dict[str, Any]) -> dict[str, Any]:
        target = self._target(payload)
        explanation = self._explanation(payload)
        learner = self._learner(payload.get("learner"))
        pipeline = C4Pipeline(self.kg, self._config(payload.get("config")))
        path = build_verified_path(target, self.kg, learner["learner_id"])
        validate_c3_path(path)
        report = pipeline.run(path, learner, explanation).to_dict()
        report["bloom_ceiling"] = pipeline._bloom_ceiling(path, learner)
        report["visual"] = pipeline.visual(path, learner)
        return report

    def generate(self, payload: dict[str, Any], ollama: OllamaExplanationGenerator | None = None) -> dict[str, Any]:
        target = self._target(payload)
        learner = self._learner(payload.get("learner"))
        source = payload.get("source", "template")
        if source not in ("template", "ollama"):
            raise ValueError("source must be 'template' or 'ollama'")
        path = build_verified_path(target, self.kg, learner["learner_id"])
        generator = TemplateExplanationGenerator() if source == "template" else (
            ollama or OllamaExplanationGenerator(timeout=60.0)
        )
        text = generator.generate(path, learner, self.kg, self._config(payload.get("config")))
        return {"source": source, "explanation": text, "prompt": (
            generator.build_prompt(path, learner, self.kg) if source == "ollama" else None
        )}

    def explain(self, payload: dict[str, Any], ollama: OllamaExplanationGenerator | None = None) -> dict[str, Any]:
        """Fully automatic run: draft an explanation, then verify, repair, and report.

        The draft is never delivered on its own; the report carries it as
        ``original_explanation`` next to the verified ``final_explanation``.
        """
        draft = self.generate(payload, ollama)
        report = self.verify({**payload, "explanation": draft["explanation"]})
        report["generator"] = draft["source"]
        report["prompt"] = draft["prompt"]
        return report

    def results(self) -> dict[str, Any]:
        """Committed evaluation artefacts, if present."""
        output: dict[str, Any] = {}
        for key, name in (("stress", "stress_test.json"), ("natural", "natural.json"),
                          ("sensitivity", "sensitivity.json")):
            path = self.results_dir / name
            output[key] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        report = self.results_dir / "RESULTS.md"
        output["markdown"] = report.read_text(encoding="utf-8") if report.exists() else None
        return output

    # ------------------------------------------------------------ validation

    def _target(self, payload: dict[str, Any]) -> str:
        target = payload.get("target")
        if target not in self.kg["concepts"]:
            raise ValueError(f"Unknown target concept: {target!r}")
        return target

    @staticmethod
    def _explanation(payload: dict[str, Any]) -> str:
        text = payload.get("explanation")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("explanation must be a non-empty string")
        if len(text) > MAX_EXPLANATION_CHARS:
            raise ValueError(f"explanation exceeds {MAX_EXPLANATION_CHARS} characters")
        return text.strip()

    def _learner(self, raw: Any) -> dict[str, Any]:
        if raw is None:
            return self._learner_payload(self.fixture_learner)
        if not isinstance(raw, dict):
            raise ValueError("learner must be an object")
        learner = {"learner_id": str(raw.get("learner_id", "custom"))[:60]}
        for key in ("mastery", "uncertainty"):
            values = raw.get(key, {})
            if not isinstance(values, dict):
                raise ValueError(f"learner.{key} must be an object")
            clean = {}
            for concept, value in values.items():
                if concept not in self.kg["concepts"]:
                    raise ValueError(f"Unknown concept in learner.{key}: {concept!r}")
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
                    raise ValueError(f"learner.{key}.{concept} must be a number between 0 and 1")
                clean[concept] = float(value)
            learner[key] = clean
        if raw.get("bloom") is not None:
            try:
                progress = LearnerProgress.from_state(raw)
            except (ValueError, TypeError, KeyError, AttributeError) as exc:
                raise ValueError(f"learner.bloom is invalid: {exc}") from None
            for concept in progress.concepts:
                if concept not in self.kg["concepts"]:
                    raise ValueError(f"Unknown concept in learner.bloom: {concept!r}")
            learner["bloom"] = progress.to_state()
        return learner

    @staticmethod
    def _config(raw: Any) -> C4Config:
        if raw is None:
            return C4Config()
        if not isinstance(raw, dict):
            raise ValueError("config must be an object")
        updates: dict[str, Any] = {}
        for key, value in raw.items():
            if key in CONFIG_FLAGS:
                if not isinstance(value, bool):
                    raise ValueError(f"config.{key} must be true or false")
                updates[key] = value
            elif key in CONFIG_LIMITS:
                kind, low, high = CONFIG_LIMITS[key]
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high:
                    raise ValueError(f"config.{key} must be a number between {low} and {high}")
                updates[key] = kind(value)
            else:
                raise ValueError(f"Unknown config option: {key!r}")
        return replace(C4Config(), **updates)
