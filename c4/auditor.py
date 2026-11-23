"""Graph Auditor: check the graph's pedagogy edges against what students actually do.

The auditor reads the graph (C1) and student evidence (C2 mastery, quizzes, exam data) and writes a
report for the lecturer. **It proposes; it never edits the graph.** Statuses are evidence, not proof:
students meet prerequisites first because the course is taught in that order, so order and
implication can look like dependence when they are only the timetable.

Edge audit, for each "A is a prerequisite of B":

* implication  mastering B without A should be rare. ``v_fwd = P(not A | B)`` with a Wilson interval.
* lift         success on B is more likely when A is mastered, *after controlling for overall
               ability* (Mantel-Haenszel odds ratio over ability strata, bootstrap interval). Without
               this control any two concepts correlate because strong students master everything.
* order        among students who mastered both, A before or with B (reported, not decisive).

Statuses: Supported, Contested, Reversed, Unsupported, plus Missing (candidate) for unlinked pairs
with a strong one-way dependency that no existing path already implies.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from .metrics import wilson_interval

SUPPORTED, CONTESTED, REVERSED, UNSUPPORTED, MISSING = (
    "Supported", "Contested", "Reversed", "Unsupported", "Missing")
Edge = tuple[str, str]  # (prerequisite, concept)


@dataclass(frozen=True)
class AuditConfig:
    epsilon: float = 0.15          # "rare": allowed rate of mastering B without A (guess and slip)
    support_cap: float = 0.30      # Supported needs the upper end of v_fwd at or below this
    min_students: int = 40         # fewer students with data: Contested ("insufficient data")
    base_rate_floor: float = 0.05  # A (or B) mastered by <5% or >95%: edge cannot be tested
    strata: int = 3                # ability strata for the lift test
    bootstrap: int = 100
    support_or_lower: float = 2.0  # Supported needs the lift interval's lower end at or above this
    missing_or_lower: float = 2.0  # candidate needs lift interval's lower end at or above this
    seed: int = 0


@dataclass
class Observations:
    """Observed mastery (0/1) per concept per student; optional week each was first observed."""

    mastered: dict[str, list[int]]
    week: dict[str, list[int | None]] = field(default_factory=dict)

    @property
    def students(self) -> int:
        return len(next(iter(self.mastered.values()))) if self.mastered else 0

    @property
    def concepts(self) -> list[str]:
        return list(self.mastered)


# ------------------------------------------------------------------ statistics


def _table(a: Sequence[int], b: Sequence[int], rows: Iterable[int]) -> tuple[int, int, int, int]:
    n11 = n10 = n01 = n00 = 0
    for i in rows:
        if a[i]:
            if b[i]:
                n11 += 1
            else:
                n10 += 1
        elif b[i]:
            n01 += 1
        else:
            n00 += 1
    return n11, n10, n01, n00


def mantel_haenszel(tables: Sequence[tuple[int, int, int, int]]) -> float | None:
    """Common odds ratio over strata; a 0.5 continuity correction only when a cell sum is zero."""
    num = den = 0.0
    for n11, n10, n01, n00 in tables:
        n = n11 + n10 + n01 + n00
        if n:
            num += n11 * n00 / n
            den += n10 * n01 / n
    if num == 0 or den == 0:
        num, den = 0.5 + num, 0.5 + den
    return num / den if den else None


def ability_strata(obs: Observations, a: str, b: str, strata: int) -> list[list[int]]:
    """Rank students by rest-score (mastery over the other concepts) and cut into equal groups."""
    others = [c for c in obs.concepts if c not in (a, b)]
    scores = [sum(obs.mastered[c][i] for c in others) for i in range(obs.students)]
    order = sorted(range(obs.students), key=lambda i: scores[i])
    size = max(1, math.ceil(len(order) / strata))
    return [order[k:k + size] for k in range(0, len(order), size)]


def adjusted_odds_ratio(obs: Observations, a: str, b: str, cfg: AuditConfig,
                        bootstrap: bool = True) -> tuple[float | None, tuple[float, float] | None]:
    groups = ability_strata(obs, a, b, cfg.strata)

    def estimate(index_groups: list[list[int]]) -> float | None:
        return mantel_haenszel([_table(obs.mastered[a], obs.mastered[b], g) for g in index_groups])

    point = estimate(groups)
    if point is None or not bootstrap:
        return point, None
    rng = random.Random(f"{cfg.seed}:{a}:{b}")
    draws = []
    n = obs.students
    for _ in range(cfg.bootstrap):
        picks = [rng.randrange(n) for _ in range(n)]
        bag = [[] for _ in groups]
        slot = {i: k for k, g in enumerate(groups) for i in g}
        for i in picks:
            bag[slot[i]].append(i)
        value = estimate(bag)
        if value is not None:
            draws.append(value)
    if len(draws) < 10:
        return point, None
    draws.sort()
    return point, (draws[int(0.025 * len(draws))], draws[min(len(draws) - 1, int(0.975 * len(draws)))])


def raw_odds_ratio(obs: Observations, a: str, b: str) -> float | None:
    """Unadjusted odds ratio (the co-occurrence baseline; confounded by overall ability)."""
    return mantel_haenszel([_table(obs.mastered[a], obs.mastered[b], range(obs.students))])


def order_share(obs: Observations, a: str, b: str) -> tuple[float, int] | None:
    """Among students who mastered both: share where A was observed no later than B."""
    if a not in obs.week or b not in obs.week:
        return None
    pairs = [(x, y) for x, y in zip(obs.week[a], obs.week[b]) if x is not None and y is not None]
    if not pairs:
        return None
    return sum(x <= y for x, y in pairs) / len(pairs), len(pairs)


# ------------------------------------------------------------------- the audit


@dataclass
class EdgeAudit:
    edge: Edge
    status: str
    reason: str
    n: int
    v_fwd: float | None
    v_fwd_ci: tuple[float, float] | None
    v_rev: float | None
    odds_ratio: float | None
    odds_ratio_ci: tuple[float, float] | None
    order_share: float | None = None

    def to_dict(self) -> dict[str, Any]:
        def r(value: Any) -> Any:
            if isinstance(value, tuple):
                return [round(x, 3) for x in value]
            return round(value, 3) if isinstance(value, float) else value
        return {"edge": list(self.edge), "status": self.status, "reason": self.reason, "n": self.n,
                "implication_violation": r(self.v_fwd), "implication_violation_ci": r(self.v_fwd_ci),
                "reverse_violation": r(self.v_rev), "odds_ratio": r(self.odds_ratio),
                "odds_ratio_ci": r(self.odds_ratio_ci), "order_share": r(self.order_share)}


def _rate(num: int, den: int) -> tuple[float | None, tuple[float, float] | None]:
    if den == 0:
        return None, None
    interval = wilson_interval(num, den)  # c4.metrics reports percent
    return num / den, ((interval[0] / 100, interval[1] / 100) if interval else None)


def audit_edge(obs: Observations, edge: Edge, cfg: AuditConfig) -> EdgeAudit:
    a, b = edge
    n11, n10, n01, n00 = _table(obs.mastered[a], obs.mastered[b], range(obs.students))
    n = obs.students
    v_fwd, v_fwd_ci = _rate(n01, n01 + n11)       # P(not A | B)
    v_rev, v_rev_ci = _rate(n10, n10 + n11)       # P(not B | A)
    order = order_share(obs, a, b)
    share = order[0] if order else None

    def done(status: str, reason: str, odds: Any = (None, None)) -> EdgeAudit:
        return EdgeAudit(edge, status, reason, n, v_fwd, v_fwd_ci, v_rev, odds[0], odds[1], share)

    if n < cfg.min_students:
        return done(CONTESTED, f"insufficient data (n={n} < {cfg.min_students})")
    rate_a, rate_b = (n11 + n10) / n, (n11 + n01) / n
    for name, rate in ((a, rate_a), (b, rate_b)):
        if not cfg.base_rate_floor <= rate <= 1 - cfg.base_rate_floor:
            return done(CONTESTED, f"{name} is mastered by {rate:.0%} of students, so the edge cannot be tested")
    odds = adjusted_odds_ratio(obs, a, b, cfg)
    lo_or = odds[1][0] if odds[1] else None
    if (v_rev is not None and v_rev <= cfg.epsilon and v_fwd_ci and v_fwd_ci[0] > cfg.epsilon
            and lo_or is not None and lo_or > 1):
        return done(REVERSED, "mastering A without B is rare but mastering B without A is common: "
                              "the dependency runs the other way", odds)
    if v_fwd_ci and v_fwd_ci[1] <= cfg.support_cap and lo_or is not None and lo_or >= cfg.support_or_lower:
        return done(SUPPORTED, "B is rarely mastered without A, and A predicts B beyond overall ability", odds)
    if v_fwd_ci and v_fwd_ci[0] > cfg.epsilon and (lo_or is None or lo_or <= 1):
        return done(UNSUPPORTED, "no dependence beyond overall ability, and B is often mastered without A", odds)
    if v_fwd_ci and v_fwd_ci[0] > cfg.support_cap:
        return done(UNSUPPORTED, "B is clearly often mastered without A, so A is not needed for B "
                                 "(any association comes from shared prerequisites)", odds)
    return done(CONTESTED, "evidence is mixed or the intervals are wide", odds)


def _reachable(edges: Iterable[Edge]) -> dict[str, set[str]]:
    children: dict[str, set[str]] = {}
    for a, b in edges:
        children.setdefault(a, set()).add(b)
    reach: dict[str, set[str]] = {}

    def walk(node: str) -> set[str]:
        if node in reach:
            return reach[node]
        reach[node] = set()
        for child in children.get(node, ()):
            reach[node] |= {child} | walk(child)
        return reach[node]

    for node in list(children):
        walk(node)
    return reach


def candidate_edges(obs: Observations, existing: Iterable[Edge], cfg: AuditConfig) -> list[EdgeAudit]:
    """Unlinked pairs with a strong one-way dependency that no existing path already implies."""
    existing = list(existing)
    reach = _reachable(existing)
    found: list[EdgeAudit] = []
    ids = obs.concepts
    n = obs.students
    if n < cfg.min_students:
        return found
    for a in ids:
        for b in ids:
            if a == b or (a, b) in existing or b in reach.get(a, ()) or a in reach.get(b, ()):
                continue
            n11, n10, n01, n00 = _table(obs.mastered[a], obs.mastered[b], range(n))
            if not (cfg.base_rate_floor <= (n11 + n10) / n <= 1 - cfg.base_rate_floor
                    and cfg.base_rate_floor <= (n11 + n01) / n <= 1 - cfg.base_rate_floor):
                continue
            v_fwd, v_fwd_ci = _rate(n01, n01 + n11)
            v_rev, _ = _rate(n10, n10 + n11)
            if v_fwd is None or v_rev is None or not v_fwd_ci or v_fwd_ci[1] > cfg.support_cap or v_fwd >= v_rev:
                continue
            odds = adjusted_odds_ratio(obs, a, b, cfg)
            if odds[1] and odds[1][0] >= cfg.missing_or_lower:
                order = order_share(obs, a, b)
                found.append(EdgeAudit((a, b), MISSING, "strong one-way dependency with no existing path",
                                       n, v_fwd, v_fwd_ci, v_rev, odds[0], odds[1], order[0] if order else None))
    found.sort(key=lambda row: -(row.odds_ratio_ci[0] if row.odds_ratio_ci else 0))
    return found


def audit_graph(kg_edges: Sequence[Edge], obs: Observations, cfg: AuditConfig | None = None) -> dict[str, Any]:
    cfg = cfg or AuditConfig()
    known = set(obs.concepts)
    usable = [edge for edge in kg_edges if edge[0] in known and edge[1] in known]
    edges = [audit_edge(obs, edge, cfg) for edge in usable]
    candidates = candidate_edges(obs, usable, cfg)
    counts: dict[str, int] = {}
    for row in edges + candidates:
        counts[row.status] = counts.get(row.status, 0) + 1
    return {
        "schema": "c4-audit/1.0", "students": obs.students, "config": cfg.__dict__,
        "edges": [row.to_dict() for row in edges],
        "missing_candidates": [row.to_dict() for row in candidates],
        "counts": counts,
        "edge_confidence": edge_confidence(edges),
        "proposals": proposals(edges, candidates),
        "caveat": "Statuses are evidence, not proof: curriculum order confounds order and implication tests.",
    }


def edge_confidence(edges: Iterable[EdgeAudit]) -> dict[str, dict[str, Any]]:
    """The block the verifier reads: ``{"a->b": {"status": ..., "n": ...}}``."""
    return {f"{row.edge[0]}->{row.edge[1]}": {"status": row.status, "n": row.n} for row in edges}


def proposals(edges: Iterable[EdgeAudit], candidates: Iterable[EdgeAudit]) -> list[dict[str, Any]]:
    """Proposals to C1; every one needs a lecturer."""
    out = []
    for row in edges:
        action = {SUPPORTED: None, CONTESTED: "keep, lower confidence", REVERSED: "review direction (possible reversal)",
                  UNSUPPORTED: "review for removal"}[row.status]
        if action:
            out.append({"edge": list(row.edge), "status": row.status, "evidence": row.reason,
                        "proposal": action, "needs_lecturer": True})
    for row in candidates:
        out.append({"edge": list(row.edge), "status": MISSING, "evidence": row.reason,
                    "proposal": "consider adding", "needs_lecturer": True})
    return out


# ------------------------------------------------- other pedagogy edge types


def bloom_audit(items: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Do higher Bloom labels behave harder?

    ``items``: ``{"id", "bloom", "correct": [0/1 per student]}``. Reports the rank correlation of
    label and empirical difficulty and flags items whose difficulty disagrees with their label.
    A disagreement is a finding about the *label*: Bloom is not a strict ladder in the research.
    """
    rows = [{"id": item["id"], "bloom": item["bloom"],
             "difficulty": 1 - sum(item["correct"]) / len(item["correct"])} for item in items if item["correct"]]
    if len(rows) < 4:
        return {"items": len(rows), "note": "too few items"}
    rho = spearman([row["bloom"] for row in rows], [row["difficulty"] for row in rows])
    by_level: dict[int, list[float]] = {}
    for row in rows:
        by_level.setdefault(row["bloom"], []).append(row["difficulty"])
    means = {level: sum(v) / len(v) for level, v in by_level.items()}
    spread = _sd([row["difficulty"] for row in rows]) or 1.0
    flagged = []
    for row in rows:
        lower = [m for level, m in means.items() if level < row["bloom"]]
        higher = [m for level, m in means.items() if level > row["bloom"]]
        if (lower and row["difficulty"] < max(lower) - spread) or (higher and row["difficulty"] > min(higher) + spread):
            flagged.append(row["id"])
    return {"items": len(rows), "spearman_label_vs_difficulty": round(rho, 3) if rho is not None else None,
            "mean_difficulty_by_level": {str(k): round(v, 3) for k, v in sorted(means.items())},
            "flagged_items": flagged, "finding": "label disagrees with data" if flagged else "labels consistent"}


