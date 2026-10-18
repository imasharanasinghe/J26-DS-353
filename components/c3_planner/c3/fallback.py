"""L7: the safety net. If no draft passes the critic after repair, build a correct
path directly: topological sort (every prerequisite before the concept that needs it),
then add the probes and misconception fixes in the right places.

Always passes the critic for any knowledge graph that has no ZPD warnings.
"""
from __future__ import annotations

import heapq

from .config import C3Config
from .frontier import Frontier
from .kg import KnowledgeGraph
from .learner import LearnerState
from .schemas import Step


def topo_order(kg: KnowledgeGraph, concepts: list, known: set) -> list:
    """Kahn's algorithm. Ties broken by easier first, then by name, so it's repeatable."""
    todo = set(concepts)
    waiting = {c: {p for p in kg.prereqs(c) if p in todo and p not in known} for c in todo}
    ready = [(kg.difficulty(c), c) for c, ps in waiting.items() if not ps]
    heapq.heapify(ready)
    order = []
    while ready:
        _, c = heapq.heappop(ready)
        order.append(c)
        for other, ps in waiting.items():
            if c in ps:
                ps.discard(c)
                if not ps:
                    heapq.heappush(ready, (kg.difficulty(other), other))
    if len(order) != len(todo):
        raise ValueError("Could not order concepts: prerequisite cycle")
    return order


def build_fallback_path(kg: KnowledgeGraph, learner: LearnerState, fr: Frontier,
                        cfg: C3Config) -> list[Step]:
    if fr.target_already_known:
        return []
    th, tu = cfg.mastery_threshold, cfg.uncertainty_threshold
    known = learner.known_set(th)
    path, probed, fixed, learned = [], set(), set(), set()
    active = [m for m in learner.misconceptions if m in kg.misconceptions]
    for c in topo_order(kg, fr.required, known):
        for p in kg.prereqs(c):
            if learner.knows(p, th) and learner.u(p) >= tu and p not in probed and p not in learned:
                path.append(Step("probe", p))
                probed.add(p)
        touched = {c, *kg.prereqs(c)}
        for m in active:
            if kg.misconception_target(m) in touched and m not in fixed:
                path.append(Step("remediate", m))
                fixed.add(m)
        path.append(Step("learn", c))
        learned.add(c)
    return path
