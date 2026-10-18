from __future__ import annotations

import json
from pathlib import Path

import pytest

from c4 import C4Pipeline


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "c4" / "data"


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


@pytest.fixture
def pipeline() -> C4Pipeline:
    return C4Pipeline.from_files(DATA / "knowledge_graph.json")


def test_rejects_unverified_c3_path(pipeline: C4Pipeline) -> None:
    path = load("verified_path.json")
    path["verified"] = False
    with pytest.raises(ValueError, match="verified paths"):
        pipeline.run(path, load("learner_state.json"), "A heap is a complete binary tree.")


def test_detects_factual_and_prerequisite_violations(pipeline: C4Pipeline) -> None:
    result = pipeline.run(
        load("verified_path.json"),
        load("learner_state.json"),
        "A heap is a complete binary tree. A heap is a fully sorted array.",
    )
    assert result.initial_claims[0].factual_status == "ENTAILED"
    assert "UNSUPPORTED_CLAIM" in result.initial_claims[1].violations
    assert "UNMASTERED_PREREQUISITE" in result.initial_claims[0].violations
    assert result.rewrite_attempts == 3
    assert result.unresolved_claims == ["claim-1", "claim-2"]


def test_valid_claim_is_preserved(pipeline: C4Pipeline) -> None:
    learner = load("learner_state.json")
    learner["mastery"].update({"tree": 0.9, "binary_tree": 0.9})
    learner["uncertainty"].update({"tree": 0.1, "binary_tree": 0.1})
    result = pipeline.run(
        load("verified_path.json"),
        learner,
        "A heap is a complete binary tree.",
    )
    assert result.final_explanation == result.original_explanation
    assert result.claims[0].accepted is True


def test_factual_violation_can_be_rewritten_when_prerequisites_are_ready(
    pipeline: C4Pipeline,
) -> None:
    learner = load("learner_state.json")
    learner["mastery"].update({"tree": 0.9, "binary_tree": 0.9})
    learner["uncertainty"].update({"tree": 0.1, "binary_tree": 0.1})
    result = pipeline.run(
        load("verified_path.json"),
        learner,
        "A heap is a fully sorted array.",
    )
    assert result.final_explanation == "A heap is a complete binary tree."
    assert result.unresolved_claims == []
    assert result.claims[0].accepted is True


def test_complete_fixture_has_c3_contract() -> None:
    path = load("verified_path.json")
    assert path["verified"] is True
    assert {"learner_id", "target", "path"} <= path.keys()
