"""E3: does feeding the audit into the verifier cut wrong "review first" detours and missed prerequisites?

Simulation on a corrupted graph (see ``c4.audit_sim``). For every (student, target) pair the
review-first list is the set of unmastered direct prerequisites. Three conditions:

* ``no_audit``        the corrupted graph is used as it is
* ``audit``           edges the audit calls Unsupported or Reversed are not used (what the verifier does
                      when given ``edge_confidence``); Contested edges still send the student to review
* ``audit_approved``  as above, plus the lecturer approves the audit's proposals that are correct
                      (flip a Reversed edge, add a Missing candidate). The lecturer is an oracle here,
                      so this is an upper bound, and it is labelled that way in the results.

Wrong detour: a concept listed for review that is not a true prerequisite of the target.
Missed prerequisite: an unmastered true prerequisite that is not listed.
"""

from __future__ import annotations

import statistics
from typing import Any, Sequence

from . import audit_sim, auditor
from .auditor import Edge, Observations


def _review_sets(edges: Sequence[Edge], obs: Observations) -> dict[tuple[int, str], set[str]]:
    parents: dict[str, list[str]] = {}
    for a, b in edges:
        parents.setdefault(b, []).append(a)
    out: dict[tuple[int, str], set[str]] = {}
    for target, prereqs in parents.items():
        if target not in obs.mastered:
            continue
        for s in range(obs.students):
            out[(s, target)] = {p for p in prereqs if p in obs.mastered and not obs.mastered[p][s]}
    return out


def _errors(truth: dict, listed: dict, targets: set[str]) -> dict[str, float]:
    wrong = missed = true_items = pairs = 0
    for (s, t), real in truth.items():
        if t not in targets:
            continue
        got = listed.get((s, t), set())
        wrong += len(got - real)
        missed += len(real - got)
        true_items += len(real)
        pairs += 1
    return {"wrong_detours_per_pair": wrong / pairs if pairs else 0.0,
            "missed_prereqs_per_pair": missed / pairs if pairs else 0.0,
            "missed_share_of_true": missed / true_items if true_items else 0.0}


def study_once(kg: dict[str, Any], students: int, seed: int, fraction: float = 0.15) -> dict[str, Any]:
    truth_edges = audit_sim.graph_edges(kg)
    obs = audit_sim.simulate_cohort(kg, students, seed)
    bad = audit_sim.corrupt(truth_edges, list(kg["concepts"]), fraction, seed)
    report = auditor.audit_graph(bad["edges"], obs, auditor.AuditConfig(seed=seed))
    status = {tuple(r["edge"]): r["status"] for r in report["edges"]}
    truth_set = set(truth_edges)

    kept = [e for e in bad["edges"] if status.get(e) not in (auditor.UNSUPPORTED, auditor.REVERSED)]
    approved = list(kept)
    for e in bad["edges"]:
        if status.get(e) == auditor.REVERSED and (e[1], e[0]) in truth_set:
            approved.append((e[1], e[0]))
    for row in report["missing_candidates"]:
        if tuple(row["edge"]) in truth_set:
            approved.append(tuple(row["edge"]))

    real = _review_sets(truth_edges, obs)
    # Score only targets that have prerequisites in the truth graph or in the graph being tested.
    targets = {b for _, b in truth_edges} | {b for _, b in bad["edges"]}
    conditions = {
        "no_audit": bad["edges"], "audit": kept, "audit_approved": approved,
    }
    # Truth review sets must exist for every scored target, even those with no true prerequisite.
    truth_sets = {(s, t): real.get((s, t), set()) for t in targets for s in range(obs.students)}
    result = {}
    for name, edges in conditions.items():
        listed = _review_sets(edges, obs)
        result[name] = _errors(truth_sets, listed, targets)
    return result


def study(kg: dict[str, Any], sizes: Sequence[int] = (120, 300, 600), seeds: int = 5,
          fraction: float = 0.15) -> dict[str, Any]:
    rows = []
    for n in sizes:
        runs = [study_once(kg, n, seed, fraction) for seed in range(seeds)]
        row: dict[str, Any] = {"students": n, "runs": seeds}
        for name in ("no_audit", "audit", "audit_approved"):
            row[name] = {metric: round(statistics.fmean(r[name][metric] for r in runs), 4)
                         for metric in runs[0][name]}
        rows.append(row)
    return {"fraction_corrupted_per_type": fraction, "rows": rows,
            "note": ("simulation; 'audit_approved' assumes the lecturer approves only correct proposals "
                     "(upper bound); detours and misses are per (student, target) pair")}
