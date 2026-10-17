"""L0 input from C2: what one learner knows, and how sure the model is."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

UNKNOWN_UNCERTAINTY = 0.5  # concept never seen: the model has no idea


@dataclass
class LearnerState:
    learner_id: str
    mastery: dict = field(default_factory=dict)      # concept -> 0..1
    uncertainty: dict = field(default_factory=dict)  # concept -> 0..0.5
    misconceptions: list = field(default_factory=list)

    def m(self, c: str) -> float:
        return float(self.mastery.get(c, 0.0))

    def u(self, c: str) -> float:
        return float(self.uncertainty.get(c, UNKNOWN_UNCERTAINTY))

    def knows(self, c: str, threshold: float) -> bool:
        return self.m(c) >= threshold

    def known_set(self, threshold: float) -> set:
        return {c for c, v in self.mastery.items() if v >= threshold}

    @classmethod
    def from_dict(cls, d: dict) -> "LearnerState":
        return cls(d["learner_id"], dict(d.get("mastery", {})), dict(d.get("uncertainty", {})),
                   list(d.get("misconceptions", [])))


def load_learners(path: str) -> dict[str, LearnerState]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {d["learner_id"]: LearnerState.from_dict(d) for d in data["learners"]}
