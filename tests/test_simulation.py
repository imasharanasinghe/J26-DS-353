from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from c4.adapters import load_json
from c4.metrics import bootstrap_mean_ci, cohens_dz, wilcoxon_signed_rank
from c4.simulation import draw_cohort, run_experiment, true_level

KG = load_json(Path(__file__).resolve().parents[1] / "c4" / "data" / "knowledge_graph.json")


@lru_cache(maxsize=1)
def small():
    return run_experiment(KG, learners=90, sessions=8, seed=7)


def test_experiment_is_deterministic_for_a_seed() -> None:
    again = run_experiment(KG, learners=90, sessions=8, seed=7)
    assert again["models"]["zpd"]["conditions"] == small()["models"]["zpd"]["conditions"]


def test_cohort_is_split_evenly_across_profiles() -> None:
    cohort = draw_cohort(90, 7)
    assert {p: sum(c["profile"] == p for c in cohort) for p in ("novice", "intermediate", "advanced")} == {
        "novice": 30, "intermediate": 30, "advanced": 30}


def test_flat_control_cannot_separate_the_conditions() -> None:
    flat = small()["models"]["flat"]
    levels = {name: row["mean_final_level"] for name, row in flat["conditions"].items()}
    assert len(set(levels.values())) == 1                      # progression has no advantage here
    assert flat["paired"]["C_vs_B"]["mean_difference"] == 0.0


def test_stretching_is_the_active_ingredient_under_the_zpd_model() -> None:
    zpd = small()["models"]["zpd"]
    assert zpd["paired"]["C_vs_B"]["mean_difference"] > 0
    assert zpd["paired"]["C_vs_C_no_stretch"]["mean_difference"] > zpd["paired"]["C_vs_B"]["mean_difference"]
    assert zpd["conditions"]["C_progressive"]["mean_final_level"] > zpd["conditions"]["C_no_stretch"]["mean_final_level"]


def test_matched_control_removes_the_advantage() -> None:
    matched = small()["models"]["matched"]
    assert matched["paired"]["C_vs_B"]["mean_difference"] < small()["models"]["zpd"]["paired"]["C_vs_B"]["mean_difference"]
    assert matched["paired"]["C_vs_B_sessions_saved_to_level_3"]["mean_difference"] <= 0.05


def test_progressive_runs_record_policy_decisions_and_tracking() -> None:
    history = small()["models"]["zpd"]["example_c_history"]
    assert history[0]["action"] == "start" and history[0]["level"] == 1
    assert all(1 <= row["level"] <= 6 and 0 <= row["observed_level"] <= 6 for row in history)
    assert small()["models"]["zpd"]["conditions"]["C_progressive"]["tracking_mae_final"] is not None


def test_trajectories_have_one_point_per_session_and_never_exceed_the_scale() -> None:
    for model in small()["models"].values():
        for row in model["conditions"].values():
            assert len(row["trajectory_mean_true_level"]) == 8 and max(row["trajectory_mean_true_level"]) <= 6


def test_true_level_is_the_rounded_capability() -> None:
    assert [true_level(x) for x in (0.2, 0.5, 1.49, 6.4, -1)] == [0, 1, 1, 6, 0]


def test_assumptions_and_caveat_are_part_of_the_result() -> None:
    result = small()
    assert any("ZPD" in item for item in result["assumptions"]) and "not students" in result["caveat"]


def test_statistics_helpers() -> None:
    assert bootstrap_mean_ci([], 0) is None
    low, high = bootstrap_mean_ci([1.0, 2.0, 3.0, 4.0], 0)
    assert 1.0 <= low <= 2.5 <= high <= 4.0
    assert wilcoxon_signed_rank([1, 2, 3])["p"] is None            # too few pairs
    assert wilcoxon_signed_rank([0.5] * 12)["p"] < 0.01
    assert wilcoxon_signed_rank([1, -1] * 10)["p"] > 0.5
    assert cohens_dz([1.0, 1.0, 1.0]) is None and cohens_dz([1.0, 2.0, 3.0]) == 2.0


def test_rq4a_progressive_repair_hits_the_target_level_without_new_violations() -> None:
    from c4.evaluation import evaluate_progressive_stress

    result = evaluate_progressive_stress(KG)
    table = result["conditions"]
    assert result["runs"] == 84 and result["runs_with_unresolved_claims"] == 0
    assert table["unverified"]["question_at_target_level_pct"] == 0.0
    assert table["static_c4"]["question_at_target_level_pct"] == 0.0
    assert table["progressive_c4"]["question_at_target_level_pct"] == 100.0
    assert table["progressive_c4"]["runs_with_violation"] == 0
    assert table["progressive_c4"]["hallucination_rate"] == 0.0
    assert set(result["policy_actions"]) == {"start", "consolidate", "advance"}


def test_progression_report_renders_every_section() -> None:
    import importlib.util

    from c4.evaluation import evaluate_progressive_stress

    path = Path(__file__).resolve().parents[1] / "scripts" / "run_c4_progression.py"
    spec = importlib.util.spec_from_file_location("run_c4_progression", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    text = module.render(evaluate_progressive_stress(KG), small())
    for heading in ("## RQ4a", "## RQ4b", "### Assumptions", "Flat control", "Matched control",
                    "Sensitivity to study length", "Reading the results honestly"):
        assert heading in text
