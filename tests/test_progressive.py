from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from c4 import C4Config, C4Pipeline
from c4 import grounding
from c4.metrics import claim_rates
from c4.paths import build_verified_path

DATA = Path(__file__).resolve().parents[1] / "c4" / "data"
PROGRESSIVE = C4Config(progressive=True)


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


@pytest.fixture
def pipeline() -> C4Pipeline:
    return C4Pipeline.from_files(DATA / "knowledge_graph.json", PROGRESSIVE)


@pytest.fixture
def path() -> dict:
    return load("verified_path.json")


def ready_learner(level: int = 2) -> dict:
    learner = load("learner_state.json")
    learner["mastery"].update({"tree": 0.9, "binary_tree": 0.9})
    learner["uncertainty"].update({"tree": 0.1, "binary_tree": 0.1})
    learner["bloom"]["heap"] = {"level": level, "attempts": []}
    return learner


@pytest.mark.parametrize("level", range(1, 7))
def test_each_check_question_is_estimated_at_its_own_bloom_level(pipeline: C4Pipeline, level: int) -> None:
    for name, other in (("Heaps", "Binary Trees"), ("Stacks", "a simpler structure")):
        sentence = grounding.task_sentence(level, name, other)
        assert pipeline._estimate_bloom(sentence) == level, sentence


def test_scaffold_hints_assert_nothing_and_sit_at_the_lowest_level(pipeline: C4Pipeline, path: dict) -> None:
    for hint in pipeline.hint_candidates(path, ready_learner()):
        assert not hint.endswith("?") and pipeline._estimate_bloom(hint) == 1


def test_static_mode_is_unchanged_by_the_new_code() -> None:
    static = C4Pipeline.from_files(DATA / "knowledge_graph.json")
    result = static.run(load("verified_path.json"), load("learner_state.json"),
                        "A heap can be stored in an array.")
    assert result.progression is None and static._bloom_ceiling(load("verified_path.json"), ready_learner()) == 3


def test_target_level_is_demonstrated_level_plus_one_when_prerequisites_are_mastered(
        pipeline: C4Pipeline, path: dict) -> None:
    decision = pipeline.progression_decision(path, ready_learner(level=2))
    assert (decision.target_level, decision.action) == (3, "advance")
    assert pipeline._bloom_ceiling(path, ready_learner(level=2)) == 3


def test_learner_with_an_unmastered_prerequisite_consolidates(pipeline: C4Pipeline, path: dict) -> None:
    decision = pipeline.progression_decision(path, load("learner_state.json"))  # binary_tree unmastered
    assert (decision.target_level, decision.action) == (1, "consolidate")


def test_learner_with_no_bloom_record_starts_at_remember(pipeline: C4Pipeline, path: dict) -> None:
    learner = ready_learner()
    del learner["bloom"]
    assert pipeline.progression_decision(path, learner).action == "start"


def test_explanation_without_a_target_level_question_is_stagnation_and_is_repaired(
        pipeline: C4Pipeline, path: dict) -> None:
    result = pipeline.run(path, ready_learner(level=2), "A heap can be stored in an array.")
    assert result.progression["stagnation_before"] is True
    assert result.progression["stagnation_after"] is False
    step = result.trace[-1]
    assert step.claim_id == "explanation" and step.violations == ("BLOOM_STAGNATION",)
    assert "### Check yourself" in result.final_explanation
    assert pipeline.task_for(3, path) in result.final_explanation
    assert result.unresolved_claims == []
    assert result.metrics["stagnation_before"] is True and result.metrics["stagnation_after"] is False


def test_question_at_the_target_level_is_not_stagnation(pipeline: C4Pipeline, path: dict) -> None:
    question = "Can you apply Heaps to a small example and trace each step?"
    result = pipeline.run(path, ready_learner(level=2), f"A heap can be stored in an array. {question}")
    assert result.progression["stagnation_before"] is False
    assert result.trace == []
    assert result.claims[-1].claim.source in ("task", "grounded")


def test_question_above_the_target_level_is_a_bloom_mismatch_and_is_relevelled(
        pipeline: C4Pipeline, path: dict) -> None:
    too_high = "Can you justify when a heap is the better choice and evaluate its trade-offs?"
    result = pipeline.run(path, ready_learner(level=2), too_high)
    first = result.initial_claims[0]
    assert first.claim.source == "task" and first.factual_status == "ENTAILED"
    assert first.cognitive_status == "BLOOM_MISMATCH"
    assert result.trace[0].strategy == "question re-levelled to the target Bloom level"
    assert pipeline.task_for(3, path) in result.final_explanation
    assert result.unresolved_claims == []


def test_stagnation_is_reported_but_not_repaired_when_rewriting_is_off(path: dict) -> None:
    pipeline = C4Pipeline.from_files(DATA / "knowledge_graph.json", replace(PROGRESSIVE, rewrite=False))
    result = pipeline.run(path, ready_learner(level=2), "A heap can be stored in an array.")
    assert result.progression["stagnation_after"] is True
    assert result.final_explanation == "A heap can be stored in an array."


