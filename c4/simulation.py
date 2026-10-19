"""Multi-session simulated-learner experiment for Bloom-level progression (RQ4b).

Honest scope. A simulation cannot show that real students learn better; it can show whether
the *mechanism* (target level, contingent scaffolding, demotion rule, check-question update)
behaves as designed under stated assumptions about how learners learn, and where it stops
helping. The learner models below are assumptions, and the result for the ZPD model follows
partly from that assumption. For that reason the experiment also runs two control learner
models in which progression has no advantage (``flat``) or a disadvantage (``matched``);
a fair mechanism should tie or lose there. All draws are seeded and paired across conditions.

Conditions (same hidden learner, same environment noise; only the explanation policy differs):

- A, unverified: the explanation level is drawn uniformly from Bloom levels 1-4.
- B, current C4: the same draw, repaired down to the static Bloom ceiling (2, or 3 when the
  prerequisites are mastered); no check question, no tracking.
- C, progressive C4: the target level and scaffold come from the real
  ``C4Pipeline.progression_decision``; each session ends with a check question whose result
  updates the learner's Bloom record.

Two ablations of C isolate its parts: ``C_no_fading`` keeps the target level but gives generic
partial support, and ``C_no_stretch`` keeps contingent scaffolding but never aims above the
demonstrated level.

Hidden learner state: ``cap`` (Bloom capability as a real number; the true level is
``floor(cap + 0.5)``), a learning rate, and prerequisite mastery that grows independently of
the condition. C4 sees only mastery, uncertainty, and its own Bloom record.
"""

from __future__ import annotations

import math
import random
from typing import Any

from .metrics import bootstrap_mean_ci, cohens_dz, wilcoxon_signed_rank
from .paths import build_verified_path
from .pipeline import C4Config, C4Pipeline
from .progression import LearnerProgress

CONDITIONS = ("A_unverified", "B_current_c4", "C_progressive")
ABLATIONS = ("C_no_fading", "C_no_stretch")
LEARNER_MODELS = ("zpd", "flat", "matched")
SUPPORT = {"full": 0.5, "partial": 0.25, "minimal": 0.0}
DEFAULT_SUPPORT = SUPPORT["partial"]  # generic, un-tailored support in conditions A and B
PROFILES = {"novice": (0.2, 1.0), "intermediate": (1.0, 2.0), "advanced": (2.0, 3.0)}
PREREQUISITE_GROWTH = 0.07  # per session, independent of the condition
ASSUMPTIONS = [
    "Learner capability is a real number; the true Bloom level is floor(capability + 0.5).",
    "ZPD model: learning is fastest when the explanation is above capability but within reach "
    "(1 level, plus 0.5 / 0.25 / 0 for full / partial / minimal support); too easy gives little; too hard gives none.",
    "Flat control: learning is independent of the explanation level.",
    "Matched control: learning is fastest when the explanation is at the learner's level; stretching hurts.",
    "Learning is halved while the target's prerequisites are not mastered.",
    "Condition A draws the explanation level uniformly from 1-4; B caps that draw at the static ceiling.",
    "Conditions A and B receive generic partial support; C receives full, partial or minimal support by policy.",
    "Check answers are Bernoulli with logistic probability in (capability + support - question level).",
    "Parameters are pilot values chosen for plausibility, not fitted to data from real learners.",
]


def _sigmoid(value: float) -> float:
    return 1 / (1 + math.exp(-value))


def _gain(model: str, level: int, cap: float, support: float, rate: float, ready: bool) -> float:
    gap = level - cap
    reach = 1.0 + support
    if model == "flat":
        shape = 0.5
    elif model == "matched":
        shape = max(0.0, 1 - max(0.0, abs(gap) - 0.5)) if abs(gap) <= 1.5 else 0.0
    else:
        if gap <= 0:
            shape = 0.1
        elif gap <= reach:
            shape = 1.0
        else:
            shape = max(0.0, 1 - (gap - reach))
    return rate * shape * (1.0 if ready else 0.5)


def true_level(cap: float) -> int:
    return max(0, min(6, int(math.floor(cap + 0.5))))


