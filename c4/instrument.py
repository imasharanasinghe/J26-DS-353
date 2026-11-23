"""Validation tests for the novice instrument (Phase 1: no humans needed).

A novice score proves nothing until the instrument itself passes these gates:

* leakage         empty or unrelated text must give a score near zero (or chance)
* discrimination  controlled explanations must be ranked in the expected order
* reliability     repeated runs on the same text must agree
* fairness        the same content written in weaker English must score the same
* depth           correct answers must trace to what the student wrote

Every function takes any ``Novice`` (see ``c4.novice``) so the lexical control and the LLM novice
go through identical tests.
"""

from __future__ import annotations

import statistics
from typing import Any

from . import synthetic
from .metrics import bootstrap_mean_ci
from .novice import Novice, graph_universe, summarise, take_test, traceability

# (better, worse, measure): the instrument should score `better` above `worse`.
EXPECTED_ORDER = (
    ("complete", "missing_one", "score"),
    ("missing_one", "half", "score"),
    ("half", "empty", "score"),
    ("complete", "wrong", "net"),
    ("missing_one", "wrong", "net"),
    ("complete", "garbled", "score"),
)
SAME_AS = (("complete", "paraphrased"),)


def _overall(novice: Novice, text: str, items: list[dict[str, Any]]) -> dict[str, float]:
    return summarise(take_test(novice, text, items))["all"]


