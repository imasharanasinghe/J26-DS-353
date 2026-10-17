"""The PP1 key experiment: does the critic actually remove teaching-rule faults?

Runs every learner x target under four set-ups and compares them:
  A  proposer only            (trust the LLM's first draft)
  B  + critic + repair        (no safety net)
  C  full C3                  (+ topological-sort fallback)
  D  topological sort only    (rule-based baseline, no LLM)

Statistics reported:
  - fault rate per set-up with a 95% Wilson confidence interval
  - exact McNemar test, A vs B (same cases, paired): is the drop real or luck?

Examples
  python scripts/run_ablation.py                                   # mock proposer, NOT real results
  python scripts/run_ablation.py --kg neo4j                        # mock proposer on your Neo4j graph
  python scripts/run_ablation.py --kg neo4j --proposer llm         # real LLM: your PP1 numbers
"""
import argparse
import csv
import math
import os
import statistics as st
import sys
import zlib
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from c3 import (C3Config, C3Pipeline, Critic, KnowledgeGraph, LLMProposer, MockProposer,  # noqa: E402
                build_fallback_path, compute_frontier, load_learners, path_str)
from c3.rl import HeuristicReranker  # noqa: E402

DEFAULT_TARGETS = ["heap", "priority_queue", "bst", "binary_tree", "tree", "stack", "queue",
                   "recursion", "dijkstra", "dfs", "bfs", "merge_sort", "hash_table",
                   "avl_tree", "dynamic_programming", "heap_sort", "tree_traversal"]
SETUPS = {"A_proposer_only": dict(use_critic=False),
          "B_critic_repair": dict(use_fallback=False),
          "C_full_C3": dict()}
ALL = list(SETUPS) + ["D_topo_only"]


