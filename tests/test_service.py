from __future__ import annotations

import pytest

from c4.service import MAX_EXPLANATION_CHARS, Workbench
from tests.stubs import StubGenerator


@pytest.fixture(scope="module")
def bench() -> Workbench:
    return Workbench(generator=StubGenerator())


def test_meta_describes_targets_presets_scenarios_and_defaults(bench: Workbench) -> None:
    meta = bench.meta()
    heap = next(item for item in meta["targets"] if item["id"] == "heap")
    assert {"valid", "factual", "cognitive", "mixed"} == set(heap["scenarios"])
    assert {"demo_learner", "all_mastered", "missing_prereq", "several_low", "uncertain"} <= set(
        heap["learner_presets"])
    assert meta["config_defaults"]["max_rewrite_attempts"] == 3
    assert meta["schema_version"] == "c4-report/1.2"


def test_every_target_has_a_usable_scenario_for_each_case(bench: Workbench) -> None:
    for target in bench.meta()["targets"]:
        for text in target["scenarios"].values():
            assert text.strip()


def test_verify_matches_the_cli_demo_result(bench: Workbench) -> None:
    heap = next(item for item in bench.meta()["targets"] if item["id"] == "heap")
    report = bench.verify({"target": "heap", "explanation": heap["scenarios"]["mixed"]})
    assert [c["factual_status"] for c in report["initial_claims"]] == [
        "ENTAILED", "CONTRADICTED", "ENTAILED"]
    assert report["initial_claims"][2]["cognitive_status"] == "UNMASTERED_PREREQUISITE"
    assert report["bloom_ceiling"] == 2
    assert report["unresolved_claims"] == []


def test_verify_uses_the_supplied_learner_state(bench: Workbench) -> None:
    payload = {"target": "heap", "explanation": "A heap is a complete binary tree.",
               "learner": {"mastery": {"binary_tree": 0.95, "arrays": 0.95},
                           "uncertainty": {"binary_tree": 0.05, "arrays": 0.05}}}
    report = bench.verify(payload)
    assert report["initial_claims"][0]["cognitive_status"] == "APPROPRIATE"
    assert report["bloom_ceiling"] == 3


def test_config_overrides_are_applied(bench: Workbench) -> None:
    payload = {"target": "heap", "explanation": "A heap is always fully sorted.",
               "config": {"rewrite": False}}
    report = bench.verify(payload)
    assert report["rewrite_trace"] == [] and report["unresolved_claims"] == ["claim-1"]


@pytest.mark.parametrize("bad", [
    {"target": "nope", "explanation": "x"},
    {"target": "heap", "explanation": "   "},
    {"target": "heap", "explanation": "x" * (MAX_EXPLANATION_CHARS + 1)},
    {"target": "heap", "explanation": "x", "learner": {"mastery": {"heap": 2}}},
    {"target": "heap", "explanation": "x", "learner": {"mastery": {"ghost": 0.5}}},
    {"target": "heap", "explanation": "x", "learner": {"mastery": {"heap": True}}},
    {"target": "heap", "explanation": "x", "config": {"mastery_threshold": 7}},
    {"target": "heap", "explanation": "x", "config": {"rewrite": "yes"}},
    {"target": "heap", "explanation": "x", "config": {"surprise": 1}},
])
def test_invalid_requests_are_rejected(bench: Workbench, bad: dict) -> None:
    with pytest.raises(ValueError):
        bench.verify(bad)


def test_generation_uses_the_model_body_the_learner_and_the_path(bench: Workbench) -> None:
    result = bench.generate({"target": "heap"})
    assert "Heaps" in result["explanation"] and "Binary Trees" in result["explanation"]
    assert result["source"] == "stub-model" and "Heaps" in result["prompt"]


def test_results_returns_committed_artefacts(bench: Workbench) -> None:
    results = bench.results()
    assert results["stress"]["cases"] == 28
    assert "C4 preliminary evaluation" in results["markdown"]


def test_unreachable_ollama_surfaces_as_runtime_error(bench: Workbench) -> None:
    from c4 import OllamaExplanationGenerator

    offline = Workbench(generator=OllamaExplanationGenerator(endpoint="http://127.0.0.1:1/api/chat", timeout=1.0))
    with pytest.raises(RuntimeError, match="Ollama is unavailable"):
        offline.generate({"target": "heap"})


def test_every_preset_and_scenario_round_trips_through_verify(bench: Workbench) -> None:
    for target in bench.meta()["targets"]:
        for preset in target["learner_presets"].values():
            for text in target["scenarios"].values():
                report = bench.verify({"target": target["id"], "explanation": text, "learner": preset})
                assert report["unresolved_claims"] == []


