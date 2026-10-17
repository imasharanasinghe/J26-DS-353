"""Basic data shapes used everywhere in C3.

A learning path is a list of Steps. There are three kinds of step:
  learn:<concept>         teach this concept
  probe:<concept>         ask a quick check question (the student model is unsure)
  remediate:<misconception>  fix a known wrong belief before moving on
"""
from __future__ import annotations

from dataclasses import dataclass, field

STEP_KINDS = ("learn", "probe", "remediate")


@dataclass(frozen=True)
class Step:
    kind: str  # one of STEP_KINDS
    ref: str   # concept id (learn / probe) or misconception id (remediate)

    def __str__(self) -> str:
        return self.ref if self.kind == "learn" else f"{self.kind}:{self.ref}"

    @staticmethod
    def parse(text: str) -> "Step":
        """'heap' or 'learn:heap' -> learn step; 'probe:tree'; 'remediate:heap_is_sorted'."""
        text = str(text).strip()
        if ":" in text:
            kind, ref = text.split(":", 1)
            kind, ref = kind.strip().lower(), ref.strip()
            if kind in STEP_KINDS:
                return Step(kind, ref)
        return Step("learn", text)


Path = list  # list[Step]


def path_str(path: list[Step]) -> str:
    return " -> ".join(str(s) for s in path) if path else "(empty)"


def learn_steps(path: list[Step]) -> list[str]:
    return [s.ref for s in path if s.kind == "learn"]


@dataclass
class Violation:
    """One typed fault found by the critic.

    rule:    which of the five rules (R1..R5)
    type:    exact fault name, e.g. MissingPrerequisite
    concept: the step the fault is about
    detail:  extra facts, e.g. {"needs": "tree"}
    """
    rule: str
    type: str
    concept: str
    detail: dict = field(default_factory=dict)

    def __str__(self) -> str:
        extra = "".join(f", {k}={v}" for k, v in self.detail.items())
        return f"{self.type}({self.concept}{extra})"

    def to_dict(self) -> dict:
        return {"rule": self.rule, "type": self.type, "concept": self.concept, **self.detail,
                "text": str(self)}
