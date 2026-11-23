"""Block-plan simulation (Phase 4): does evidence-driven practice allocation shrink the number of
students under the mastery floor, compared with a uniform plan?

Goal wording: every student reaches a minimum mastery floor on every concept in the block before
the exam, and the spread between students shrinks. Not "every student equal".

Plans, all with the SAME total practice budget per student per week:

* ``uniform``   equal practice on every concept in the block
* ``tiered``    last semester's marks split students into three tiers; weaker tiers get the extra
                budget the stronger tiers give up, spread evenly over concepts
* ``evidence``  weekly allocation proportional to gap (target minus current estimate) times the
                number of later concepts that depend on the concept, over concepts whose
                prerequisites are close enough to ready; re-planned each week from noisy checks

The student model (learning rate, diminishing returns, prerequisite gating, forgetting, noisy
checkpoint quizzes) is an assumption. Results here reflect that assumption; real claims need the pilot.
"""

from __future__ import annotations

import math
import random
import statistics
from typing import Any, Sequence

from .audit_sim import graph_edges, topological_order
from .metrics import bootstrap_mean_ci


def block_concepts(kg: dict[str, Any], size: int = 10) -> list[str]:
    ids = topological_order(list(kg["concepts"]), graph_edges(kg))
    return ids[:size]


def _dependents(kg: dict[str, Any], block: Sequence[str]) -> dict[str, int]:
    edges = graph_edges(kg)
    children: dict[str, set[str]] = {}
    for a, b in edges:
        children.setdefault(a, set()).add(b)

    def below(node: str, seen: set[str]) -> set[str]:
        for child in children.get(node, ()):
            if child not in seen:
                seen.add(child)
                below(child, seen)
        return seen

    return {c: len(below(c, set()) & set(block)) for c in block}


class Student:
    def __init__(self, rng: random.Random, concepts: Sequence[str], parents: dict[str, list[str]]):
        self.rate = max(0.15, rng.gauss(1.0, 0.45))            # learning speed multiplier
        self.prior_mark = min(100.0, max(20.0, rng.gauss(55, 18) + 10 * (self.rate - 1)))
        self.mastery = {c: min(0.9, max(0.0, rng.gauss(0.12 + 0.004 * (self.prior_mark - 50), 0.07))) for c in concepts}
        self.parents = parents

    def practise(self, concept: str, hours: float, rng: random.Random) -> None:
        if hours <= 0:
            return
        gate = min((self.mastery.get(p, 1.0) for p in self.parents.get(concept, [])), default=1.0)
        # Diminishing returns in hours; weak prerequisites slow learning (not a hard block).
        gain = self.rate * (1 - self.mastery[concept]) * (1 - math.exp(-0.45 * hours)) * (0.35 + 0.65 * gate)
        self.mastery[concept] = min(1.0, self.mastery[concept] + gain * rng.uniform(0.85, 1.15))

    def forget(self, factor: float) -> None:
        for c in self.mastery:
            self.mastery[c] *= factor

    def quiz(self, concept: str, rng: random.Random, items: int = 5) -> float:
        """Raw quiz score: a guess floor of 0.2 and a slip ceiling of 0.9."""
        p = 0.2 + 0.7 * self.mastery[concept]
        return sum(rng.random() < p for _ in range(items)) / items

    def check(self, concept: str, rng: random.Random, items: int = 5) -> float:
        """Guess-corrected mastery estimate from a quiz (what a knowledge-tracing update would use)."""
        return min(1.0, max(0.0, (self.quiz(concept, rng, items) - 0.2) / 0.7))


def plan_uniform(student: Student, concepts: Sequence[str], budget: float, **_: Any) -> dict[str, float]:
    return {c: budget / len(concepts) for c in concepts}


def plan_tiered(student: Student, concepts: Sequence[str], budget: float, tier_cuts: tuple[float, float] = (45, 65),
                **_: Any) -> dict[str, float]:
    weight = 1.35 if student.prior_mark < tier_cuts[0] else 1.0 if student.prior_mark < tier_cuts[1] else 0.7
    total = budget * weight
    return {c: total / len(concepts) for c in concepts}


BASELINE_SHARE = 0.5  # nobody gets less than the baseline: half the budget is spread evenly


