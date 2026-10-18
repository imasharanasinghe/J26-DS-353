from __future__ import annotations

import json
from pathlib import Path

import pytest

from c4 import C4Config, C4Pipeline
from c4.evaluation import evaluate_stress
from c4.metrics import confusion, mcnemar_exact, wilson_interval
from c4.paths import build_verified_path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "c4" / "data"


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


@pytest.fixture
def pipeline() -> C4Pipeline:
    return C4Pipeline.from_files(DATA / "knowledge_graph.json")


def run(pipeline: C4Pipeline, text: str, learner: dict | None = None, target: str = "heap"):
    path = load("verified_path.json") if target == "heap" else build_verified_path(target, pipeline.kg)
    return pipeline.run(path, learner or load("learner_state.json"), text)


def ready_learner() -> dict:
    learner = load("learner_state.json")
    learner["mastery"].update({"tree": 0.9, "binary_tree": 0.9})
    learner["uncertainty"].update({"tree": 0.1, "binary_tree": 0.1})
    return learner


def test_rejects_unverified_c3_path(pipeline: C4Pipeline) -> None:
    path = load("verified_path.json")
    path["verified"] = False
    with pytest.raises(ValueError, match="verified paths"):
        pipeline.run(path, load("learner_state.json"), "A heap is a complete binary tree.")


def test_supported_and_appropriate_claim_is_untouched(pipeline: C4Pipeline) -> None:
    result = run(pipeline, "A heap can be stored in an array.")
    claim = result.claims[0]
    assert (claim.factual_status, claim.cognitive_status) == ("ENTAILED", "APPROPRIATE")
    assert claim.confidence == "HIGH" and result.trace == []
    assert result.final_explanation == result.original_explanation


def test_contradicted_claim_is_flagged_with_evidence_and_repaired(pipeline: C4Pipeline) -> None:
    result = run(pipeline, "A heap is always fully sorted.")
    first = result.initial_claims[0]
    assert first.factual_status == "CONTRADICTED"
    assert "CONTRADICTED_CLAIM" in first.violations and first.evidence
    assert result.claims[0].accepted and result.unresolved_claims == []


def test_unsupported_claim_is_flagged(pipeline: C4Pipeline) -> None:
    result = run(pipeline, "Heaps always take constant time for every operation.")
    assert result.initial_claims[0].factual_status == "UNSUPPORTED"
    assert "UNSUPPORTED_CLAIM" in result.initial_claims[0].violations


def test_true_but_cognitively_inappropriate_claim_gets_guidance_not_a_fact_swap(
    pipeline: C4Pipeline,
) -> None:
    result = run(pipeline, "A heap is a complete binary tree.")
    first = result.initial_claims[0]
    assert first.factual_status == "ENTAILED"
    assert first.cognitive_status == "UNMASTERED_PREREQUISITE"
    assert result.trace[0].strategy == "prerequisite-review guidance"
    assert result.review_first == ["binary_tree"]
    assert result.claims[0].accepted


def test_valid_claims_are_preserved_when_neighbours_are_repaired(pipeline: C4Pipeline) -> None:
    good = "A heap can be stored in an array."
    result = run(pipeline, f"{good} A heap is always fully sorted.")
    assert result.final_explanation.startswith(good)
    assert [step.claim_id for step in result.trace] == ["claim-2"]
    assert result.metrics["new_violations_introduced"] == 0


def test_target_is_not_a_violation_just_for_being_new(pipeline: C4Pipeline) -> None:
    # Heap prerequisites are unmastered, but the claim only mentions the target.
    result = run(pipeline, "Heaps always take constant time.")
    assert result.initial_claims[0].cognitive_status == "APPROPRIATE"


def test_bloom_mismatch_above_ceiling(pipeline: C4Pipeline) -> None:
    result = run(pipeline, "Evaluate why a heap can be stored in an array.")
    assert result.initial_claims[0].factual_status == "ENTAILED"
    assert result.initial_claims[0].cognitive_status == "BLOOM_MISMATCH"


def test_ceiling_rises_only_when_all_target_prerequisites_are_mastered(
    pipeline: C4Pipeline,
) -> None:
    text = "Analyze why a heap can be stored in an array."  # Bloom 4 > ceiling 3 either way
    assert run(pipeline, text, ready_learner()).initial_claims[0].cognitive_status == "BLOOM_MISMATCH"
    path = load("verified_path.json")
    assert pipeline._bloom_ceiling(path, ready_learner()) == 3
    assert pipeline._bloom_ceiling(path, load("learner_state.json")) == 2


def test_mastery_state_handles_uncertainty_missing_history_and_threshold_margin(
    pipeline: C4Pipeline,
) -> None:
    learner = {"mastery": {"a": 0.9, "b": 0.9, "c": 0.72, "d": 0.4},
               "uncertainty": {"a": 0.1, "b": 0.5, "c": 0.1, "d": 0.1}}
    state = lambda concept: pipeline._mastery_state(concept, learner)  # noqa: E731
    assert state("a") == "MASTERED"
    assert state("b") == "UNKNOWN"      # high uncertainty
    assert state("c") == "UNKNOWN"      # within margin of the 0.70 threshold
    assert state("d") == "UNMASTERED"
    assert state("missing") == "UNKNOWN"  # no learner history