def leakage(novice: Novice, kg: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
    """Score with no knowledge supplied. Chance is 1 / options; a leaky novice beats it."""
    chance = sum(1 / len(item["options"]) for item in items) / len(items)
    empty = _overall(novice, "", items)
    # Unrelated text: teach the novice about half of the concepts, test it on the other half.
    ids = list(kg["concepts"])
    taught, held_out = ids[: len(ids) // 2], ids[len(ids) // 2:]
    held_items = [item for item in items if item["concept"] in held_out]
    cross = _overall(novice, synthetic.explain(kg, "complete", concepts=taught), held_items)
    return {
        "chance_if_forced_to_guess": round(chance, 4),
        "empty_text": empty,
        "unrelated_text_heldout_items": {**cross, "items": len(held_items)},
        "leaks": empty["score"] > chance or cross["score"] > chance,
        "note": "score counts 'I don't know' as wrong; a score above chance means the novice used knowledge not in the text",
    }


def discrimination(novice: Novice, kg: dict[str, Any], items: list[dict[str, Any]],
                   seeds: int = 10, variants: tuple[str, ...] = synthetic.VARIANTS) -> dict[str, Any]:
    table: dict[str, dict[str, list[float]]] = {name: {"score": [], "net": []} for name in variants}
    for seed in range(seeds):
        for name in variants:
            row = _overall(novice, synthetic.explain(kg, name, seed), items)
            table[name]["score"].append(row["score"])
            table[name]["net"].append(row["net"])
    means = {name: {measure: round(statistics.fmean(values), 4) for measure, values in measures.items()}
             for name, measures in table.items()}
    checks = []
    for better, worse, measure in EXPECTED_ORDER:
        if better not in table or worse not in table:
            continue
        diffs = [a - b for a, b in zip(table[better][measure], table[worse][measure])]
        checks.append({
            "expect": f"{better} > {worse} ({measure})",
            "mean_difference": round(statistics.fmean(diffs), 4),
            "ci95": bootstrap_mean_ci(diffs, seed=1),
            "passes": bool(statistics.fmean(diffs) > 0 and (bootstrap_mean_ci(diffs, seed=1) or (0, 0))[0] > 0),
        })
    invariance = []
    for left, right in SAME_AS:
        if left in table and right in table:
            diffs = [a - b for a, b in zip(table[left]["score"], table[right]["score"])]
            invariance.append({
                "expect": f"{right} ~ {left}",
                "mean_difference": round(statistics.fmean(diffs), 4),
                "passes": abs(statistics.fmean(diffs)) <= 0.05,
            })
    return {"seeds": seeds, "means": means, "ordering_checks": checks, "invariance_checks": invariance,
            "all_pass": all(check["passes"] for check in checks + invariance)}


def reliability(novice: Novice, kg: dict[str, Any], items: list[dict[str, Any]],
                runs: int = 5, variant: str = "missing_one", temperature: float = 0.7) -> dict[str, Any]:
    """Same text, repeated runs. Deterministic novices have no spread; LLMs are run with varying seeds."""
    text = synthetic.explain(kg, variant, 0)
    scores: list[float] = []
    choices: dict[str, list[int | None]] = {item["id"]: [] for item in items}
    for run in range(runs):
        instance = novice.with_seed(run, temperature) if hasattr(novice, "with_seed") else novice
        results = take_test(instance, text, items)
        scores.append(summarise(results)["all"]["score"])
        for row in results:
            choices[row["id"]].append(row["chosen"])
    agreement = [max(values.count(value) for value in set(values)) / len(values) for values in choices.values()]
    return {
        "variant": variant, "runs": runs, "temperature": temperature if hasattr(novice, "with_seed") else None,
        "mean_score": round(statistics.fmean(scores), 4),
        "sd": round(statistics.pstdev(scores), 4),
        "range": [round(min(scores), 4), round(max(scores), 4)],
        "item_agreement": round(statistics.fmean(agreement), 4),
    }


def fairness(novice: Novice, kg: dict[str, Any], items: list[dict[str, Any]],
             levels: tuple[float, ...] = (0.3, 0.6), seeds: int = 10) -> dict[str, Any]:
    """Same content, weaker English: how much does the score fall? Also the concept-list option."""
    clean = [_overall(novice, synthetic.explain(kg, "complete", seed), items)["score"] for seed in range(seeds)]
    rows = {}
    for level in levels:
        gaps = []
        for seed in range(seeds):
            text = synthetic.weaker_writer(synthetic.explain(kg, "complete", seed), level, seed)
            gaps.append(clean[seed] - _overall(novice, text, items)["score"])
        rows[f"weaker_writer_{level}"] = {
            "mean_gap": round(statistics.fmean(gaps), 4), "ci95": bootstrap_mean_ci(gaps, seed=2)}
    listed = _overall(novice, synthetic.as_concept_list(kg), items)["score"]
    return {
        "clean_prose_score": round(statistics.fmean(clean), 4),
        "gap_vs_clean_prose": rows,
        "concept_list_score": round(listed, 4),
        "concept_list_gap": round(statistics.fmean(clean) - listed, 4),
        "note": "gap = score(clean prose) - score(altered text) for identical content; 0 means style-blind",
    }


def depth(text: str, kg: dict[str, Any], results: list[dict[str, Any]],
          items: list[dict[str, Any]]) -> dict[str, Any]:
    """Credit only correct answers that trace to the student's own statements."""
    by_id = {item["id"]: item for item in items}
    universe = graph_universe(kg)
    traced = untraced = 0
    for row in results:
        if not row["correct"]:
            continue
        if traceability(text, by_id[row["id"]], universe) >= 1.0:
            traced += 1
        else:
            untraced += 1
    total = len(results)
    return {
        "correct": traced + untraced, "traced": traced, "untraced": untraced,
        "raw_score": round((traced + untraced) / total, 4) if total else None,
        "depth_adjusted_score": round(traced / total, 4) if total else None,
    }


def run_gate(novice: Novice, kg: dict[str, Any], items: list[dict[str, Any]], seeds: int = 10,
             runs: int = 5) -> dict[str, Any]:
    """Phase 1 gate: if the novice fails leakage and discrimination, stop and report that."""
    leak = leakage(novice, kg, items)
    disc = discrimination(novice, kg, items, seeds)
    rel = reliability(novice, kg, items, runs)
    fair = fairness(novice, kg, items, seeds=seeds)
    return {"novice": novice.name, "items": len(items), "leakage": leak, "discrimination": disc,
            "reliability": rel, "fairness": fair,
            "gate_passed": (not leak["leaks"]) and disc["all_pass"]}
