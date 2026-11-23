"""Planted-error test for the Graph Auditor (Phase 3, no real students needed).

1. Take a graph and treat it as the *truth*.
2. Simulate a cohort whose mastery really depends on the truth graph (guess, slip, an ability
   trait, a small share of students who skip a prerequisite).
3. Corrupt a share of the edges (delete, reverse, add spurious) to get the graph the auditor sees.
4. Audit the corrupted graph against the cohort and score how well the planted errors are found,
   across cohort sizes, against two simple baselines.

This is a simulation: the cohort generator encodes the dependency assumption the auditor tests, so
the numbers measure the method, not real classes. The real-data run needs ASSISTments or SLIIT
performance data (the loader ``observations_from_rows`` is ready for it).
"""

from __future__ import annotations

import math
import random
import statistics
from typing import Any, Iterable, Sequence

from . import auditor
from .auditor import Edge, Observations
from .metrics import precision_recall_f1


def graph_edges(kg: dict[str, Any]) -> list[Edge]:
    concepts = kg["concepts"]
    return [(p, c) for c, v in concepts.items() for p in v.get("prerequisites", []) if p in concepts]


def topological_order(ids: Sequence[str], edges: Iterable[Edge]) -> list[str]:
    edges = list(edges)
    parents = {c: [a for a, b in edges if b == c] for c in ids}
    order: list[str] = []
    seen: set[str] = set()

    def visit(node: str) -> None:
        if node in seen:
            return
        seen.add(node)
        for parent in parents[node]:
            visit(parent)
        order.append(node)

    for node in ids:
        visit(node)
    return order


def simulate_cohort(
    kg: dict[str, Any], students: int, seed: int = 0, items_per_concept: int = 6,
    guess: float = 0.2, slip: float = 0.1, skip: float = 0.03, pass_mark: float = 0.6,
) -> Observations:
    """Students master concepts only after their prerequisites (except a ``skip`` share)."""
    rng = random.Random(f"cohort:{seed}")
    concepts = kg["concepts"]
    edges = graph_edges(kg)
    order = topological_order(list(concepts), edges)
    parents = {c: [a for a, b in edges if b == c] for c in concepts}
    mastered = {c: [] for c in concepts}
    week = {c: [] for c in concepts}
    depth: dict[str, int] = {}
    for c in order:
        depth[c] = 1 + max((depth[p] for p in parents[c]), default=0)
    for _ in range(students):
        theta = rng.gauss(0, 1)
        true: dict[str, bool] = {}
        taught: dict[str, float] = {}
        for c in order:
            hard = (concepts[c].get("difficulty", 3) - 3) * 0.5
            ready = all(true[p] for p in parents[c]) or rng.random() < skip
            learns = rng.random() < 1 / (1 + math.exp(-(1.6 * theta - hard + 0.6)))
            true[c] = bool(ready and learns)
            taught[c] = max([taught[p] for p in parents[c]], default=0) + depth[c] + rng.expovariate(1.0)
            correct = sum(rng.random() < (1 - slip if true[c] else guess) for _ in range(items_per_concept))
            observed = correct / items_per_concept >= pass_mark
            mastered[c].append(int(observed))
            week[c].append(int(taught[c]) if observed else None)
    return Observations(mastered, week)


def corrupt(edges: Sequence[Edge], ids: Sequence[str], fraction: float, seed: int = 0) -> dict[str, Any]:
    """Delete, reverse and add (spurious) edges, ``fraction`` of the edge count in each way.

    Spurious edges join concepts with no existing path between them in either direction, so every
    planted error is a clean, unambiguous mistake."""
    rng = random.Random(f"corrupt:{seed}")
    edges = list(edges)
    k = max(1, round(fraction * len(edges)))
    shuffled = edges[:]
    rng.shuffle(shuffled)
    deleted, reversed_ = shuffled[:k], shuffled[k:2 * k]
    kept = [e for e in edges if e not in deleted and e not in reversed_]
    swapped = [(b, a) for a, b in reversed_]
    current = kept + swapped
    reach = auditor._reachable(edges)
    spurious: list[Edge] = []
    pool = [(a, b) for a in ids for b in ids if a != b and b not in reach.get(a, ()) and a not in reach.get(b, ())]
    rng.shuffle(pool)
    for pair in pool:
        if len(spurious) >= k:
            break
        if (pair[1], pair[0]) in spurious or pair in current:
            continue
        spurious.append(pair)
    return {"edges": current + spurious, "deleted": deleted, "reversed": swapped,
            "spurious": spurious, "clean": kept}


