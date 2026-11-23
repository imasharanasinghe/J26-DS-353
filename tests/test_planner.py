from __future__ import annotations

import json
from pathlib import Path

from c4 import planner

KG30 = json.loads((Path(__file__).resolve().parents[1] / "c4" / "data" / "c3_import" / "graph_30_concepts.json").read_text())


def test_block_is_prerequisite_ordered() -> None:
    block = planner.block_concepts(KG30, 10)
    assert len(block) == 10 and block.index("variables") < block.index("loops")


def test_all_plans_spend_the_same_budget() -> None:
    import random
    rng = random.Random(0)
    block = planner.block_concepts(KG30, 6)
    student = planner.Student(rng, block, {})
    est = {c: 0.3 for c in block}
    dep = {c: 1 for c in block}
    for name, fn in planner.PLANS.items():
        spent = sum(fn(student=student, concepts=block, budget=5.0, estimate=est, dependents=dep, floor=0.6).values())
        if name != "tiered":
            assert abs(spent - 5.0) < 1e-9
    plan = planner.plan_evidence(student, block, 5.0, est, dep, 0.6)
    assert min(plan.values()) >= 0.5 * 5.0 / len(block) - 1e-9  # nobody below the baseline


def test_evidence_plan_gives_more_to_bigger_gaps() -> None:
    import random
    block = planner.block_concepts(KG30, 4)
    student = planner.Student(random.Random(1), block, {})
    est = {block[0]: 0.9, block[1]: 0.1, block[2]: 0.9, block[3]: 0.9}
    plan = planner.plan_evidence(student, block, 8.0, est, {c: 1 for c in block}, 0.6)
    assert plan[block[1]] == max(plan.values())


def test_simulation_is_seeded_and_paired() -> None:
    a = planner.simulate_cohort(KG30, "uniform", students=40, seed=3)
    b = planner.simulate_cohort(KG30, "uniform", students=40, seed=3)
    assert a["exam_mean"] == b["exam_mean"]
    result = planner.compare(KG30, seeds=2, students=40, budget=8.0)
    assert set(result["summary"]) == {"uniform", "tiered", "evidence"} and result["paired_differences"]
