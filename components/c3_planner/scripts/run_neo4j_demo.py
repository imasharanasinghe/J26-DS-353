"""Run C3 on the knowledge graph stored in Neo4j.

  python scripts/run_neo4j_demo.py
  python scripts/run_neo4j_demo.py --target priority_queue
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from c3 import C3Pipeline, LLMProposer, MockProposer, load_learners, path_str  # noqa: E402
from c3.kg_neo4j import load_kg_from_neo4j  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="heap")
    ap.add_argument("--proposer", choices=["mock", "llm"], default="mock")
    ap.add_argument("--learners", default=os.path.join(ROOT, "data", "mock_learners.json"))
    a = ap.parse_args()

    kg = load_kg_from_neo4j()
    print(f"Loaded from Neo4j: {len(kg.concepts)} concepts, "
          f"{len(kg.misconceptions)} misconceptions")
    print(f"{a.target} needs (strong prerequisites only): {sorted(kg.ancestors(a.target))}")

    learners = load_learners(a.learners)
    proposer = MockProposer(seed=7) if a.proposer == "mock" else LLMProposer()
    print(f"Proposer: {a.proposer}"
          + (f" ({proposer.client.provider} / {proposer.client.model})" if a.proposer == "llm" else ""))
    pipe = C3Pipeline(kg, proposer)
    for lid in ["L01_beginner", "L02_intermediate", "L05_uneven"]:
        res = pipe.plan(learners[lid], a.target)
        print(f"\n{lid} -> {a.target}   [{res.source}, verified={res.verified}]")
        for d in res.drafts:
            faults = "; ".join(map(str, d.initial_violations)) or "no faults"
            print(f"   draft {d.draft_id + 1}: {path_str(d.initial_path)}")
            print(f"            checker: {faults}")
        print(f"   FINAL : {path_str(res.path)}")


if __name__ == "__main__":
    main()
