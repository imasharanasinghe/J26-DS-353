from __future__ import annotations

import pytest

from c4.service import MAX_EXPLANATION_CHARS, Workbench


@pytest.fixture(scope="module")
def bench() -> Workbench:
    return Workbench()


def test_meta_describes_targets_presets_scenarios_and_defaults(bench: Workbench) -> None:
    meta = bench.meta()
    heap = next(item for item in meta["targets"] if item["id"] == "heap")
    assert {"valid", "factual", "cognitive", "mixed"} == set(heap["scenarios"])
    assert {"demo_learner", "all_mastered", "missing_prereq", "several_low", "uncertain"} <= set(
        heap["learner_presets"])
    assert meta["config_defaults"]["max_rewrite_attempts"] == 3
    assert meta["schema_version"] == "c4-report/1.0"


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


def test_template_generation_uses_the_learner_and_path(bench: Workbench) -> None:
    result = bench.generate({"target": "heap", "source": "template"})
    assert "Heaps" in result["explanation"] and result["prompt"] is None
    with pytest.raises(ValueError):
        bench.generate({"target": "heap", "source": "gpt"})


def test_results_returns_committed_artefacts(bench: Workbench) -> None:
    results = bench.results()
    assert results["stress"]["cases"] == 28
    assert "C4 preliminary evaluation" in results["markdown"]


def test_unreachable_ollama_surfaces_as_runtime_error(bench: Workbench) -> None:
    from c4 import OllamaExplanationGenerator

    offline = OllamaExplanationGenerator(endpoint="http://127.0.0.1:1/api/chat", timeout=1.0)
    with pytest.raises(RuntimeError, match="Ollama is unavailable"):
        bench.generate({"target": "heap", "source": "ollama"}, ollama=offline)


def test_every_preset_and_scenario_round_trips_through_verify(bench: Workbench) -> None:
    for target in bench.meta()["targets"]:
        for preset in target["learner_presets"].values():
            for text in target["scenarios"].values():
                report = bench.verify({"target": target["id"], "explanation": text, "learner": preset})
                assert report["unresolved_claims"] == []