def load_audit(depths: dict[str, int], mastery_rate: dict[str, float]) -> dict[str, Any]:
    """cognitive-load edge type: does computed load (prerequisite depth) predict difficulty?"""
    ids = [c for c in depths if c in mastery_rate]
    rho = spearman([depths[c] for c in ids], [1 - mastery_rate[c] for c in ids]) if len(ids) >= 4 else None
    return {"concepts": len(ids), "spearman_depth_vs_difficulty": round(rho, 3) if rho is not None else None}


def misconception_audit(records: Sequence[dict[str, Any]], options: int = 4) -> dict[str, Any]:
    """common-misconception-of: among wrong answers, how often is the misconception option chosen?

    ``records``: ``{"misconception": id, "wrong": bool, "chose_misconception": bool}`` per attempt.
    Needs the wrong option recorded; callers without it should skip this audit.
    """
    chance = 1 / (options - 1)
    table: dict[str, list[int]] = {}
    for record in records:
        if record["wrong"]:
            cell = table.setdefault(record["misconception"], [0, 0])
            cell[0] += bool(record["chose_misconception"])
            cell[1] += 1
    out = {}
    for key, (chosen, wrong) in table.items():
        interval = wilson_interval(chosen, wrong)
        low, high = (interval[0] / 100, interval[1] / 100) if interval else (None, None)
        out[key] = {"wrong_answers": wrong, "share": round(chosen / wrong, 3),
                    "ci95": [round(low, 3), round(high, 3)] if interval else None,
                    "common": bool(interval and low > chance)}
    return out


def spearman(x: Sequence[float], y: Sequence[float]) -> float | None:
    def ranks(values: Sequence[float]) -> list[float]:
        order = sorted(range(len(values)), key=lambda i: values[i])
        out = [0.0] * len(values)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
                j += 1
            for k in range(i, j + 1):
                out[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return out

    rx, ry = ranks(x), ranks(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    sxx = sum((a - mx) ** 2 for a in rx)
    syy = sum((b - my) ** 2 for b in ry)
    sxy = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    return sxy / math.sqrt(sxx * syy) if sxx and syy else None


def _sd(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))