def test_inconclusive_learner_evidence_is_not_silently_accepted(pipeline: C4Pipeline) -> None:
    learner = ready_learner()
    learner["uncertainty"]["arrays"] = 0.6
    result = run(pipeline, "A heap can be stored in an array.", learner)
    assert result.initial_claims[0].cognitive_status == "INCONCLUSIVE"
    assert "INCONCLUSIVE_COGNITIVE" in result.initial_claims[0].violations


def test_longest_match_does_not_double_count_contained_concepts(pipeline: C4Pipeline) -> None:
    assert pipeline._mentioned_concepts("A heap is a complete binary tree.") == ("binary_tree", "heap")
    assert pipeline._mentioned_concepts("Trees are hierarchical data structures.") == ("tree",)


def test_one_word_difference_to_a_known_false_statement_is_resolved_by_closeness(
    pipeline: C4Pipeline,
) -> None:
    true_claim = run(pipeline, "A stack follows the last-in-first-out rule.", target="stack")
    false_claim = run(pipeline, "A stack follows the first-in-first-out rule.", target="stack")
    assert true_claim.initial_claims[0].factual_status == "ENTAILED"
    assert false_claim.initial_claims[0].factual_status == "CONTRADICTED"


def test_negated_graph_fact_is_contradicted(pipeline: C4Pipeline) -> None:
    result = run(pipeline, "Recursion does not need a base case to stop.", target="recursion")
    assert result.initial_claims[0].factual_status == "CONTRADICTED"


def test_retry_limit_and_unresolved_policy(pipeline: C4Pipeline) -> None:
    capped = C4Pipeline(pipeline.kg, C4Config(max_rewrite_attempts=0))
    result = run(capped, "A heap is always fully sorted.")
    assert result.rewrite_attempts == 0
    assert result.unresolved_claims == ["claim-1"]
    assert result.final_explanation == result.original_explanation


def test_ablation_flags_isolate_each_dimension(pipeline: C4Pipeline) -> None:
    text = "A heap is a complete binary tree."  # true, but unmastered prerequisite
    factual_only = C4Pipeline(pipeline.kg, C4Config(check_cognitive=False))
    cognitive_only = C4Pipeline(pipeline.kg, C4Config(check_factual=False))
    assert run(factual_only, text).initial_claims[0].accepted
    assert not run(cognitive_only, text).initial_claims[0].accepted
    contradicted = "A heap is always fully sorted."
    assert not run(factual_only, contradicted).initial_claims[0].accepted
    assert run(cognitive_only, contradicted).initial_claims[0].accepted


def test_report_schema_and_metrics(pipeline: C4Pipeline) -> None:
    report = run(pipeline, "A heap is always fully sorted. A heap can be stored in an array.").to_dict()
    assert report["schema_version"] == "c4-report/1.0"
    assert report["rewrite_trace"][0]["claim_id"] == "claim-1"
    metrics = report["metrics"]
    assert metrics["before"]["hallucination_rate"] == 50.0
    assert metrics["after"]["hallucination_rate"] == 0.0
    assert metrics["rewrite_success_rate"] == 100.0
    json.dumps(report)  # serialisable


def test_metric_helpers() -> None:
    assert confusion([(True, True), (True, False), (False, True), (False, False)])["f1"] == 0.5
    assert mcnemar_exact(10, 0) == pytest.approx(2 / 1024)
    assert mcnemar_exact(0, 0) == 1.0
    assert wilson_interval(0, 28)[0] == 0.0


def test_verified_path_builder_orders_prerequisites_first(pipeline: C4Pipeline) -> None:
    path = build_verified_path("heap", pipeline.kg)
    ids = [step["id"] for step in path["path"]]
    assert ids.index("binary_tree") < ids.index("heap") and ids[-1] == "heap"
    with pytest.raises(ValueError):
        build_verified_path("nope", pipeline.kg)


def test_stress_evaluation_runs_and_full_c4_clears_violations() -> None:
    result = evaluate_stress(load("knowledge_graph.json"))
    assert result["cases"] == 28 and result["claims"] == 84
    assert result["detection"]["factual"]["f1"] == 1.0
    assert result["conditions_after_repair"]["full_c4"]["cases_with_violation"] == 0
    assert result["conditions_after_repair"]["factual_only"]["cognitive_mismatch_rate"] > 0
    assert result["conditions_after_repair"]["cognitive_only"]["hallucination_rate"] > 0


def test_singular_concept_name_matches_plural_graph_name(pipeline: C4Pipeline) -> None:
    result = pipeline.run(
        {
            "learner_id": "L02_intermediate",
            "target": "arrays",
            "verified": True,
            "path": [{"kind": "learn", "id": "arrays", "name": "Arrays"}],
        },
        load("learner_state.json"),
        "An array stores elements in contiguous indexed positions.",
    )
    assert result.claims[0].factual_status == "ENTAILED"
    assert result.claims[0].accepted is True


def test_complete_fixture_has_c3_contract() -> None:
    path = load("verified_path.json")
    assert path["verified"] is True
    assert {"learner_id", "target", "path"} <= path.keys()
