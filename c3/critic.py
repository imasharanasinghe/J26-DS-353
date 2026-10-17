"""L4: the symbolic critic. Checks a path against five teaching rules and returns
exact, typed faults. It never guesses and gives the same answer every time.

  R1 Prerequisites first     MissingPrerequisite(c, needs=p) / LateStep(p, after=c)
  R2 ZPD difficulty          CognitiveLoadJump(c, from, load, level) / BloomJump(c, from, bloom, level)
                             / AlreadyKnown(c)
  R3 Structure               UnknownStep / DuplicateStep / OffPath / TargetMissing / TargetNotLast
  R4 Uncertainty probing     MissingProbe(p, before=c)
  R5 Misconception repair    UnremediatedMisconception(m, before=c)
"""
from __future__ import annotations

from .config import C3Config
from .kg import KnowledgeGraph
from .learner import LearnerState
from .schemas import Step, Violation


class Critic:
    def __init__(self, kg: KnowledgeGraph, cfg: C3Config | None = None):
        self.kg = kg
        self.cfg = cfg or C3Config()

    def check(self, path: list[Step], learner: LearnerState, target: str) -> list[Violation]:
        on = set(self.cfg.rules)
        out: list[Violation] = []
        if "R3" in on:
            out += self._r3_structure(path, learner, target)
        # The other rules only look at steps that are valid concepts / misconceptions.
        clean = [s for s in path if self._valid_ref(s)]
        if "R1" in on:
            out += self._r1_prerequisites(clean, learner)
        if "R2" in on:
            out += self._r2_zpd(clean, learner)
        if "R4" in on:
            out += self._r4_probes(clean, learner)
        if "R5" in on:
            out += self._r5_misconceptions(clean, learner)
        return out

    def is_valid(self, path, learner, target) -> bool:
        return not self.check(path, learner, target)

    # ------------------------------------------------------------------ helpers
    def _valid_ref(self, s: Step) -> bool:
        if s.kind in ("learn", "probe"):
            return self.kg.has(s.ref)
        if s.kind == "remediate":
            return s.ref in self.kg.misconceptions
        return False

    def _known(self, learner: LearnerState) -> set:
        return learner.known_set(self.cfg.mastery_threshold)

    # ------------------------------------------------------------------ R3
    def _r3_structure(self, path, learner, target):
        out = []
        relevant = set(self.kg.ancestors(target)) | {target}
        seen = set()
        for s in path:
            if not self._valid_ref(s):
                out.append(Violation("R3", "UnknownStep", str(s)))
                continue
            if s in seen:
                out.append(Violation("R3", "DuplicateStep", str(s)))
            seen.add(s)
            if s.kind == "learn" and s.ref not in relevant:
                out.append(Violation("R3", "OffPath", s.ref, {"target": target}))
        learns = [s.ref for s in path if s.kind == "learn"]
        if target not in learns:
            out.append(Violation("R3", "TargetMissing", target))
        elif learns[-1] != target or path[-1] != Step("learn", target):
            out.append(Violation("R3", "TargetNotLast", target))
        return out

    # ------------------------------------------------------------------ R1
    def _r1_prerequisites(self, path, learner):
        out = []
        known_before = self._known(learner)
        known = set(known_before)
        learned_so_far = []
        for s in path:
            if s.kind != "learn":
                continue
            for p in self.kg.prereqs(s.ref):
                if p not in known:
                    out.append(Violation("R1", "MissingPrerequisite", s.ref, {"needs": p}))
            # LateStep: this topic is taught AFTER something that depends on it.
            # (Only for topics the learner already partly knows; otherwise
            #  MissingPrerequisite above already reports the problem.)
            if s.ref in known_before:
                for earlier in learned_so_far:
                    if s.ref in self.kg.prereqs(earlier):
                        out.append(Violation("R1", "LateStep", s.ref, {"after": earlier}))
                        break
            known.add(s.ref)
            learned_so_far.append(s.ref)
        return out

    # ------------------------------------------------------------------ R2
    def _r2_zpd(self, path, learner):
        out = []
        th, tu, w = self.cfg.mastery_threshold, self.cfg.uncertainty_threshold, self.cfg.zpd_width
        known = [c for c in self._known(learner) if self.kg.has(c)]
        # Cognitive load level = heaviest topic known so far
        level = max((self.kg.difficulty(c) for c in known), default=0)
        # Bloom level = highest thinking level reached so far (only if C1 gave Bloom levels)
        use_bloom = self.cfg.check_bloom and self.kg.has_bloom()
        bloom_level = max((self.kg.bloom_rank(c) for c in known), default=0) if use_bloom else 0
        prev = "known topics"
        for s in path:
            if s.kind != "learn":
                continue
            d = self.kg.difficulty(s.ref)
            if learner.knows(s.ref, th) and learner.u(s.ref) < tu:
                out.append(Violation("R2", "AlreadyKnown", s.ref, {"mastery": round(learner.m(s.ref), 2)}))
                continue
            if d > level + w:
                out.append(Violation("R2", "CognitiveLoadJump", s.ref,
                                     {"from": prev, "load": d, "level": level}))
            if use_bloom:
                b = self.kg.bloom_rank(s.ref)
                if b > bloom_level + self.cfg.bloom_width:
                    out.append(Violation("R2", "BloomJump", s.ref,
                                         {"from": prev, "bloom": self.kg.bloom_name(s.ref),
                                          "level": bloom_level}))
                bloom_level = max(bloom_level, b)
            level = max(level, d)
            prev = s.ref
        return out

    # ------------------------------------------------------------------ R4
    def _r4_probes(self, path, learner):
        out, reported = [], set()
        th, tu = self.cfg.mastery_threshold, self.cfg.uncertainty_threshold
        probed, learned = set(), set()
        for s in path:
            if s.kind == "probe":
                probed.add(s.ref)
                continue
            if s.kind != "learn":
                continue
            for p in self.kg.prereqs(s.ref):
                unsure_known = learner.knows(p, th) and learner.u(p) >= tu
                if unsure_known and p not in probed and p not in learned and p not in reported:
                    out.append(Violation("R4", "MissingProbe", p, {"before": s.ref}))
                    reported.add(p)
            learned.add(s.ref)
        return out

    # ------------------------------------------------------------------ R5
    def _r5_misconceptions(self, path, learner):
        out, reported = [], set()
        active = [m for m in learner.misconceptions if m in self.kg.misconceptions]
        fixed = set()
        for s in path:
            if s.kind == "remediate":
                fixed.add(s.ref)
                continue
            if s.kind != "learn":
                continue
            touched = {s.ref, *self.kg.prereqs(s.ref)}
            for m in active:
                if self.kg.misconception_target(m) in touched and m not in fixed and m not in reported:
                    out.append(Violation("R5", "UnremediatedMisconception", m, {"before": s.ref}))
                    reported.add(m)
        return out