def test_explain_drafts_then_verifies_in_one_call(bench: Workbench) -> None:
    report = bench.explain({"target": "arrays"})
    assert report["generator"] == "stub-model"
    assert report["original_explanation"].strip() and report["final_explanation"].strip()
    assert report["unresolved_claims"] == []


def test_explain_reports_an_unreachable_generator(bench: Workbench) -> None:
    from c4 import OllamaExplanationGenerator

    offline = Workbench(generator=OllamaExplanationGenerator(endpoint="http://127.0.0.1:1/api/chat", timeout=1.0))
    with pytest.raises(RuntimeError):
        offline.explain({"target": "heap"})


def test_meta_exposes_the_c3_path_and_c1_context_for_the_inputs_view(bench: Workbench) -> None:
    heap = next(item for item in bench.meta()["targets"] if item["id"] == "heap")
    assert heap["path"]["verified"] is True and heap["path"]["target"] == "heap"
    assert [step["id"] for step in heap["graph_context"]] == [step["id"] for step in heap["path"]["path"]]
    assert all(item["facts"] for item in heap["graph_context"])


def test_demo_learner_carries_a_bloom_record_and_presets_are_seeded(bench: Workbench) -> None:
    heap = next(item for item in bench.meta()["targets"] if item["id"] == "heap")
    assert heap["learner_presets"]["demo_learner"]["bloom"]["arrays"]["level"] == 3
    seeded = heap["learner_presets"]["all_mastered"]["bloom"]["heap"]
    assert seeded["level"] == 1 and len(seeded["attempts"]) == 1


def test_bloom_state_is_validated_and_normalised(bench: Workbench) -> None:
    good = {"target": "heap", "explanation": "A heap can be stored in an array.",
            "learner": {"bloom": {"heap": {"level": 2}}}}
    assert bench.verify(good)["verified_path"] is True
    for bad in ({"ghost": {"level": 1}}, {"heap": {"level": 9}}, {"heap": "x"}, []):
        with pytest.raises(ValueError, match="bloom"):
            bench.verify({**good, "learner": {"bloom": bad}})


READY = {"mastery": {"binary_tree": 0.95, "arrays": 0.95}, "uncertainty": {"binary_tree": 0.05, "arrays": 0.05},
         "bloom": {"heap": {"level": 2}}}


def test_session_returns_a_verified_progressive_explanation_and_a_check_question(bench: Workbench) -> None:
    report = bench.session({"target": "heap", "learner": READY})
    assert report["schema_version"] == "c4-report/1.2" and report["unresolved_claims"] == []
    assert report["progression"]["target_name"] == "Apply" and report["progression"]["stagnation_after"] is False
    check = report["check"]
    assert check["level"] == 3 and check["question"] in report["final_explanation"]
    assert len(check["hints"]) == 2 and report["session"] == 1


def test_answer_updates_the_bloom_record_and_previews_the_next_decision(bench: Workbench) -> None:
    result = bench.answer({"target": "heap", "learner": READY, "level": 3, "score": 0.9, "scaffold": "full"})
    assert result["learner"]["bloom"]["heap"]["level"] == 3
    assert result["next"]["target_level"] == 4 and result["next"]["action"] == "advance"
    assert result["concept_progress"]["attempts"][0]["session"] == 1


def test_a_failed_stretch_is_retried_with_full_support(bench: Workbench) -> None:
    result = bench.answer({"target": "heap", "learner": READY, "level": 3, "score": 0.1})
    assert result["learner"]["bloom"]["heap"]["level"] == 2
    assert (result["next"]["action"], result["next"]["scaffold"]) == ("retry", "full")


def test_answers_accumulate_across_sessions_and_scaffolding_fades(bench: Workbench) -> None:
    learner = dict(READY)
    for _ in range(2):
        step = bench.answer({"target": "heap", "learner": learner, "level": bench.session(
            {"target": "heap", "learner": learner})["check"]["level"], "score": 0.9})
        learner = step["learner"]
    assert learner["bloom"]["heap"]["level"] == 4 and len(learner["bloom"]["heap"]["attempts"]) == 2
    assert step["next"]["scaffold"] == "minimal"


@pytest.mark.parametrize("bad", [
    {"level": 0, "score": 0.5}, {"level": 7, "score": 0.5}, {"level": "2", "score": 0.5},
    {"level": 2, "score": 1.5}, {"level": 2, "score": True}, {"level": 2, "score": 0.5, "scaffold": "huge"},
    {"level": 2, "score": 0.5, "session": 0},
])
def test_answer_rejects_invalid_input(bench: Workbench, bad: dict) -> None:
    with pytest.raises(ValueError):
        bench.answer({"target": "heap", "learner": READY, **bad})


def test_results_include_the_progression_and_bloom_evaluations(bench: Workbench) -> None:
    results = bench.results()
    assert set(results["progression"]) == {"rq1", "rq2"} and results["bloom"]["splits"]["test"]