def test_stagnation_check_can_be_switched_off(path: dict) -> None:
    pipeline = C4Pipeline.from_files(DATA / "knowledge_graph.json", replace(PROGRESSIVE, check_stagnation=False))
    result = pipeline.run(path, ready_learner(level=2), "A heap can be stored in an array.")
    assert result.progression["stagnation_before"] is None and result.trace == []


def test_questions_join_the_cognitive_denominator_but_not_the_hallucination_one(
        pipeline: C4Pipeline, path: dict) -> None:
    text = ("A heap can be stored in an array. "
            "Can you justify when a heap is the better choice and evaluate its trade-offs?")
    rates = claim_rates(pipeline.run(path, ready_learner(level=2), text).initial_claims)
    assert rates["claims"] == 1 and rates["hallucination_rate"] == 0.0
    assert rates["cognitive_mismatch_rate"] == 50.0


def test_hints_and_questions_written_by_c4_are_grounded_and_do_not_dilute_rates(
        pipeline: C4Pipeline, path: dict) -> None:
    learner = ready_learner(level=2)
    decision = pipeline.progression_decision(path, learner)
    text = " ".join(pipeline.check_section(path, learner, decision))
    result = pipeline.run(path, learner, text)
    assert all(item.claim.source == "grounded" for item in result.initial_claims)
    assert claim_rates(result.initial_claims)["claims"] == 0 and result.trace == []


def test_a_lookalike_question_is_not_trusted_as_grounded(pipeline: C4Pipeline, path: dict) -> None:
    lookalike = "Can you apply Heaps to a small example and trace each step now?"
    result = pipeline.run(path, ready_learner(level=2), lookalike)
    assert result.initial_claims[0].claim.source == "task"


def test_scaffold_fades_with_demonstrated_success(pipeline: C4Pipeline, path: dict) -> None:
    learner = ready_learner(level=2)
    full = pipeline.scaffold_hints(path, learner, pipeline.progression_decision(path, learner))
    assert len(full) == 2
    learner["bloom"]["heap"]["attempts"] = [{"session": 1, "level": 2, "score": 0.9}]
    partial = pipeline.scaffold_hints(path, learner, pipeline.progression_decision(path, learner))
    assert len(partial) == 1
    learner["bloom"]["heap"]["attempts"].append({"session": 2, "level": 2, "score": 0.9})
    assert pipeline.scaffold_hints(path, learner, pipeline.progression_decision(path, learner)) == []


def test_report_exposes_the_progression_block_and_visual(pipeline: C4Pipeline, path: dict) -> None:
    learner = ready_learner(level=2)
    report = pipeline.run(path, learner, "A heap can be stored in an array.").to_dict()
    assert report["schema_version"] == "c4-report/1.2"
    assert report["progression"]["target_name"] == "Apply"
    assert pipeline.visual(path, learner)["progression"]["scaffold"] == "full"


def test_other_targets_get_a_task_for_their_own_concept(pipeline: C4Pipeline) -> None:
    stack_path = build_verified_path("stack", pipeline.kg)
    learner = {"learner_id": "x", "mastery": {"arrays": 0.9}, "uncertainty": {"arrays": 0.05}}
    result = pipeline.run(stack_path, learner, "A stack follows the last-in-first-out rule.")
    assert "Stacks" in result.final_explanation and result.progression["action"] == "start"


def _draft(attempts: list[dict], progressive: bool = True) -> str:
    from c4 import TemplateExplanationGenerator
    learner = ready_learner(level=2)
    learner["bloom"]["heap"]["attempts"] = attempts
    pipeline = C4Pipeline.from_files(DATA / "knowledge_graph.json")
    return TemplateExplanationGenerator().generate(
        load("verified_path.json"), learner, pipeline.kg, C4Config(progressive=progressive))


def test_draft_detail_fades_with_consecutive_passes() -> None:
    passes = [{"session": 1, "level": 2, "score": 0.9}, {"session": 2, "level": 2, "score": 0.9}]
    full, partial, minimal = _draft([]), _draft(passes[:1]), _draft(passes)
    assert "Refresher" in full and "Common mistakes" in full and full.count("Hint:") == 2
    assert "Refresher" not in partial and partial.count("Hint:") == 1
    assert "Hint:" not in minimal and "Before you start" not in minimal
    assert len(full) > len(partial) > len(minimal)


def test_every_progressive_draft_ends_with_the_target_level_question_and_is_not_stagnant(
        pipeline: C4Pipeline, path: dict) -> None:
    for attempts in ([], [{"session": 1, "level": 2, "score": 0.9}]):
        draft = _draft(attempts)
        assert draft.rstrip().endswith("Can you apply Heaps to a small example and trace each step?")
        learner = ready_learner(level=2)
        learner["bloom"]["heap"]["attempts"] = attempts
        assert pipeline.run(path, learner, draft).progression["stagnation_before"] is False


def test_static_drafts_have_no_check_section() -> None:
    assert "Check yourself" not in _draft([], progressive=False)
