"""Build the offline RL dataset (state, action, reward, next_state) from interaction logs.

Works on any log with one row per attempt. For MOOCCubeX, first map its exercise
records to KG concept ids (C1 provides that mapping), then call build_transitions().

Input row:  {"student_id", "concept", "timestamp", "score"}  score in {0, 1, 2}
Output:     list of dicts  {state, action, reward, next_state, done}
            state = {"mastery": {...}, "uncertainty": {...}}  (running estimates)
"""
from __future__ import annotations

from collections import defaultdict


def _update(est: dict, cnt: dict, concept: str, score: float, max_score: float):
    """Running average mastery; uncertainty shrinks with more attempts."""
    cnt[concept] = cnt.get(concept, 0) + 1
    x = score / max_score
    est[concept] = est.get(concept, 0.0) + (x - est.get(concept, 0.0)) / cnt[concept]


def _snapshot(est, cnt):
    return {"mastery": {k: round(v, 4) for k, v in est.items()},
            "uncertainty": {k: round(0.5 / (1 + n) ** 0.5, 4) for k, n in cnt.items()}}


def build_transitions(rows, max_score: float = 2.0, min_steps: int = 2):
    by_student = defaultdict(list)
    for r in rows:
        by_student[r["student_id"]].append(r)
    out = []
    for sid, rs in by_student.items():
        rs.sort(key=lambda r: r["timestamp"])
        if len(rs) < min_steps:
            continue
        est, cnt = {}, {}
        for i, r in enumerate(rs):
            state = _snapshot(est, cnt)
            _update(est, cnt, r["concept"], float(r["score"]), max_score)
            out.append({
                "student_id": sid,
                "state": state,
                "action": r["concept"],
                "reward": float(r["score"]),
                "next_state": _snapshot(est, cnt),
                "done": i == len(rs) - 1,
            })
    return out
