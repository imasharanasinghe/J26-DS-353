from __future__ import annotations

import json
import random
from pathlib import Path

from c4 import audit_sim, auditor
from c4.auditor import AuditConfig, Observations

ROOT = Path(__file__).resolve().parents[1] / "c4" / "data"
KG30 = json.loads((ROOT / "c3_import" / "graph_30_concepts.json").read_text())


def chain_obs(n: int = 400, seed: int = 0) -> Observations:
    """A needs nothing, B needs A, C is independent; ability drives everything a little."""
    rng = random.Random(seed)
    data = {"A": [], "B": [], "C": [], "D": []}
    for _ in range(n):
        theta = rng.gauss(0, 1)
        p = lambda shift: 1 / (1 + 2.718 ** (-(theta - shift)))
        a = rng.random() < p(0)
        b = a and rng.random() < p(0.2)
        c = rng.random() < p(0)
        d = rng.random() < p(0)
        for key, value in zip("ABCD", (a, b, c, d)):
            data[key].append(int(value))
    return Observations(data)


def status_of(report: dict, edge: list[str]) -> str:
    return next(row["status"] for row in report["edges"] if row["edge"] == edge)


def test_true_edge_supported_reverse_flagged_and_unrelated_not_supported() -> None:
    obs = chain_obs()
    report = auditor.audit_graph([("A", "B"), ("B", "A"), ("C", "D")], obs, AuditConfig(seed=1))
    assert status_of(report, ["A", "B"]) == auditor.SUPPORTED
    assert status_of(report, ["B", "A"]) == auditor.REVERSED
    assert status_of(report, ["C", "D"]) in (auditor.UNSUPPORTED, auditor.CONTESTED)
    assert status_of(report, ["C", "D"]) != auditor.SUPPORTED


def test_small_class_is_contested_not_supported() -> None:
    obs = chain_obs(n=20)
    report = auditor.audit_graph([("A", "B")], obs, AuditConfig(min_students=40))
    assert status_of(report, ["A", "B"]) == auditor.CONTESTED
    assert "insufficient" in report["edges"][0]["reason"]


def test_untestable_base_rate_is_contested() -> None:
    obs = Observations({"A": [1] * 100, "B": [1, 0] * 50})
    assert auditor.audit_edge(obs, ("A", "B"), AuditConfig()).status == auditor.CONTESTED


def test_missing_edge_is_proposed_and_already_implied_pairs_are_not() -> None:
    obs = chain_obs()
    report = auditor.audit_graph([], obs, AuditConfig(seed=1))
    assert [c["edge"] for c in report["missing_candidates"]][:1] == [["A", "B"]]
    implied = auditor.audit_graph([("A", "X"), ("X", "B")], Observations({**obs.mastered, "X": obs.mastered["A"]}))
    assert ["A", "B"] not in [c["edge"] for c in implied["missing_candidates"]]


def test_report_proposes_only_and_needs_a_lecturer() -> None:
    report = auditor.audit_graph([("B", "A"), ("A", "B")], chain_obs(), AuditConfig(seed=1))
    assert report["proposals"] and all(p["needs_lecturer"] for p in report["proposals"])
    assert "a->b" not in report["edge_confidence"] and "A->B" in report["edge_confidence"]


def test_ability_control_removes_a_shared_cause_association() -> None:
    obs = chain_obs()
    raw = auditor.raw_odds_ratio(obs, "C", "D")
    adjusted, _ = auditor.adjusted_odds_ratio(obs, "C", "D", AuditConfig(), bootstrap=False)
    assert raw > 1.5 and adjusted < raw


def test_planted_errors_are_found_with_no_false_alarms_on_clean_edges() -> None:
    run = audit_sim.planted_error_run(KG30, 300, 0)
    assert run["bad_edge_detection_strict"]["precision"] >= 0.8
    assert run["bad_edge_detection_strict"]["recall"] >= 0.5
    assert run["reversed_found"] >= run["planted"]["reversed"] - 2
    assert run["clean_flagged"] <= 3


def test_corruption_keeps_graph_free_of_trivial_cycles() -> None:
    truth = audit_sim.graph_edges(KG30)
    bad = audit_sim.corrupt(truth, list(KG30["concepts"]), 0.15, 3)
    assert all((b, a) not in bad["edges"] for a, b in bad["spurious"])
    assert set(bad["deleted"]).isdisjoint(bad["edges"])


def test_bloom_audit_flags_a_mislabelled_item() -> None:
    rng = random.Random(0)
    items = []
    for level in (1, 2, 3, 4):
        for k in range(3):
            items.append({"id": f"{level}-{k}", "bloom": level,
                          "correct": [int(rng.random() < 0.9 - 0.2 * (level - 1)) for _ in range(300)]})
    items.append({"id": "mislabelled", "bloom": 1, "correct": [int(rng.random() < 0.1) for _ in range(300)]})
    result = auditor.bloom_audit(items)
    assert result["spearman_label_vs_difficulty"] > 0.5 and "mislabelled" in result["flagged_items"]


def test_misconception_and_load_audits() -> None:
    records = [{"misconception": "heap_sorted", "wrong": True, "chose_misconception": i < 40} for i in range(60)]
    assert auditor.misconception_audit(records)["heap_sorted"]["common"]
    assert auditor.load_audit({"a": 1, "b": 2, "c": 3, "d": 4}, {"a": 0.9, "b": 0.7, "c": 0.5, "d": 0.3})[
        "spearman_depth_vs_difficulty"] == 1.0


def test_rows_loader_builds_observations() -> None:
    rows = [{"student": s, "concept": c, "correct": int(s != "s3"), "order": i}
            for i, (s, c) in enumerate((s, c) for s in ("s1", "s2", "s3") for c in ("x", "y") for _ in range(3))]
    obs = audit_sim.observations_from_rows(rows)
    assert obs.mastered["x"] == [1, 1, 0] and obs.students == 3
