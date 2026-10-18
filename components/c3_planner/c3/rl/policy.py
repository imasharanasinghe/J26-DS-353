"""L2: an ordering bias handed to the proposer BEFORE it drafts.

It only nudges ("try these first"); it can never make an invalid path valid.

HeuristicPolicy is a stand-in. Replace it with IQLPolicy once the offline policy
is trained on MOOCCubeX transitions (see rl/dataset.py).
"""
from __future__ import annotations

from ..frontier import Frontier
from ..learner import LearnerState


class OrderingPolicy:
    def bias(self, learner: LearnerState, fr: Frontier) -> list[str]:
        """Return concepts in preferred teaching order (a hint, not a rule)."""
        raise NotImplementedError


class HeuristicPolicy(OrderingPolicy):
    """Prefer what the learner can start now, weakest first."""

    def bias(self, learner, fr):
        now = sorted(fr.admissible_now, key=lambda c: (learner.m(c), c))
        rest = [c for c in fr.required if c not in now]
        return now + rest


class IQLPolicy(OrderingPolicy):
    """Placeholder for the trained offline IQL policy (PP2 work).

    Plan:
      state  = mastery + uncertainty vectors from C2 (fixed concept order)
      action = which admissible concept to teach next
      reward = next-attempt score from MOOCCubeX (0 / 1 / 2)
    bias() would rank fr.admissible_now by the learned Q(state, action).
    """

    def __init__(self, model=None):
        self.model = model

    def bias(self, learner, fr):
        if self.model is None:
            raise NotImplementedError("Train the IQL model first (see rl/dataset.py).")
        raise NotImplementedError