def plan_evidence(student: Student, concepts: Sequence[str], budget: float, estimate: dict[str, float],
                  dependents: dict[str, int], floor: float, **_: Any) -> dict[str, float]:
    base = {c: BASELINE_SHARE * budget / len(concepts) for c in concepts}
    extra_budget = (1 - BASELINE_SHARE) * budget
    parents = student.parents
    weights = {}
    for c in concepts:
        gap = max(0.0, floor + 0.1 - estimate[c])
        ready = min((estimate.get(p, 1.0) for p in parents.get(c, [])), default=1.0)
        weights[c] = gap * (1 + dependents.get(c, 0)) * (0.35 + 0.65 * ready)
    total = sum(weights.values())
    if total == 0:  # everyone at floor: stretch, spread evenly
        return {c: budget / len(concepts) for c in concepts}
    return {c: base[c] + extra_budget * w / total for c, w in weights.items()}


PLANS = {"uniform": plan_uniform, "tiered": plan_tiered, "evidence": plan_evidence}


def simulate_cohort(kg: dict[str, Any], plan: str, students: int = 200, weeks: int = 7, seed: int = 0,
                    floor: float = 0.6, budget: float = 4.0, block: int = 10, forgetting: float = 0.985,
                    checkpoint_weeks: Sequence[int] = (3,)) -> dict[str, Any]:
    """Run one plan on a cohort (paired by seed across plans: same students, same noise)."""
    concepts = block_concepts(kg, block)
    edges = graph_edges(kg)
    parents = {c: [a for a, b in edges if b == c and a in concepts] for c in concepts}
    dependents = _dependents(kg, concepts)
    cohort_rng = random.Random(f"planner-cohort:{seed}")
    cohort = [Student(cohort_rng, concepts, parents) for _ in range(students)]
    noise = random.Random(f"planner-noise:{seed}:{plan}")
    below_by_week: list[float] = []
    for student in cohort:
        # Week-0 diagnostic: noisy estimate of every concept (last semester's marks only a prior).
        history = {c: [student.check(c, noise, 8)] for c in concepts}
        estimate = {c: history[c][-1] for c in concepts}
        for week in range(1, weeks + 1):
            allocation = PLANS[plan](student=student, concepts=concepts, budget=budget, estimate=estimate,
                                     dependents=dependents, floor=floor)
            for c in concepts:
                student.practise(c, allocation[c], noise)
            student.forget(forgetting)
            # Re-plan from a fresh noisy weekly check (the evidence plan uses it, others ignore it).
            for c in concepts:
                history[c].append(student.check(c, noise, 8))
                estimate[c] = statistics.fmean(history[c][-3:])
    exam = [[student.quiz(c, noise, 8) for c in concepts] for student in cohort]
    true_mastery = [min(s.mastery.values()) for s in cohort]
    scores = [statistics.fmean(row) for row in exam]
    below_floor = [sum(m < floor for m in s.mastery.values()) / len(concepts) for s in cohort]
    return {
        "plan": plan, "seed": seed,
        "share_students_with_any_concept_below_floor": round(sum(m < floor for m in true_mastery) / students, 4),
        "mean_share_of_concepts_below_floor": round(statistics.fmean(below_floor), 4),
        "exam_mean": round(statistics.fmean(scores), 4),
        "exam_sd": round(statistics.pstdev(scores), 4),
        "per_student_below": below_floor, "per_student_exam": scores,
    }


def compare(kg: dict[str, Any], seeds: int = 8, students: int = 200, seed_offset: int = 0,
            **kwargs: Any) -> dict[str, Any]:
    """The plan was tuned on seeds 0-5 while it was being designed; report on fresh seeds
    (``seed_offset``) so the comparison is not selected on the tuning cohorts."""
    runs = {plan: [simulate_cohort(kg, plan, students=students, seed=seed_offset + s, **kwargs) for s in range(seeds)]
            for plan in PLANS}
    summary = {}
    for plan, rows in runs.items():
        summary[plan] = {key: round(statistics.fmean(r[key] for r in rows), 4) for key in
                         ("share_students_with_any_concept_below_floor", "mean_share_of_concepts_below_floor",
                          "exam_mean", "exam_sd")}
    paired = {}
    for other in ("uniform", "tiered"):
        for metric in ("share_students_with_any_concept_below_floor", "mean_share_of_concepts_below_floor", "exam_sd"):
            diffs = [e[metric] - o[metric] for e, o in zip(runs["evidence"], runs[other])]
            paired[f"evidence_minus_{other}:{metric}"] = {
                "mean": round(statistics.fmean(diffs), 4), "ci95": bootstrap_mean_ci(diffs, seed=3)}
    return {"seeds": seeds, "seed_offset": seed_offset, "students": students, "weeks": kwargs.get("weeks", 7),
            "floor": kwargs.get("floor", 0.6), "budget_per_week": kwargs.get("budget", 4.0),
            "summary": summary, "paired_differences": paired,
            "note": "same budget for every plan; simulated learners, so this reflects the model's assumptions (circular)"}
