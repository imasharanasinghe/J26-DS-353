"""L3: the proposer writes draft paths; it also does the repairs asked for in L5.

Two versions with the same interface:
  MockProposer - no API key needed. Imitates typical LLM mistakes on purpose
                 (skips prerequisites, swaps order, forgets probes) so the critic
                 has something to catch. Use it to build and test. Its numbers are
                 NOT research results.
  LLMProposer  - the real thing. Calls Anthropic or OpenAI (see prompts.py).
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from .config import C3Config
from .edits import apply_fix
from .fallback import topo_order
from .frontier import Frontier
from .kg import KnowledgeGraph
from .learner import LearnerState
from .schemas import Step, Violation


@dataclass
class ProposalContext:
    kg: KnowledgeGraph
    learner: LearnerState
    frontier: Frontier
    cfg: C3Config
    bias: list  # L2 hint: preferred order


class Proposer:
    name = "base"

    def propose(self, ctx: ProposalContext, k: int) -> list[list[Step]]:
        raise NotImplementedError

    def repair(self, ctx: ProposalContext, path: list[Step], violations: list[Violation]) -> list[Step]:
        raise NotImplementedError


class MockProposer(Proposer):
    name = "mock"

    def __init__(self, seed: int = 0, drop_p=0.2, swap_p=0.25, extra_p=0.15,
                 probe_p=0.5, remediate_p=0.5, repair_miss_p=0.15):
        self.rng = random.Random(seed)
        self.drop_p, self.swap_p, self.extra_p = drop_p, swap_p, extra_p
        self.probe_p, self.remediate_p, self.repair_miss_p = probe_p, remediate_p, repair_miss_p

    def propose(self, ctx, k):
        kg, fr, learner = ctx.kg, ctx.frontier, ctx.learner
        known = learner.known_set(ctx.cfg.mastery_threshold)
        base = topo_order(kg, fr.required, known)
        # follow the L2 bias a little: among equal-difficulty neighbours, prefer biased ones
        rank = {c: i for i, c in enumerate(ctx.bias)}
        drafts = []
        for _ in range(k):
            order = list(base)
            # mistakes an LLM typically makes
            order = [c for c in order if c == fr.target or self.rng.random() > self.drop_p]
            for i in range(len(order) - 1):
                if order[i + 1] != fr.target and self.rng.random() < self.swap_p:
                    order[i], order[i + 1] = order[i + 1], order[i]
            for i in range(len(order) - 1):
                a, b = order[i], order[i + 1]
                if kg.difficulty(a) == kg.difficulty(b) and rank.get(b, 99) < rank.get(a, 99) \
                        and a not in kg.prereqs(b) and b != fr.target:
                    order[i], order[i + 1] = b, a
            if known and self.rng.random() < self.extra_p:
                order.insert(self.rng.randrange(len(order)), self.rng.choice(sorted(known)))
            path = [Step("learn", c) for c in order]
            # sometimes it remembers the probe / misconception instructions
            pre = []
            if self.rng.random() < self.probe_p:
                pre += [Step("probe", p) for p in fr.probe_candidates]
            if self.rng.random() < self.remediate_p:
                pre += [Step("remediate", m) for m in fr.misconceptions]
            drafts.append(pre + path)
        return drafts

    def repair(self, ctx, path, violations):
        known = ctx.learner.known_set(ctx.cfg.mastery_threshold)
        for v in violations:
            if self.rng.random() < self.repair_miss_p:
                continue  # an LLM sometimes ignores one instruction
            path = apply_fix(path, v, ctx.kg, known)
        return path


class LLMProposer(Proposer):
    """Real LLM proposer. See prompts.py for the exact prompts."""
    name = "llm"

    def __init__(self, client=None):
        from .llm_client import LLMClient
        self.client = client or LLMClient.from_env()
        self.format_failures = 0   # replies we could not read as JSON paths (report this!)

    def propose(self, ctx, k):
        from .prompts import parse_paths, proposal_prompt
        system, user = proposal_prompt(ctx, k)
        text = self.client.complete(system, user, temperature=0.8,
                                    tag=f"propose:{ctx.learner.learner_id}:{ctx.frontier.target}")
        paths = parse_paths(text)
        if not paths:
            self.format_failures += 1
            return [[]]  # an empty draft; the critic will flag TargetMissing and repair/fallback handle it
        return paths[:k]

    def repair(self, ctx, path, violations):
        from .prompts import parse_paths, repair_prompt
        system, user = repair_prompt(ctx, path, violations)
        text = self.client.complete(system, user, temperature=0.0,
                                    tag=f"repair:{ctx.learner.learner_id}:{ctx.frontier.target}")
        paths = parse_paths(text)
        if not paths:
            self.format_failures += 1
            return path
        return paths[0]