def planted_error_run(kg: dict[str, Any], students: int, seed: int, fraction: float = 0.15,
                      cfg: auditor.AuditConfig | None = None) -> dict[str, Any]:
    cfg = cfg or auditor.AuditConfig(seed=seed)
    truth = graph_edges(kg)
    obs = simulate_cohort(kg, students, seed)
    bad = corrupt(truth, list(kg["concepts"]), fraction, seed)
    report = auditor.audit_graph(bad["edges"], obs, cfg)
    status = {tuple(row["edge"]): row["status"] for row in report["edges"]}
    wrong = set(map(tuple, bad["reversed"])) | set(map(tuple, bad["spurious"]))
    seen = [e for e in bad["edges"] if e in status]

    def score(flag: set[Edge]) -> dict[str, Any]:
        tp = sum(e in wrong for e in seen if e in flag)
        fp = sum(e not in wrong for e in seen if e in flag)
        fn = sum(e in wrong for e in seen if e not in flag)
        return precision_recall_f1(tp, fp, fn)

    strict = {e for e in seen if status[e] in (auditor.REVERSED, auditor.UNSUPPORTED)}
    lenient = strict | {e for e in seen if status[e] == auditor.CONTESTED}
    cands = {tuple(row["edge"]) for row in report["missing_candidates"]}
    deleted = set(map(tuple, bad["deleted"]))
    # Baselines: unadjusted co-occurrence (flag edges with a low raw odds ratio) and order only
    # (flag edges where A is usually observed after B).
    cooc = {e for e in seen if (auditor.raw_odds_ratio(obs, *e) or 0) < 4.0}
    ordered = set()
    for e in seen:
        share = auditor.order_share(obs, *e)
        if share and share[0] < 0.6:
            ordered.add(e)
    k = len(deleted)
    by_raw = sorted(((a, b) for a in obs.concepts for b in obs.concepts if a != b and (a, b) not in bad["edges"]),
                    key=lambda p: -(auditor.raw_odds_ratio(obs, *p) or 0))[:k]
    tp_c = len(cands & deleted)
    return {
        "students": students, "seed": seed,
        "planted": {"deleted": len(deleted), "reversed": len(bad["reversed"]), "spurious": len(bad["spurious"])},
        "bad_edge_detection_strict": score(strict),
        "bad_edge_detection_incl_contested": score(lenient),
        "baseline_cooccurrence": score(cooc),
        "baseline_order_only": score(ordered),
        "reversed_found": sum(status.get(e) == auditor.REVERSED for e in map(tuple, bad["reversed"])),
        "spurious_found": sum(status.get(e) in (auditor.UNSUPPORTED, auditor.REVERSED) for e in map(tuple, bad["spurious"])),
        "clean_flagged": sum(e in strict for e in bad["clean"]),
        "missing_recovery": {**precision_recall_f1(tp_c, len(cands - deleted), len(deleted - cands)),
                              "candidates": len(cands), "deleted": len(deleted)},
        "missing_baseline_top_k_raw_or": {"recall": round(len(set(by_raw) & deleted) / k, 4) if k else None},
        "contested_clean_share": round(sum(status[e] == auditor.CONTESTED for e in bad["clean"] if e in status)
                                       / max(1, len([e for e in bad["clean"] if e in status])), 4),
    }


def _mean(rows: Sequence[dict[str, Any]], *path: str) -> dict[str, float | None]:
    values = []
    for row in rows:
        node: Any = row
        for key in path:
            node = node[key]
        if node is not None:
            values.append(node)
    return {"mean": round(statistics.fmean(values), 4) if values else None,
            "sd": round(statistics.pstdev(values), 4) if len(values) > 1 else 0.0}


def sweep(kg: dict[str, Any], sizes: Sequence[int] = (60, 120, 300, 600), seeds: int = 5,
          fraction: float = 0.15) -> dict[str, Any]:
    table = []
    for n in sizes:
        runs = [planted_error_run(kg, n, seed, fraction) for seed in range(seeds)]
        table.append({
            "students": n, "runs": seeds,
            "ours_strict_f1": _mean(runs, "bad_edge_detection_strict", "f1"),
            "ours_strict_recall": _mean(runs, "bad_edge_detection_strict", "recall"),
            "ours_strict_precision": _mean(runs, "bad_edge_detection_strict", "precision"),
            "ours_incl_contested_f1": _mean(runs, "bad_edge_detection_incl_contested", "f1"),
            "baseline_cooccurrence_f1": _mean(runs, "baseline_cooccurrence", "f1"),
            "baseline_order_f1": _mean(runs, "baseline_order_only", "f1"),
            "missing_recall": _mean(runs, "missing_recovery", "recall"),
            "missing_precision": _mean(runs, "missing_recovery", "precision"),
            "missing_baseline_recall": _mean(runs, "missing_baseline_top_k_raw_or", "recall"),
            "clean_edges_flagged": _mean(runs, "clean_flagged"),
            "clean_edges_contested_share": _mean(runs, "contested_clean_share"),
        })
    return {"fraction_corrupted_per_type": fraction, "concepts": len(kg["concepts"]),
            "true_edges": len(graph_edges(kg)), "rows": table,
            "note": "simulation: the cohort generator encodes the dependency the auditor tests; real data is needed for real claims"}


def observations_from_rows(rows: Iterable[dict[str, Any]], pass_mark: float = 0.6, min_attempts: int = 3) -> Observations:
    """Build Observations from ``{"student", "concept", "correct": 0/1, "order": int}`` attempt rows
    (the shape of ASSISTments-style logs). A student counts as mastering a concept when at least
    ``min_attempts`` attempts reach ``pass_mark``; concepts without enough attempts are missing for
    that student and treated as not mastered, which biases toward Contested, not toward Supported."""
    scores: dict[tuple[str, str], list[int]] = {}
    first: dict[tuple[str, str], int] = {}
    for row in rows:
        key = (row["student"], row["concept"])
        scores.setdefault(key, []).append(int(row["correct"]))
        first.setdefault(key, int(row.get("order", len(first))))
    students = sorted({s for s, _ in scores})
    concepts = sorted({c for _, c in scores})
    mastered = {c: [] for c in concepts}
    week: dict[str, list[int | None]] = {c: [] for c in concepts}
    for s in students:
        for c in concepts:
            attempts = scores.get((s, c), [])
            ok = len(attempts) >= min_attempts and sum(attempts) / len(attempts) >= pass_mark
            mastered[c].append(int(ok))
            week[c].append(first.get((s, c)) if ok else None)
    return Observations(mastered, week)
