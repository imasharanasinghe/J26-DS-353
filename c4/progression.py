"""Bloom-level progression policy: how C4 moves a learner up over repeated sessions.

A snapshot check asks whether an explanation matches the learner's level *now*. This
module adds the time dimension: it keeps the Bloom level a learner has demonstrated on
each concept, decides the level the next explanation should target, and updates the
record from the learner's answers to the check question at the end of each explanation.

Design (pilot decisions, not validated educational truths; see docs/GUIDELINES.md):

- Demonstrated level: the highest Bloom level (1 Remember .. 6 Create) on which the
  learner passed a check question; 0 means nothing demonstrated yet.
- Target level (zone of proximal development): demonstrated level + 1, but only when the
  learner is *ready* (the concept's prerequisites are mastered). Otherwise the learner
  consolidates at the demonstrated level.
- Contingent scaffolding: the amount of support follows demonstrated success. It starts
  full, fades after consecutive passes, and returns after a failure.
- Demotion: failing the same level twice in a row on a level already demonstrated lowers
  the demonstrated level (forgetting or an over-generous earlier pass). Failing a
  stretch task above the demonstrated level never lowers it.

Everything here is a pure function over plain data so it can be tested without a pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

LEVELS = {1: "Remember", 2: "Understand", 3: "Apply", 4: "Analyze", 5: "Evaluate", 6: "Create"}
MAX_LEVEL = 6
SCAFFOLDS = ("full", "partial", "minimal")
ACTIONS = ("start", "advance", "retry", "consolidate", "maintain")


@dataclass(frozen=True)
class ProgressionConfig:
    """Pilot thresholds for the progression policy."""

    pass_score: float = 0.7        # a check answer at or above this passes
    fail_score: float = 0.4        # a check answer below this fails
    step_back_after: int = 2       # consecutive fails on a demonstrated level before demotion
    partial_after: int = 1         # consecutive passes before support drops to "partial"
    minimal_after: int = 2         # consecutive passes before support drops to "minimal"
    max_level: int = MAX_LEVEL


@dataclass(frozen=True)
class Attempt:
    """One answered check question."""

    session: int
    level: int
    score: float
    scaffold: str = "full"

    def to_dict(self) -> dict[str, Any]:
        return {"session": self.session, "level": self.level,
                "score": round(self.score, 4), "scaffold": self.scaffold}

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Attempt":
        return cls(int(raw["session"]), int(raw["level"]), float(raw["score"]),
                   str(raw.get("scaffold", "full")))


@dataclass
class ConceptProgress:
    """What the learner has demonstrated on one concept, with the evidence."""

    level: int = 0
    attempts: list[Attempt] = field(default_factory=list)

    def passes_streak(self, config: ProgressionConfig) -> int:
        """Consecutive passing attempts at the end of the history."""
        streak = 0
        for attempt in reversed(self.attempts):
            if attempt.score < config.pass_score:
                break
            streak += 1
        return streak

    def fails_streak_at(self, level: int, config: ProgressionConfig) -> int:
        """Consecutive failed attempts at ``level`` at the end of the history."""
        streak = 0
        for attempt in reversed(self.attempts):
            if attempt.level != level or attempt.score >= config.fail_score:
                break
            streak += 1
        return streak

    def to_dict(self) -> dict[str, Any]:
        return {"level": self.level, "attempts": [item.to_dict() for item in self.attempts]}

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ConceptProgress":
        level = int(raw.get("level", 0))
        if not 0 <= level <= MAX_LEVEL:
            raise ValueError(f"Bloom level must be between 0 and {MAX_LEVEL}")
        return cls(level, [Attempt.from_dict(item) for item in raw.get("attempts", [])])


@dataclass(frozen=True)
class Decision:
    """What the next explanation for this concept should do."""

    target_level: int
    action: str
    scaffold: str
    reason: str
    current_level: int

    @property
    def target_name(self) -> str:
        return LEVELS.get(self.target_level, str(self.target_level))

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_level": self.current_level,
            "current_name": LEVELS.get(self.current_level, "None yet"),
            "target_level": self.target_level,
            "target_name": self.target_name,
            "action": self.action,
            "scaffold": self.scaffold,
            "reason": self.reason,
        }


def scaffold_for(progress: ConceptProgress, config: ProgressionConfig) -> str:
    """Contingent support: fades with consecutive passes, returns after a failure."""
    streak = progress.passes_streak(config)
    if streak >= config.minimal_after:
        return "minimal"
    if streak >= config.partial_after:
        return "partial"
    return "full"


def decide(progress: ConceptProgress, ready: bool, config: ProgressionConfig | None = None) -> Decision:
    """Target Bloom level, action, and scaffold for the learner's next explanation.

    ``ready`` is True when the concept's prerequisites are mastered (computed by the
    caller from C2 mastery and uncertainty).
    """
    config = config or ProgressionConfig()
    level = progress.level
    scaffold = scaffold_for(progress, config)
    if level == 0 and not progress.attempts:
        return Decision(1, "start", "full", "nothing demonstrated on this concept yet", 0)
    if not ready:
        return Decision(max(level, 1), "consolidate", scaffold,
                        "prerequisites are not secure, so stay at the demonstrated level", level)
    if level >= config.max_level:
        return Decision(config.max_level, "maintain", "minimal",
                        "the highest Bloom level is already demonstrated", level)
    target = level + 1
    last = progress.attempts[-1] if progress.attempts else None
    if last is not None and last.level == target and last.score < config.pass_score:
        return Decision(target, "retry", "full",
                        "the last attempt at this level did not pass, so retry with full support", level)
    return Decision(target, "advance", scaffold,
                    "ready: aim one Bloom level above the demonstrated level", level)


def update(
    progress: ConceptProgress,
    session: int,
    level: int,
    score: float,
    scaffold: str = "full",
    config: ProgressionConfig | None = None,
) -> ConceptProgress:
    """Record one answered check question and return the updated progress (input unchanged)."""
    config = config or ProgressionConfig()
    if not 1 <= level <= config.max_level:
        raise ValueError(f"level must be between 1 and {config.max_level}")
    if not 0.0 <= score <= 1.0:
        raise ValueError("score must be between 0 and 1")
    updated = ConceptProgress(progress.level, list(progress.attempts))
    updated.attempts.append(Attempt(session, level, score, scaffold))
    if score >= config.pass_score and level > updated.level:
        updated.level = level
    elif (score < config.fail_score and level <= updated.level
          and updated.fails_streak_at(level, config) >= config.step_back_after):
        updated.level = level - 1
    return updated


@dataclass
class LearnerProgress:
    """Per-concept progress for one learner, stored under ``learner_state["bloom"]``."""

    concepts: dict[str, ConceptProgress] = field(default_factory=dict)

    def get(self, concept_id: str) -> ConceptProgress:
        return self.concepts.get(concept_id, ConceptProgress())

    def with_attempt(
        self, concept_id: str, session: int, level: int, score: float,
        scaffold: str = "full", config: ProgressionConfig | None = None,
    ) -> "LearnerProgress":
        concepts = dict(self.concepts)
        concepts[concept_id] = update(self.get(concept_id), session, level, score, scaffold, config)
        return LearnerProgress(concepts)

    def to_state(self) -> dict[str, Any]:
        return {key: value.to_dict() for key, value in self.concepts.items()}

    @classmethod
    def from_state(cls, learner_state: dict[str, Any]) -> "LearnerProgress":
        raw = learner_state.get("bloom")
        raw = {} if raw is None else raw
        if not isinstance(raw, dict):
            raise ValueError("learner.bloom must be an object")
        return cls({key: ConceptProgress.from_dict(value) for key, value in raw.items()})
