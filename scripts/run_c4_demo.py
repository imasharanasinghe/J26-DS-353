from __future__ import annotations

import json
import argparse
from copy import deepcopy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from c4 import C4Pipeline, TemplateExplanationGenerator
from c4.adapters import load_c2_learner, load_json, validate_c3_path


DATA = ROOT / "c4" / "data"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--learner", help="Learner id when using a collection file")
    parser.add_argument("--generated", action="store_true",
                        help="Generate the input explanation from the C3 path and learner")
    parser.add_argument("--scenario", choices=("default", "valid", "factual", "cognitive"),
                        default="default")
    parser.add_argument("--pretty", action="store_true",
                        help="Print a concise human-readable report")
    args = parser.parse_args()

    pipeline = C4Pipeline.from_files(DATA / "knowledge_graph.json")
    path = load_json(DATA / "verified_path.json")
    validate_c3_path(path)
    learner = load_c2_learner(load_json(DATA / "learner_state.json"), args.learner)
    explanation = (DATA / "explanation.txt").read_text(encoding="utf-8")
    if args.scenario == "valid":
        learner = deepcopy(learner)
        learner["mastery"].update({"tree": 0.9, "binary_tree": 0.9})
        learner["uncertainty"].update({"tree": 0.1, "binary_tree": 0.1})
        explanation = "A heap is a complete binary tree."
    elif args.scenario == "factual":
        learner = deepcopy(learner)
        learner["mastery"].update({"tree": 0.9, "binary_tree": 0.9})
        learner["uncertainty"].update({"tree": 0.1, "binary_tree": 0.1})
        explanation = "A heap is a fully sorted array."
    elif args.scenario == "cognitive":
        explanation = "A heap is a complete binary tree."
    if args.generated:
        explanation = TemplateExplanationGenerator().generate(path, learner, pipeline.kg)
    result = pipeline.run(path, learner, explanation)
    if args.pretty:
        print(f"C4 REPORT | learner={result.learner_id} target={result.target}")
        print(f"verified_path={result.verified_path} rewrite_attempts={result.rewrite_attempts}")
        print(f"original: {result.original_explanation}")
        for claim in result.claims:
            print(
                f"- {claim.claim.claim_id}: factual={claim.factual_status} "
                f"cognitive={claim.cognitive_status} accepted={claim.accepted}"
            )
            if claim.violations:
                print(f"  violations: {', '.join(claim.violations)}")
        print(f"final: {result.final_explanation}")
        print(f"unresolved: {', '.join(result.unresolved_claims) or 'none'}")
        return
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
