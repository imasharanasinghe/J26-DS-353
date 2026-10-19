"""Metric definitions frozen in docs/GUIDELINES.md, computed from verifier output."""

from __future__ import annotations

import math
from typing import Any, Iterable, Sequence

FACTUAL_BAD = ("UNSUPPORTED", "CONTRADICTED")
COGNITIVE_BAD = ("BLOOM_MISMATCH", "UNMASTERED_PREREQUISITE")


def percent(numerator: float, denominator: float) -> float | None:
    return round(100.0 * numerator / denominator, 2) if denominator else None


def claim_rates(claims: Sequence[Any]) -> dict[str, Any]:
    """Hallucination and cognitive-mismatch rates over VerifiedClaim objects.

    Sentences C4 wrote itself from learner, path, or graph data are not model claims, so
    they are excluded from the denominators; counting them would dilute the rates.
    """
    claims = [c for c in claims if getattr(c.claim, "source", "domain") in ("domain", "task")]
    # A question asserts no domain fact, so it joins only the cognitive denominator.
    domain = [c for c in claims if getattr(c.claim, "source", "domain") == "domain"]
    total = len(domain)
    factual = sum(c.factual_status in FACTUAL_BAD for c in domain)
    cognitive = sum(c.cognitive_status in COGNITIVE_BAD for c in claims)
    inconclusive = sum(c.cognitive_status == "INCONCLUSIVE" for c in claims)
    return {
        "claims": total,
        "factual_violations": factual,
        "cognitive_violations": cognitive,
        "inconclusive": inconclusive,
        "hallucination_rate": percent(factual, total),
        "cognitive_mismatch_rate": percent(cognitive, len(claims)),
    }


def summarize(result: Any) -> dict[str, Any]:
    """Per-run metrics: before/after rates, rewrite success, new violations, confidence."""
    sent = [c for c in result.initial_claims if not c.accepted]
    final_by_id = {c.claim.claim_id: c for c in result.claims}
    # A sentence removed by the rewrite loop no longer violates anything.
    def final_ok(claim_id: str) -> bool:
        return claim_id not in final_by_id or final_by_id[claim_id].accepted

    corrected = sum(1 for c in sent if final_ok(c.claim.claim_id))
    new_violations = sum(
        1 for c in result.initial_claims
        if c.accepted and not final_ok(c.claim.claim_id)
    )
    confidence: dict[str, int] = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for claim in result.claims:
        confidence[claim.confidence] += 1
    return {
        "before": claim_rates(result.initial_claims),
        "after": claim_rates(result.claims),
        "claims_sent_for_rewrite": len(sent),
        "claims_corrected": corrected,
        "rewrite_success_rate": percent(corrected, len(sent)),
        "new_violations_introduced": new_violations,
        "unresolved": len(result.unresolved_claims),
        "stagnation_before": (result.progression or {}).get("stagnation_before"),
        "stagnation_after": (result.progression or {}).get("stagnation_after"),
        "final_confidence": confidence,
        "llm_calls_in_verifier": 0,
    }


def precision_recall_f1(tp: int, fp: int, fn: int) -> dict[str, float | None]:
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    if precision is None or recall is None or precision + recall == 0:
        f1 = None
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {
        "tp": tp, "fp": fp, "fn": fn,
        "precision": None if precision is None else round(precision, 4),
        "recall": None if recall is None else round(recall, 4),
        "f1": None if f1 is None else round(f1, 4),
    }


def confusion(pairs: Iterable[tuple[bool, bool]]) -> dict[str, float | None]:
    """``pairs`` are (reference_is_violation, predicted_is_violation)."""
    tp = fp = fn = 0
    for reference, predicted in pairs:
        tp += reference and predicted
        fp += (not reference) and predicted
        fn += reference and (not predicted)
    return precision_recall_f1(tp, fp, fn)


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value for discordant counts b and c."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float] | None:
    if total == 0:
        return None
    p = successes / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return round(100 * max(0.0, centre - margin), 1), round(100 * min(1.0, centre + margin), 1)


def _normal_cdf(value: float) -> float:
    return 0.5 * (1 + math.erf(value / math.sqrt(2)))


def bootstrap_mean_ci(
    values: Sequence[float], seed: int = 0, resamples: int = 2000, level: float = 0.95
) -> tuple[float, float] | None:
    """Percentile bootstrap interval for the mean (seeded, so results are reproducible)."""
    import random

    if not values:
        return None
    rng = random.Random(seed)
    n = len(values)
    means = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(resamples))
    low = means[int(((1 - level) / 2) * resamples)]
    high = means[min(resamples - 1, int((1 - (1 - level) / 2) * resamples))]
    return round(low, 4), round(high, 4)


def wilcoxon_signed_rank(differences: Sequence[float]) -> dict[str, float | int | None]:
    """Paired Wilcoxon signed-rank test, normal approximation with tie and continuity correction.

    Zero differences are dropped. Returns ``None`` statistics when fewer than 6 non-zero pairs remain.
    """
    nonzero = [d for d in differences if d != 0]
    n = len(nonzero)
    if n < 6:
        return {"n": n, "w_plus": None, "z": None, "p": None}
    order = sorted(range(n), key=lambda i: abs(nonzero[i]))
    ranks = [0.0] * n
    tie_term = 0.0
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs(nonzero[order[j + 1]]) == abs(nonzero[order[i]]):
            j += 1
        average = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = average
        size = j - i + 1
        tie_term += size ** 3 - size
        i = j + 1
    w_plus = sum(rank for rank, d in zip(ranks, nonzero) if d > 0)
    mean = n * (n + 1) / 4
    variance = n * (n + 1) * (2 * n + 1) / 24 - tie_term / 48
    if variance <= 0:
        return {"n": n, "w_plus": w_plus, "z": None, "p": None}
    shift = w_plus - mean
    shift -= 0.5 if shift > 0 else -0.5 if shift < 0 else 0
    z = shift / math.sqrt(variance)
    return {"n": n, "w_plus": round(w_plus, 1), "z": round(z, 3), "p": float(f"{2 * (1 - _normal_cdf(abs(z))):.4g}")}


def cohens_dz(differences: Sequence[float]) -> float | None:
    """Effect size for paired data: mean difference over the standard deviation of the differences."""
    n = len(differences)
    if n < 2:
        return None
    mean = sum(differences) / n
    variance = sum((d - mean) ** 2 for d in differences) / (n - 1)
    return round(mean / math.sqrt(variance), 3) if variance > 0 else None
