"""Plan one path and print every step of the pipeline in plain words.

  python scripts/run_demo.py --learner L02_intermediate --target heap
  python scripts/run_demo.py --learner L03_strong_unsure --target dijkstra --proposer llm
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from c3 import C3Config, C3Pipeline, KnowledgeGraph, LLMProposer, MockProposer, load_learners, path_str  # noqa: E402
from c3.frontier import compute_frontier  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kg", default=os.path.join(ROOT, "data", "mock_kg.json"))
    ap.add_argument("--learners", default=os.path.join(ROOT, "data", "mock_learners.json"))
    ap.add_argument("--learner", default="L02_intermediate")
    ap.add_argument("--target", default="heap")
    ap.add_argument("--proposer", choices=["mock", "llm"], default="mock")
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "demo_output.json"))
    a = ap.parse_args()

    kg = KnowledgeGraph.from_json(a.kg)
    learner = load_learners(a.learners)[a.learner]
    cfg = C3Config(k_drafts=a.k)
    proposer = MockProposer(seed=a.seed) if a.proposer == "mock" else LLMProposer()
    pipe = C3Pipeline(kg, proposer, cfg)

    fr = compute_frontier(kg, learner, a.target, cfg)
    print(f"\n=== C3 demo: {learner.learner_id} -> {kg.name(a.target)} ({a.proposer} proposer) ===\n")
    print("L1 still needs to learn :", ", ".join(fr.required) or "nothing")
    print("L1 can start right now  :", ", ".join(fr.admissible_now) or "-")
    print("L1 unsure, should probe :", ", ".join(fr.probe_candidates) or "-")
    print("L1 misconceptions       :", ", ".join(fr.misconceptions) or "-")

    res = pipe.plan(learner, a.target)
    for d in res.drafts:
        print(f"\n--- Draft {d.draft_id + 1} ---")
        print("L3 proposer wrote :", path_str(d.initial_path))
        for rnd, vs in d.history:
            label = "L4 critic found" if rnd == 0 else f"L5 after repair {rnd}"
            print(f"{label:<17} : " + ("OK, no faults" if not vs else "; ".join(map(str, vs))))
        print("Result            :", "VERIFIED" if d.verified else "still has faults")

    print(f"\nL6/L7 chosen ({res.source}):", path_str(res.path))
    print("Verified:", res.verified, "| score:", res.score, f"| {res.elapsed_s:.3f}s")

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res.to_json(kg), f, indent=2)
    print(f"\nL8 output for C4 saved to {os.path.relpath(a.out, ROOT)}")


if __name__ == "__main__":
    main()
