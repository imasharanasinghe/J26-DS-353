"""Preliminary C4 evaluation: controlled violation stress test and natural generations.

Honest scope (see docs/GUIDELINES.md): the stress-test reference labels are assigned by
construction from the case recipe and a hand-written mention table, NOT by two
independent human annotators, so no Cohen's kappa exists yet. Post-repair rates are
measured by the same verifier and are therefore not independent evidence.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import replace
from pathlib import Path
from typing import Any

from .metrics import (
    claim_rates,
    confusion,
    mcnemar_exact,
    percent,
    wilson_interval,
)
from .bloom import estimate_level, estimate_level_v2, score_estimator
from .explainer import GENERATION_OPTIONS
from .paths import build_verified_path
from .pipeline import C4Config, C4Pipeline

CORPUS_VERSION = "stress-v1"

# Hand-annotated non-target concepts that each graph statement relies on.
MENTIONS: dict[str, list[str]] = {
    "A heap is a complete binary tree.": ["binary_tree"],
    "A heap can be stored in an array.": ["arrays"],
    "A heap is a fully sorted array.": ["arrays"],
    "A binary tree is a tree in which every node has at most two children.": ["tree"],
    "Tree nodes can be traversed using recursion.": ["recursion"],
    "A stack can be implemented with an array.": ["arrays"],
    "A queue can be implemented with an array.": ["arrays"],
}

PROFILES = ("all_mastered", "missing_prereq", "several_low", "uncertain")
INJECTIONS = ("contradicted", "unsupported", "bloom_unsupported", "too_advanced_correct")


def make_learner(kg: dict[str, Any], target: str, profile: str) -> tuple[dict, dict[str, str]]:
    """Return (C2-shaped learner, hand annotation of each non-target concept)."""
    concepts = [c for c in kg["concepts"] if c != target]
    prereqs = kg["concepts"][target].get("prerequisites", [])
    mastery: dict[str, float] = {}
    uncertainty: dict[str, float] = {}
    annotation: dict[str, str] = {}
    for concept in kg["concepts"]:
        if concept == target:
            mastery[concept], uncertainty[concept] = 0.3, 0.2
            continue
        state, score, spread = "mastered", 0.9, 0.1
        if profile == "missing_prereq" and prereqs and concept == prereqs[0]:
            state, score, spread = "unmastered", 0.3, 0.2
        elif profile == "several_low":
            state, score, spread = "unmastered", 0.35, 0.2
        elif profile == "uncertain":
            state, score, spread = "uncertain", 0.85, 0.4
        mastery[concept], uncertainty[concept] = score, spread
        annotation[concept] = state
    learner = {"learner_id": f"{profile}:{target}", "mastery": mastery, "uncertainty": uncertainty}
    return learner, annotation


def _cognitive_truth(mentions: list[str], bloom: bool, annotation: dict[str, str]) -> str:
    if bloom:
        return "BLOOM_MISMATCH"
    states = [annotation.get(item, "mastered") for item in mentions]
    if "unmastered" in states:
        return "UNMASTERED_PREREQUISITE"
    if "uncertain" in states:
        return "INCONCLUSIVE"
    return "APPROPRIATE"


def build_stress_corpus(kg: dict[str, Any]) -> list[dict[str, Any]]:
    cases = []
    targets = list(kg["concepts"])
    for ti, target in enumerate(targets):
        concept = kg["concepts"][target]
        name = concept["name"]
        fact_a, fact_b = concept["facts"][0], concept["facts"][1]
        false_text = concept["known_false"][0]
        for pi, profile in enumerate(PROFILES):
            learner, annotation = make_learner(kg, target, profile)
            injection = INJECTIONS[(ti + pi) % len(INJECTIONS)]
            if injection == "contradicted":
                text, factual, bloom = false_text, "CONTRADICTED", False
                mentions = MENTIONS.get(false_text, [])
            elif injection == "unsupported":
                text, factual, bloom = f"{name} always takes constant time for every operation.", "UNSUPPORTED", False
                mentions = []
            elif injection == "bloom_unsupported":
                text, factual, bloom = f"Analyze and compare {name} against every alternative data structure.", "UNSUPPORTED", True
                mentions = []
            else:
                body = fact_a[0].lower() + fact_a[1:-1]
                text, factual, bloom = f"Evaluate why {body}.", "ENTAILED", True
                mentions = MENTIONS.get(fact_a, [])
            sentences = [
                {"text": fact_a, "factual": "ENTAILED",
                 "cognitive": _cognitive_truth(MENTIONS.get(fact_a, []), False, annotation)},
                {"text": text, "factual": factual,
                 "cognitive": _cognitive_truth(mentions, bloom, annotation), "injected": injection},
                {"text": fact_b, "factual": "ENTAILED",
                 "cognitive": _cognitive_truth(MENTIONS.get(fact_b, []), False, annotation)},
            ]
            cases.append({
                "case_id": f"{target}/{profile}", "target": target, "profile": profile,
                "learner": learner, "sentences": sentences,
                "explanation": " ".join(item["text"] for item in sentences),
            })
    return cases


def _any_reference_violation(sentences: list[dict]) -> bool:
    return any(
        s["factual"] != "ENTAILED" or s["cognitive"] in ("BLOOM_MISMATCH", "UNMASTERED_PREREQUISITE")
        for s in sentences
    )


def _measure(pipeline: C4Pipeline, kg: dict, case: dict, text: str):
    """Measure a text with the full verifier (no rewriting)."""
    measurer = C4Pipeline(kg, replace(pipeline.config, check_factual=True,
                                      check_cognitive=True, rewrite=False))
    path = build_verified_path(case["target"], kg, case["learner"]["learner_id"])
    return measurer.run(path, case["learner"], text).claims


def _has_violation(claims) -> bool:
    return any(
        c.factual_status != "ENTAILED" or c.cognitive_status in ("BLOOM_MISMATCH", "UNMASTERED_PREREQUISITE")
        for c in claims
    )


def evaluate_stress(kg: dict[str, Any]) -> dict[str, Any]:
    cases = build_stress_corpus(kg)
    base = C4Config()
    conditions = {
        "factual_only": replace(base, check_cognitive=False),
        "cognitive_only": replace(base, check_factual=False),
        "full_c4": base,
    }
    pipeline = C4Pipeline(kg, base)

    # Reference label counts and baseline (unverified) rates from the reference labels.
    sentences = [s for case in cases for s in case["sentences"]]
    factual_labels: dict[str, int] = {}
    cognitive_labels: dict[str, int] = {}
    for s in sentences:
        factual_labels[s["factual"]] = factual_labels.get(s["factual"], 0) + 1
        cognitive_labels[s["cognitive"]] = cognitive_labels.get(s["cognitive"], 0) + 1
    total = len(sentences)
    baseline = {
        "claims": total,
        "hallucination_rate": percent(sum(s["factual"] != "ENTAILED" for s in sentences), total),
        "cognitive_mismatch_rate": percent(
            sum(s["cognitive"] in ("BLOOM_MISMATCH", "UNMASTERED_PREREQUISITE") for s in sentences), total),
        "cases_with_violation": sum(_any_reference_violation(c["sentences"]) for c in cases),
    }

    # Verifier detection quality against the reference labels (full C4, initial claims).
    factual_pairs, cog_pairs, bloom_pairs, prereq_pairs = [], [], [], []
    exact_factual = exact_cognitive = 0
    full_runs: dict[str, Any] = {}
    outcomes: dict[str, dict[str, Any]] = {name: {"rates": [], "any": [], "latency": []} for name in conditions}
    rewrite_sent = rewrite_ok = new_violations = 0
    for case in cases:
        path = build_verified_path(case["target"], kg, case["learner"]["learner_id"])
        for name, config in conditions.items():
            result = C4Pipeline(kg, config).run(path, case["learner"], case["explanation"])
            final_claims = _measure(pipeline, kg, case, result.final_explanation)
            outcomes[name]["rates"].append(claim_rates(final_claims))
            outcomes[name]["any"].append(_has_violation(final_claims))
            outcomes[name]["latency"].append(result.latency_s)
            if name == "full_c4":
                full_runs[case["case_id"]] = result.to_dict()
                m = result.metrics
                rewrite_sent += m["claims_sent_for_rewrite"]
                rewrite_ok += m["claims_corrected"]
                new_violations += m["new_violations_introduced"]
                for reference, claim in zip(case["sentences"], result.initial_claims):
                    ref_f = reference["factual"] != "ENTAILED"
                    ref_c = reference["cognitive"] in ("BLOOM_MISMATCH", "UNMASTERED_PREREQUISITE")
                    factual_pairs.append((ref_f, claim.factual_status != "ENTAILED"))
                    cog_pairs.append((ref_c, claim.cognitive_status in ("BLOOM_MISMATCH", "UNMASTERED_PREREQUISITE")))
                    bloom_pairs.append((reference["cognitive"] == "BLOOM_MISMATCH", claim.cognitive_status == "BLOOM_MISMATCH"))
                    prereq_pairs.append((reference["cognitive"] == "UNMASTERED_PREREQUISITE",
                                         claim.cognitive_status == "UNMASTERED_PREREQUISITE"))
                    exact_factual += reference["factual"] == claim.factual_status
                    exact_cognitive += reference["cognitive"] == claim.cognitive_status

    baseline_any = [_any_reference_violation(c["sentences"]) for c in cases]
    summary: dict[str, Any] = {}
    for name, data in outcomes.items():
        claims = sum(r["claims"] for r in data["rates"])
        factual = sum(r["factual_violations"] for r in data["rates"])
        cognitive = sum(r["cognitive_violations"] for r in data["rates"])
        b = sum(x and not y for x, y in zip(baseline_any, data["any"]))
        c = sum((not x) and y for x, y in zip(baseline_any, data["any"]))
        after = sum(data["any"])
        summary[name] = {
            "claims_after": claims,
            "hallucination_rate": percent(factual, claims),
            "cognitive_mismatch_rate": percent(cognitive, claims),
            "cases_with_violation": after,
            "cases_with_violation_ci95": wilson_interval(after, len(cases)),
            "mcnemar_vs_baseline": {"fixed": b, "worsened": c, "p_exact": round(mcnemar_exact(b, c), 8)},
            "mean_latency_ms": round(1000 * statistics.mean(data["latency"]), 3),
        }

    return {
        "corpus_version": CORPUS_VERSION,
        "label_provenance": "constructed by recipe + hand-written mention table; not independently human-annotated; no Cohen's kappa",
        "cases": len(cases),
        "targets": len(kg["concepts"]),
        "profiles": list(PROFILES),
        "claims": total,
        "reference_factual_labels": factual_labels,
        "reference_cognitive_labels": cognitive_labels,
        "baseline_unverified_reference": baseline,
        "baseline_cases_with_violation_ci95": wilson_interval(baseline["cases_with_violation"], len(cases)),
        "detection": {
            "factual": confusion(factual_pairs),
            "cognitive_all": confusion(cog_pairs),
            "bloom_mismatch": confusion(bloom_pairs),
            "unmastered_prerequisite": confusion(prereq_pairs),
            "exact_factual_label_accuracy": percent(exact_factual, total),
            "exact_cognitive_label_accuracy": percent(exact_cognitive, total),
        },
        "rewrite": {
            "claims_sent": rewrite_sent,
            "corrected": rewrite_ok,
            "success_rate": percent(rewrite_ok, rewrite_sent),
            "new_violations_introduced": new_violations,
        },
        "conditions_after_repair": summary,
        "caveat": "Post-repair rates use the same verifier as the repair loop (not independent). "
                  "Detection scores on a recipe-built corpus show the rules behave as specified; they are not generalisation evidence.",
        "sample_reports": {key: full_runs[key] for key in list(full_runs)[:3]},
    }


def evaluate_natural(kg: dict[str, Any], cache_path: Path, generator=None) -> dict[str, Any]:
    """Qwen (or cached) explanations measured by the verifier; exploratory, no reference labels."""
    cache: dict[str, Any] = {}
    if cache_path.exists():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    entries = cache.setdefault("explanations", {})
    pipeline = C4Pipeline(kg)
    rows = []
    failures: list[dict[str, str]] = []
    for target in kg["concepts"]:
        for profile in PROFILES:
            key = f"{target}/{profile}"
            learner, _ = make_learner(kg, target, profile)
            path = build_verified_path(target, kg, learner["learner_id"])
            if key not in entries:
                if generator is None:
                    continue
                try:
                    entries[key] = generator.generate_body(path, learner, kg)
                except RuntimeError as exc:
                    failures.append({"case_id": key, "error": str(exc)})
                    continue
                cache["model"] = generator.model
                cache["options"] = {**GENERATION_OPTIONS, "think": False, "format": "json: {explanation}"}
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps(cache, indent=2) + "\n", encoding="utf-8")
            result = pipeline.run(path, learner, entries[key])
            rows.append({"case_id": key, "text": entries[key], "result": result})
    claims_before = [c for r in rows for c in r["result"].initial_claims]
    claims_after = [c for r in rows for c in r["result"].claims]
    sent = sum(r["result"].metrics["claims_sent_for_rewrite"] for r in rows)
    corrected = sum(r["result"].metrics["claims_corrected"] for r in rows)
    flagged = sum(not all(c.accepted for c in r["result"].initial_claims) for r in rows)
    return {
        "model": cache.get("model"),
        "explanations": len(rows),
        "failed_generations": failures,
        "claims": len(claims_before),
        "before": claim_rates(claims_before),
        "after": claim_rates(claims_after),
        "explanations_with_flagged_claim": flagged,
        "explanations_with_flagged_claim_ci95": wilson_interval(flagged, len(rows)),
        "rewrite_success_rate": percent(corrected, sent),
        "unresolved_explanations": sum(bool(r["result"].unresolved_claims) for r in rows),
        "caveat": "Rates are measured by C4's own verifier on unlabelled model output: they show how much the "
                  "rules flag, not ground-truth accuracy. Independent human labels are still required.",
        "examples": [
            {"case_id": r["case_id"], "original": r["text"], "final": r["result"].final_explanation}
            for r in rows[:4]
        ],
    }


def evaluate_sensitivity(kg: dict[str, Any], cache_path: Path,
                         thresholds=(0.3, 0.4, 0.5, 0.6, 0.7, 0.8)) -> list[dict[str, Any]]:
    """Sweep the entailment-similarity threshold on both corpora (pilot tuning evidence)."""
    entries = {}
    if cache_path.exists():
        entries = json.loads(cache_path.read_text(encoding="utf-8")).get("explanations", {})
    cases = build_stress_corpus(kg)
    rows = []
    for threshold in thresholds:
        pipeline = C4Pipeline(kg, C4Config(entail_similarity=threshold, rewrite=False))
        pairs = []
        for case in cases:
            path = build_verified_path(case["target"], kg, case["learner"]["learner_id"])
            result = pipeline.run(path, case["learner"], case["explanation"])
            for reference, claim in zip(case["sentences"], result.initial_claims):
                pairs.append((reference["factual"] != "ENTAILED", claim.factual_status != "ENTAILED"))
        natural_claims = []
        for key, text in entries.items():
            target, profile = key.split("/")
            learner, _ = make_learner(kg, target, profile)
            path = build_verified_path(target, kg, learner["learner_id"])
            natural_claims += pipeline.run(path, learner, text).initial_claims
        score = confusion(pairs)
        rows.append({
            "entail_similarity": threshold,
            "stress_factual_precision": score["precision"],
            "stress_factual_recall": score["recall"],
            "stress_factual_f1": score["f1"],
            "natural_not_graph_supported_pct": claim_rates(natural_claims)["hallucination_rate"],
        })
    return rows


def evaluate_bloom(items_path: str | Path) -> dict[str, Any]:
    """Score the V1 and V2 Bloom estimators on the labelled item set, split by split.

    ``dev`` informed the V2 lexicon, ``test`` was scored once after it was frozen, and
    ``hard`` (indirect phrasing without cue verbs) was never used for tuning.
    """
    document = json.loads(Path(items_path).read_text(encoding="utf-8"))
    splits: dict[str, Any] = {}
    for split in ("dev", "test", "hard"):
        items = [item for item in document["items"] if item["split"] == split]
        row: dict[str, Any] = {}
        for name, estimator in (("v1", estimate_level), ("v2", estimate_level_v2)):
            scored = score_estimator(items, estimator)
            correct = round(scored["accuracy"] * scored["items"] / 100)
            scored["accuracy_ci95"] = wilson_interval(correct, scored["items"])
            row[name] = scored
        splits[split] = row
    return {
        "version": document["version"],
        "provenance": document["provenance"],
        "split_rule": document["split_rule"],
        "items": len(document["items"]),
        "splits": splits,
        "caveat": ("One annotator (the C4 author) wrote and labelled the items, so there is no inter-annotator "
                   "agreement. The V2 lexicon uses the standard Bloom verb lists and was extended after reading dev "
                   "errors, so its dev score is optimistic; the test items use the same vocabulary family, so its "
                   "test score measures in-vocabulary coverage, not generalisation. The hard split shows the limit of "
                   "any verb-cue matcher. A second annotator and a learned classifier are still required."),
    }


PROGRESSIVE_SEEDS = {"new_concept": None, "level_1": 1, "level_2": 2}


def evaluate_progressive_stress(kg: dict[str, Any]) -> dict[str, Any]:
    """RQ1 on the stress corpus: does level-targeted repair keep faithfulness and hit the target level?

    Each stress case is run with the learner starting a new concept, at demonstrated level 1,
    and at level 2. Three texts are measured by the same progressive verifier without
    rewriting: the original (unverified) explanation, the final text of static C4, and the
    final text of progressive C4. ``question at target level`` is the share of runs whose
    text contains an accepted check question at the learner's target Bloom level.
    """
    cases = build_stress_corpus(kg)
    static = C4Config()
    progressive = C4Config(progressive=True)
    measure = C4Config(progressive=True, rewrite=False)
    texts: dict[str, list[dict[str, Any]]] = {"unverified": [], "static_c4": [], "progressive_c4": []}
    actions: dict[str, int] = {}
    unresolved = 0
    for case in cases:
        path = build_verified_path(case["target"], kg, case["learner"]["learner_id"])
        for seed_name, level in PROGRESSIVE_SEEDS.items():
            learner = dict(case["learner"])
            if level is not None:
                learner["bloom"] = {case["target"]: {"level": level, "attempts": [
                    {"session": 1, "level": level, "score": 0.9, "scaffold": "full"}]}}
            final_static = C4Pipeline(kg, static).run(path, learner, case["explanation"]).final_explanation
            run = C4Pipeline(kg, progressive).run(path, learner, case["explanation"])
            actions[run.progression["action"]] = actions.get(run.progression["action"], 0) + 1
            unresolved += bool(run.unresolved_claims)
            for name, text in (("unverified", case["explanation"]), ("static_c4", final_static),
                               ("progressive_c4", run.final_explanation)):
                measured = C4Pipeline(kg, measure).run(path, learner, text)
                # Static C4 wrote its sentences for the static ceiling, so its faithfulness is
                # measured with the static verifier; the target-level question check is always
                # the progressive one.
                judged = C4Pipeline(kg, replace(static, rewrite=False)).run(path, learner, text) \
                    if name == "static_c4" else measured
                texts[name].append({
                    "stagnating": bool(measured.progression["stagnation_after"]),
                    "violation": _has_violation(judged.claims),
                    "rates": claim_rates(judged.claims),
                })
    runs = len(texts["unverified"])
    table: dict[str, Any] = {}
    for name, rows in texts.items():
        claims = sum(r["rates"]["claims"] for r in rows)
        table[name] = {
            "runs": runs,
            "question_at_target_level_pct": percent(sum(not r["stagnating"] for r in rows), runs),
            "question_at_target_level_ci95": wilson_interval(sum(not r["stagnating"] for r in rows), runs),
            "runs_with_violation": sum(r["violation"] for r in rows),
            "hallucination_rate": percent(sum(r["rates"]["factual_violations"] for r in rows), claims),
            "cognitive_mismatch_rate": percent(sum(r["rates"]["cognitive_violations"] for r in rows), claims),
        }
    return {
        "cases": len(cases), "runs": runs, "learner_starts": list(PROGRESSIVE_SEEDS),
        "policy_actions": actions, "runs_with_unresolved_claims": unresolved, "conditions": table,
        "caveat": ("Measured by the same progressive verifier that performs the repair, so these rates show the "
                   "repair does what it is specified to do, not independent accuracy. Neither the unverified text "
                   "nor static C4 ever contains a check question, so the target-level gap is expected by construction."),
    }
