"""L1: work out what this learner still needs before the target, and what they
could start right now (the admissible set, same idea as MC-CPO's masking)."""
from __future__ import annotations

from dataclasses import dataclass

from .config import C3Config
from .kg import KnowledgeGraph
from .learner import LearnerState


@dataclass
class Frontier:
    target: str
    required: list            # unknown concepts the path must teach (target included)
    admissible_now: list      # required concepts whose prerequisites are all known already
    probe_candidates: list    # known-but-unsure prerequisites -> should be checked
    misconceptions: list      # active misconceptions that touch this path
    target_already_known: bool = False


def compute_frontier(kg: KnowledgeGraph, learner: LearnerState, target: str,
                     cfg: C3Config) -> Frontier:
    if not kg.has(target):
        raise KeyError(f"Unknown target concept '{target}'")
    th = cfg.mastery_threshold
    known = learner.known_set(th)

    if target in known and learner.u(target) < cfg.uncertainty_threshold:
        return Frontier(target, [], [], [], [], target_already_known=True)

    needed = [c for c in sorted(kg.ancestors(target) | {target}) if c not in known or c == target]
    admissible = [c for c in needed if all(p in known for p in kg.prereqs(c))]

    # Prerequisites the learner "knows" but the model is unsure about.
    probes = set()
    for c in needed:
        for p in kg.prereqs(c):
            if p in known and learner.u(p) >= cfg.uncertainty_threshold:
                probes.add(p)

    touched = set(needed) | {p for c in needed for p in kg.prereqs(c)}
    mis = [m for m in learner.misconceptions
           if m in kg.misconceptions and kg.misconception_target(m) in touched]

    return Frontier(target, needed, admissible, sorted(probes), mis)
