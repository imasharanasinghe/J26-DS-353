from __future__ import annotations

import json
from pathlib import Path

from c4 import C4Config, C4Pipeline, audit_loop
from c4.paths import build_verified_path

DATA = Path(__file__).resolve().parents[1] / "c4" / "data"
KG = json.loads((DATA / "knowledge_graph.json").read_text())
KG30 = json.loads((DATA / "c3_import" / "graph_30_concepts.json").read_text())


def learner() -> dict:
    state = json.loads((DATA / "learner_state.json").read_text())
    state["mastery"].update({"tree": 0.9, "binary_tree": 0.1, "arrays": 0.9})
    state["uncertainty"].update({"tree": 0.1, "binary_tree": 0.1, "arrays": 0.1})
    return state


TEXT = "A heap is a complete binary tree. A heap can be stored in an array."


def run(edge_confidence):
    pipeline = C4Pipeline(KG, C4Config(rewrite=False), edge_confidence=edge_confidence)
    return pipeline.run(build_verified_path("heap", KG), learner(), TEXT)


def test_no_audit_behaves_as_before() -> None:
    result = run(None)
    assert result.to_dict()["schema_version"] == "c4-report/1.2" and "edge_confidence" not in result.to_dict()
    assert "binary_tree" in result.review_first


def test_unsupported_edge_no_longer_sends_student_to_review() -> None:
    result = run({"binary_tree->heap": {"status": "Unsupported", "n": 300}})
    assert "binary_tree" not in result.review_first
    assert not any("UNMASTERED_PREREQUISITE" in c.violations for c in result.initial_claims)
    report = result.to_dict()
    assert report["schema_version"] == "c4-report/1.3"
    assert report["edge_confidence"]["binary_tree->heap"]["status"] == "Unsupported"


def test_contested_edge_is_inconclusive_not_a_hard_violation() -> None:
    result = run({"binary_tree->heap": {"status": "Contested", "n": 30}})
    violations = [v for c in result.initial_claims for v in c.violations]
    assert "UNMASTERED_PREREQUISITE" not in violations and "INCONCLUSIVE_COGNITIVE" in violations


def test_supported_edge_keeps_the_hard_violation() -> None:
    result = run({"binary_tree->heap": {"status": "Supported", "n": 300}})
    assert any("UNMASTERED_PREREQUISITE" in c.violations for c in result.initial_claims)


def test_audit_reduces_wrong_detours_and_approved_proposals_cut_misses() -> None:
    row = audit_loop.study_once(KG30, 300, 0)
    assert row["audit"]["wrong_detours_per_pair"] < row["no_audit"]["wrong_detours_per_pair"]
    assert row["audit_approved"]["missed_prereqs_per_pair"] < row["no_audit"]["missed_prereqs_per_pair"]
