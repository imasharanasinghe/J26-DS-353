"""L6: rank the paths that already PASSED the critic and pick one.

HeuristicReranker is a stand-in score. Replace with the IQL value of each path
(sum of Q along the path) in PP2. Never call this on unverified paths.
"""
from __future__ import annotations

from ..kg import KnowledgeGraph
from ..learner import LearnerState
from ..schemas import Step


class Reranker:
    def score(self, path: list[Step], learner: LearnerState, kg: KnowledgeGraph) -> float:
        raise NotImplementedError

    def best(self, paths, learner, kg):
        return max(paths, key=lambda p: self.score(p, learner, kg)) if paths else None


class HeuristicReranker(Reranker):
    """Higher is better: shorter paths, smoother difficulty climb, weakest topics early."""

    def score(self, path, learner, kg):
        learns = [s.ref for s in path if s.kind == "learn"]
        if not learns:
            return 0.0
        length_pen = 0.2 * len(path)
        diffs = [kg.difficulty(c) for c in learns]
        bumps = sum(max(0, b - a) ** 2 for a, b in zip(diffs, diffs[1:]))
        drops = sum(max(0, a - b) for a, b in zip(diffs, diffs[1:]))  # going back to easy stuff
        n = len(learns)
        early_weak = sum((1 - learner.m(c)) * (n - i) / n for i, c in enumerate(learns)) / n
        return round(-length_pen - 0.5 * bumps - 0.3 * drops + early_weak, 4)
