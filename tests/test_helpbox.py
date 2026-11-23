from __future__ import annotations

import json
from pathlib import Path

import pytest

from c4 import helpbox

DATA = Path(__file__).resolve().parents[1] / "c4" / "data"
KG = json.loads((DATA / "knowledge_graph.json").read_text())
LEARNER = json.loads((DATA / "learner_state.json").read_text())


def test_attempt_comes_first_and_explanation_is_refused_without_one() -> None:
    assert helpbox.step(KG, LEARNER, "heap", "start")["next"] == "attempt"
    refused = helpbox.step(KG, LEARNER, "heap", "explain", attempted=False)
    assert refused["refused"] and "explanation" not in refused


def test_help_requests_are_never_mastery_evidence() -> None:
    for stage in ("start", "hint"):
        assert helpbox.step(KG, LEARNER, "heap", stage)["mastery_evidence"] is None


def test_attempt_is_evidence_and_hints_lower_its_weight() -> None:
    good = helpbox.step(KG, LEARNER, "heap", "attempt", attempt="A heap is a complete binary tree.")
    assert good["correct"] and good["mastery_evidence"]["weight"] == "medium"
    hinted = helpbox.step(KG, LEARNER, "heap", "attempt", attempt="A heap is a complete binary tree.", hints_used=2)
    assert hinted["mastery_evidence"]["weight"] == "low"
    bad = helpbox.step(KG, LEARNER, "heap", "attempt", attempt="A heap is always fully sorted.")
    assert not bad["correct"] and bad["next"] == "hint" and bad["mastery_evidence"]["score"] == 0.0


def test_hints_grow_then_hand_over_to_explanation() -> None:
    first = helpbox.step(KG, LEARNER, "heap", "hint", hints_used=0)
    assert first["hint"] and first["hints_left"] >= 1
    last = helpbox.step(KG, LEARNER, "heap", "hint", hints_used=len(helpbox.hints_for(KG, "heap")))
    assert last["next"] == "explain" and last["hint"] is None


def test_explanation_after_attempt_is_verified_for_this_learner() -> None:
    result = helpbox.step(KG, LEARNER, "heap", "explain", attempted=True)
    assert "explanation" in result and result["unresolved"] == []
    assert "binary_tree" in result["review_first"] or result["verified_claims"] > 0


def test_confusion_map_and_bad_input() -> None:
    log = helpbox.HelpLog()
    for student, stage in (("a", "start"), ("b", "start"), ("b", "explain")):
        log.record(student, "heap", stage)
    log.record("a", "stack", "start")
    cm = log.confusion_map()
    assert list(cm)[0] == "heap" and cm["heap"]["students"] == 2 and cm["heap"]["reached_explanation"] == 1
    with pytest.raises(ValueError):
        helpbox.step(KG, LEARNER, "nope", "start")
    with pytest.raises(ValueError):
        helpbox.step(KG, LEARNER, "heap", "attempt", attempt=" ")