# ---------------------------------------------------------------- statistics
def wilson_ci(k, n, z=1.96):
    """95% confidence interval for a proportion k/n (works well for small n)."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def mcnemar_exact(b, c):
    """Exact two-sided McNemar p-value. b = A faulty & B clean, c = A clean & B faulty."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * p)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kg", default=os.path.join(ROOT, "data", "mock_kg.json"),
                    help="path to a KG JSON file, or the word 'neo4j' to read from Neo4j")
    ap.add_argument("--learners", default=os.path.join(ROOT, "data", "mock_learners.json"))
    ap.add_argument("--proposer", choices=["mock", "llm"], default="mock")
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--targets", nargs="*", default=DEFAULT_TARGETS)
    ap.add_argument("--outdir", default=os.path.join(ROOT, "results"))
    a = ap.parse_args()

    if a.kg == "neo4j":
        from c3.kg_neo4j import load_kg_from_neo4j
        kg, kg_name = load_kg_from_neo4j(), "neo4j"
    else:
        kg, kg_name = KnowledgeGraph.from_json(a.kg), os.path.splitext(os.path.basename(a.kg))[0]
    learners = load_learners(a.learners)
    cfg = C3Config(k_drafts=a.k)
    critic, rr = Critic(kg, cfg), HeuristicReranker()
    llm = LLMProposer() if a.proposer == "llm" else None

    targets = [t for t in a.targets if kg.has(t)]
    cases = [(lid, t) for lid in learners for t in targets
             if not compute_frontier(kg, learners[lid], t, cfg).target_already_known]
    print(f"KG: {kg_name} ({len(kg.concepts)} concepts) | proposer: {a.proposer} | "
          f"{len(cases)} cases x {len(ALL)} set-ups")

    rows, rule_hits, faulty = [], {s: Counter() for s in ALL}, {s: {} for s in ALL}
    for n, (lid, t) in enumerate(cases, 1):
        lr = learners[lid]
        case_seed = a.seed * 100003 + zlib.crc32(f"{lid}|{t}".encode())
        cached = None
        for setup, kw in SETUPS.items():
            prop = MockProposer(seed=case_seed) if llm is None else _CachedDrafts(llm, cached)
            res = C3Pipeline(kg, prop, cfg).plan(lr, t, **kw)
            if llm is not None:
                cached = prop.drafts
            left = critic.check(res.path, lr, t)
            for v in left:
                rule_hits[setup][v.rule] += 1
            faulty[setup][(lid, t)] = bool(left)
            rows.append(_row(setup, lid, t, res.path, left, res, rr, lr, kg))
        p = build_fallback_path(kg, lr, compute_frontier(kg, lr, t, cfg), cfg)
        left = critic.check(p, lr, t)
        faulty["D_topo_only"][(lid, t)] = bool(left)
        rows.append(_row("D_topo_only", lid, t, p, left, None, rr, lr, kg))
        if llm is not None:
            print(f"  case {n}/{len(cases)} done  (LLM calls so far: {llm.client.calls})")

    tag = f"{a.proposer}_{kg_name}"
    os.makedirs(a.outdir, exist_ok=True)
    _write_csv(os.path.join(a.outdir, f"ablation_cases_{tag}.csv"), rows)

    summary = []
    for setup in ALL:
        rs = [r for r in rows if r["setup"] == setup]
        k = sum(r["violations"] > 0 for r in rs)
        lo, hi = wilson_ci(k, len(rs))
        rounds = [r["repair_rounds_mean"] for r in rs if r["repair_rounds_mean"] != ""]
        summary.append({
            "setup": setup, "cases": len(rs),
            "fault_rate_%": round(100 * k / len(rs), 1),
            "95%_CI": f"{100 * lo:.1f}-{100 * hi:.1f}",
            "mean_faults": round(st.mean(r["violations"] for r in rs), 2),
            **{r: rule_hits[setup][r] for r in ("R1", "R2", "R3", "R4", "R5")},
            "repair_rounds": round(st.mean(rounds), 2) if rounds else "",
            "fallback_%": round(100 * sum(r["source"] == "fallback" for r in rs) / len(rs), 1),
            "steps": round(st.mean(r["steps"] for r in rs), 1),
            "score": round(st.mean(r["score"] for r in rs), 3),
        })
    _write_csv(os.path.join(a.outdir, f"ablation_summary_{tag}.csv"), summary)

    # paired test A vs B on the same cases
    b = sum(faulty["A_proposer_only"][c] and not faulty["B_critic_repair"][c] for c in cases)
    c = sum(not faulty["A_proposer_only"][c] and faulty["B_critic_repair"][c] for c in cases)
    p = mcnemar_exact(b, c)

    cols = list(summary[0])
    print("\n| " + " | ".join(cols) + " |")
    print("|" + "---|" * len(cols))
    for s in summary:
        print("| " + " | ".join(str(s[x]) for x in cols) + " |")
    print(f"\nMcNemar (A vs B, paired): A-faulty-only={b}, B-faulty-only={c}, exact p = {p:.4g}")
    if llm is not None:
        print(f"LLM calls: {llm.client.calls} | call failures: {llm.client.failures} | "
              f"unreadable replies: {llm.format_failures}")
        print("Every prompt and reply is in results/llm_log.jsonl")
    else:
        print("NOTE: mock proposer = simulated LLM mistakes. Use --proposer llm for real results.")
    with open(os.path.join(a.outdir, f"ablation_stats_{tag}.txt"), "w", encoding="utf-8") as f:
        f.write(f"McNemar A vs B: b={b} c={c} p={p:.6g}\n")
    print(f"Saved results/ablation_*_{tag}.*")


def _row(setup, lid, t, path, left, res, rr, lr, kg):
    return {
        "setup": setup, "learner": lid, "target": t,
        "violations": len(left),
        "violation_types": ";".join(sorted({v.type for v in left})),
        "source": res.source if res else "topo",
        "repair_rounds_mean": round(st.mean(d.rounds for d in res.drafts), 2)
        if res and res.drafts and setup != "A_proposer_only" else "",
        "steps": len(path), "score": rr.score(path, lr, kg), "path": path_str(path),
    }


def _write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


class _CachedDrafts:
    """Wraps the LLM proposer so set-ups A, B and C see the SAME drafts for a case."""

    def __init__(self, inner, drafts=None):
        self.inner, self.drafts = inner, drafts

    def propose(self, ctx, k):
        if self.drafts is None:
            self.drafts = self.inner.propose(ctx, k)
        return [list(d) for d in self.drafts]

    def repair(self, ctx, path, violations):
        return self.inner.repair(ctx, path, violations)


if __name__ == "__main__":
    main()
