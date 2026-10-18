"""C3 pipeline, L0 -> L8.

  L0 inputs (KG from C1, learner state from C2)
  L1 frontier / admissible set
  L2 ordering bias (learned layer)
  L3 proposer writes K drafts
  L4 critic checks each draft          <- decides validity, alone
  L5 repair loop, max N rounds
  L6 rerank ONLY verified drafts
  L7 fallback (topological sort) if none verified
  L8 verified path JSON -> C4
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from .config import C3Config
from .critic import Critic
from .fallback import build_fallback_path
from .frontier import compute_frontier
from .kg import KnowledgeGraph
from .learner import LearnerState
from .proposer import ProposalContext, Proposer
from .rl import HeuristicPolicy, HeuristicReranker, OrderingPolicy, Reranker
from .schemas import Step, Violation, path_str


@dataclass
class DraftTrace:
    draft_id: int
    initial_path: list
    initial_violations: list
    final_path: list
    final_violations: list
    rounds: int
    history: list = field(default_factory=list)  # [(round, violations)]

    @property
    def verified(self) -> bool:
        return not self.final_violations


@dataclass
class PlanResult:
    learner_id: str
    target: str
    path: list
    verified: bool
    source: str            # "draft" | "repaired" | "fallback" | "unverified" | "already_known"
    drafts: list
    score: float | None
    elapsed_s: float
    remaining_violations: list = field(default_factory=list)

    def to_json(self, kg: KnowledgeGraph) -> dict:
        """L8 output contract for C4 (see docs/interfaces.md)."""
        steps = []
        for i, s in enumerate(self.path, 1):
            item = {"step": i, "kind": s.kind, "id": s.ref}
            if s.kind in ("learn", "probe"):
                item.update(name=kg.name(s.ref), difficulty=kg.difficulty(s.ref),
                            prerequisites=kg.prereqs(s.ref))
            else:
                m = kg.misconceptions[s.ref]
                item.update(affects=m["affects"], description=m["description"])
            steps.append(item)
        fixed = []
        for d in self.drafts:
            fixed += [v.to_dict() for v in d.initial_violations]
        return {
            "learner_id": self.learner_id,
            "target": self.target,
            "verified": self.verified,
            "source": self.source,
            "path": steps,
            "summary": path_str(self.path),
            "score": self.score,
            "drafts_considered": len(self.drafts),
            "repair_rounds": [d.rounds for d in self.drafts],
            "violations_found": fixed,
            "remaining_violations": [v.to_dict() for v in self.remaining_violations],
            "elapsed_s": round(self.elapsed_s, 3),
        }


class C3Pipeline:
    def __init__(self, kg: KnowledgeGraph, proposer: Proposer, cfg: C3Config | None = None,
                 policy: OrderingPolicy | None = None, reranker: Reranker | None = None):
        self.kg, self.proposer = kg, proposer
        self.cfg = cfg or C3Config()
        self.critic = Critic(kg, self.cfg)
        self.policy = policy or HeuristicPolicy()
        self.reranker = reranker or HeuristicReranker()

    def plan(self, learner: LearnerState, target: str, *, use_critic=True, use_repair=True,
             use_fallback=True) -> PlanResult:
        t0 = time.perf_counter()
        fr = compute_frontier(self.kg, learner, target, self.cfg)                       # L1
        if fr.target_already_known:
            return PlanResult(learner.learner_id, target, [], True, "already_known", [], None,
                              time.perf_counter() - t0)
        ctx = ProposalContext(self.kg, learner, fr, self.cfg, self.policy.bias(learner, fr))  # L2
        drafts = self.proposer.propose(ctx, self.cfg.k_drafts)                          # L3

        traces = []
        for i, d in enumerate(drafts):
            v0 = self.critic.check(d, learner, target)                                  # L4
            path, v, rounds, hist = d, v0, 0, [(0, v0)]
            if use_critic and use_repair:
                while v and rounds < self.cfg.max_repair_rounds:                        # L5
                    rounds += 1
                    path = self.proposer.repair(ctx, path, v)
                    v = self.critic.check(path, learner, target)
                    hist.append((rounds, v))
            traces.append(DraftTrace(i, d, v0, path, v, rounds, hist))

        if not use_critic:
            # Ablation: trust the first draft blindly (what most LLM tutors do).
            t = traces[0]
            return PlanResult(learner.learner_id, target, t.initial_path, not t.initial_violations,
                              "unverified", traces, None, time.perf_counter() - t0,
                              t.initial_violations)

        verified = [t for t in traces if t.verified]
        if verified:                                                                    # L6
            best = max(verified, key=lambda t: self.reranker.score(t.final_path, learner, self.kg))
            src = "draft" if best.rounds == 0 else "repaired"
            return PlanResult(learner.learner_id, target, best.final_path, True, src, traces,
                              self.reranker.score(best.final_path, learner, self.kg),
                              time.perf_counter() - t0)

        if use_fallback:                                                                # L7
            path = build_fallback_path(self.kg, learner, fr, self.cfg)
            left = self.critic.check(path, learner, target)
            return PlanResult(learner.learner_id, target, path, not left, "fallback", traces,
                              self.reranker.score(path, learner, self.kg),
                              time.perf_counter() - t0, left)

        best = min(traces, key=lambda t: len(t.final_violations))
        return PlanResult(learner.learner_id, target, best.final_path, False, "unverified", traces,
                          None, time.perf_counter() - t0, best.final_violations)