def draw_cohort(learners: int, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(f"cohort:{seed}")
    names = list(PROFILES)
    cohort = []
    for index in range(learners):
        profile = names[index % len(names)]
        low, high = PROFILES[profile]
        cohort.append({
            "id": f"S{index:03d}", "profile": profile,
            "cap0": rng.uniform(low, high),
            "rate": max(0.05, rng.gauss(0.35, 0.1)),
            "prereq0": rng.uniform(0.3, 0.95),
            "seed": rng.randrange(1 << 30),
        })
    return cohort


def run_learner(
    params: dict[str, Any], condition: str, model: str, sessions: int,
    static: C4Pipeline, progressive: C4Pipeline, path: dict[str, Any], target: str,
) -> dict[str, Any]:
    cap = params["cap0"]
    env = random.Random(f"env:{params['seed']}")
    pick = random.Random(f"pick:{params['seed']}:{condition}")
    progress = LearnerProgress()
    history: list[dict[str, Any]] = []
    prereqs = static.kg["concepts"][target]["prerequisites"]
    for session in range(1, sessions + 1):
        mastery = min(0.95, params["prereq0"] + PREREQUISITE_GROWTH * (session - 1))
        state = {
            "learner_id": params["id"],
            "mastery": {**{item: mastery for item in prereqs}, target: 0.3},
            "uncertainty": {**{item: 0.1 for item in prereqs}, target: 0.2},
            "bloom": progress.to_state(),
        }
        # Environment noise is drawn in every condition so that the streams stay paired.
        gain_noise, answer_draw, score_draw = env.gauss(0, 0.05), env.random(), env.random()
        draw = pick.choice((1, 2, 3, 4))
        decision = None
        if condition == "A_unverified":
            level, support = draw, DEFAULT_SUPPORT
        elif condition == "B_current_c4":
            level, support = min(draw, static._bloom_ceiling(path, state)), DEFAULT_SUPPORT
        else:
            decision = progressive.progression_decision(path, state)
            level, support = decision.target_level, SUPPORT[decision.scaffold]
            if condition == "C_no_fading":
                support = DEFAULT_SUPPORT
            elif condition == "C_no_stretch":
                level = max(1, decision.current_level)
        ready = mastery >= 0.7
        gap = level - cap
        cap = min(6.0, max(0.0, cap + _gain(model, level, cap, support, params["rate"], ready) + gain_noise))
        row = {"session": session, "level": level, "gap": round(gap, 3), "support": support,
               "true_level": true_level(cap), "cap": round(cap, 3),
               "too_hard": gap > 1.0 + support, "too_easy": gap <= 0}
        if decision is not None:
            probability = _sigmoid(2.5 * (cap + support - level + 0.5))
            passed = answer_draw < probability
            score = 0.75 + 0.25 * score_draw if passed else 0.35 * score_draw
            progress = progress.with_attempt(target, session, level, score, decision.scaffold)
            row.update({"action": decision.action, "scaffold": decision.scaffold,
                        "observed_level": progress.get(target).level, "score": round(score, 3)})
        history.append(row)
    return {"id": params["id"], "profile": params["profile"], "cap0": params["cap0"],
            "initial_level": true_level(params["cap0"]), "history": history}


def _first_session_at(history: list[dict[str, Any]], level: int, sessions: int) -> int:
    for row in history:
        if row["true_level"] >= level:
            return row["session"]
    return sessions + 1  # censored: not reached within the study


def summarize_condition(runs: list[dict[str, Any]], sessions: int) -> dict[str, Any]:
    finals = [r["history"][-1]["true_level"] for r in runs]
    final_cap = [r["history"][-1]["cap"] for r in runs]
    gains = [fc - r["cap0"] for fc, r in zip(final_cap, runs)]
    rows = [row for r in runs for row in r["history"]]
    trajectory = []
    for session in range(1, sessions + 1):
        values = [r["history"][session - 1]["true_level"] for r in runs]
        trajectory.append(round(sum(values) / len(values), 3))
    tracked = [r for r in runs if "observed_level" in r["history"][-1]]
    return {
        "learners": len(runs),
        "mean_final_level": round(sum(finals) / len(finals), 3),
        "mean_capability_gain": round(sum(gains) / len(gains), 3),
        "mean_sessions_to_level_3": round(sum(_first_session_at(r["history"], 3, sessions) for r in runs) / len(runs), 3),
        "share_reaching_level_3_pct": round(100 * sum(f >= 3 for f in finals) / len(finals), 1),
        "trajectory_mean_true_level": trajectory,
        "sessions_too_hard_pct": round(100 * sum(row["too_hard"] for row in rows) / len(rows), 1),
        "sessions_too_easy_pct": round(100 * sum(row["too_easy"] for row in rows) / len(rows), 1),
        "tracking_mae_final": (round(sum(abs(r["history"][-1]["observed_level"] - r["history"][-1]["true_level"])
                                       for r in tracked) / len(tracked), 3) if tracked else None),
    }


def paired(runs_x: list[dict[str, Any]], runs_y: list[dict[str, Any]], key: str, seed: int) -> dict[str, Any]:
    """Paired comparison x - y on one per-learner outcome; a positive difference favours x.

    Outcomes: ``capability_gain`` (final minus initial capability) or ``sessions_saved_to_level_3``.
    """
    def outcome(run: dict[str, Any]) -> float:
        if key == "capability_gain":
            return run["history"][-1]["cap"] - run["cap0"]
        # Sessions saved: higher is better; a learner who never reaches level 3 saves zero.
        sessions = len(run["history"])
        return float(sessions + 1 - _first_session_at(run["history"], 3, sessions))

    differences = [outcome(x) - outcome(y) for x, y in zip(runs_x, runs_y)]
    mean = sum(differences) / len(differences)
    return {
        "outcome": key,
        "mean_difference": round(mean, 4),
        "ci95_bootstrap": bootstrap_mean_ci(differences, seed),
        "wilcoxon": wilcoxon_signed_rank(differences),
        "cohens_dz": cohens_dz(differences),
        "learners_better": sum(d > 0 for d in differences),
        "learners_worse": sum(d < 0 for d in differences),
        "learners_equal": sum(d == 0 for d in differences),
    }


def run_experiment(
    knowledge_graph: dict[str, Any], learners: int = 300, sessions: int = 8, seed: int = 2026,
    target: str = "heap",
) -> dict[str, Any]:
    static = C4Pipeline(knowledge_graph, C4Config())
    progressive = C4Pipeline(knowledge_graph, C4Config(progressive=True))
    path = build_verified_path(target, knowledge_graph)
    cohort = draw_cohort(learners, seed)
    models: dict[str, Any] = {}
    for model in LEARNER_MODELS:
        runs = {
            condition: [run_learner(p, condition, model, sessions, static, progressive, path, target) for p in cohort]
            for condition in CONDITIONS + ABLATIONS
        }
        # Sessions-to-level-3 is only meaningful for learners who start below level 3.
        eligible = [i for i, r in enumerate(runs["A_unverified"]) if r["initial_level"] < 3]
        subset = {c: [rs[i] for i in eligible] for c, rs in runs.items()}
        models[model] = {
            "conditions": {c: summarize_condition(rs, sessions) for c, rs in runs.items()},
            "by_profile": {
                profile: {c: summarize_condition([r for r in rs if r["profile"] == profile], sessions)
                          for c, rs in runs.items() if c in CONDITIONS}
                for profile in PROFILES
            },
            "paired": {
                "C_vs_B": paired(runs["C_progressive"], runs["B_current_c4"], "capability_gain", seed),
                "C_vs_A": paired(runs["C_progressive"], runs["A_unverified"], "capability_gain", seed),
                "B_vs_A": paired(runs["B_current_c4"], runs["A_unverified"], "capability_gain", seed),
                "C_vs_C_no_fading": paired(runs["C_progressive"], runs["C_no_fading"], "capability_gain", seed),
                "C_vs_C_no_stretch": paired(runs["C_progressive"], runs["C_no_stretch"], "capability_gain", seed),
                "C_vs_B_sessions_saved_to_level_3": {
                    "learners_started_below_level_3": len(eligible),
                    **paired(subset["C_progressive"], subset["B_current_c4"], "sessions_saved_to_level_3", seed),
                },
            },
            "example_c_history": runs["C_progressive"][0]["history"],
        }
    return {
        "config": {"learners": learners, "sessions": sessions, "seed": seed, "target": target,
                   "conditions": list(CONDITIONS), "learner_models": list(LEARNER_MODELS)},
        "assumptions": ASSUMPTIONS,
        "models": models,
        "sensitivity_sessions": _sensitivity(knowledge_graph, learners, seed, target),
        "caveat": ("Simulated learners are not students. Under the ZPD model the advantage of condition C follows "
                   "partly from the model's own assumption; the flat and matched controls show where the mechanism "
                   "does not help. The result supports the design and its limits, not a claim about real learners. "
                   "The human pilot (docs/PILOT_STUDY.md) is the validation."),
    }


def _sensitivity(knowledge_graph: dict[str, Any], learners: int, seed: int, target: str) -> dict[str, Any]:
    """C minus B capability gain for shorter and longer studies, per learner model."""
    rows: dict[str, Any] = {}
    static = C4Pipeline(knowledge_graph, C4Config())
    progressive = C4Pipeline(knowledge_graph, C4Config(progressive=True))
    path = build_verified_path(target, knowledge_graph)
    cohort = draw_cohort(learners, seed)
    for sessions in (4, 8, 12):
        rows[str(sessions)] = {}
        for model in LEARNER_MODELS:
            c = [run_learner(p, "C_progressive", model, sessions, static, progressive, path, target) for p in cohort]
            b = [run_learner(p, "B_current_c4", model, sessions, static, progressive, path, target) for p in cohort]
            result = paired(c, b, "capability_gain", seed)
            rows[str(sessions)][model] = {k: result[k] for k in ("mean_difference", "ci95_bootstrap", "cohens_dz")}
    return rows
