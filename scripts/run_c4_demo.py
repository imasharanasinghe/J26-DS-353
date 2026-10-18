from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from c4 import C4Pipeline, OllamaExplanationGenerator, TemplateExplanationGenerator
from c4.adapters import load_c2_learner, load_json, validate_c3_path
from c4.paths import build_verified_path
from c4.service import scenario_text


DATA = ROOT / "c4" / "data"


def print_claims(title: str, claims) -> None:
    print(title)
    for item in claims:
        flags = ", ".join(item.violations) or "none"
        print(f"  {item.claim.claim_id} [{item.confidence}] {item.claim.text}")
        print(f"      factual={item.factual_status} cognitive={item.cognitive_status} "
              f"bloom~{item.claim.estimated_bloom_level} violations: {flags}")
        for evidence in item.evidence:
            print(f"      evidence: {evidence}")


def print_report(result) -> None:
    metrics = result.metrics
    print(f"C4 REPORT | learner={result.learner_id} target={result.target} "
          f"verified_path={result.verified_path}")
    print(f"ORIGINAL: {result.original_explanation}\n")
    print_claims("INITIAL VERIFICATION", result.initial_claims)
    print("\nTARGETED REWRITES (only violating claims change)")
    if not result.trace:
        print("  none needed")
    for step in result.trace:
        print(f"  attempt {step.attempt} {step.claim_id} [{', '.join(step.violations)}] via {step.strategy}")
        print(f"      - {step.before}\n      + {step.after or '(sentence removed)'}")
    print()
    print_claims("RE-VERIFICATION", result.claims)
    print(f"\nFINAL: {result.final_explanation}")
    print(f"unresolved: {', '.join(result.unresolved_claims) or 'none'}"
          f" | review first: {', '.join(result.review_first) or 'nothing'}")
    before, after = metrics["before"], metrics["after"]
    print(f"hallucination rate {before['hallucination_rate']}% -> {after['hallucination_rate']}% | "
          f"cognitive mismatch {before['cognitive_mismatch_rate']}% -> {after['cognitive_mismatch_rate']}% | "
          f"rewrite success {metrics['rewrite_success_rate']}% | "
          f"new violations {metrics['new_violations_introduced']} | "
          f"latency {result.latency_s * 1000:.1f} ms")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--learner", help="Learner id when using a collection file")
    parser.add_argument("--target", default="heap",
                        help="Target concept to explain, for example arrays or recursion")
    parser.add_argument("--generated", action="store_true",
                        help="Generate the input explanation from the C3 path and learner")
    parser.add_argument("--ollama", action="store_true",
                        help="Generate the input explanation with local Ollama")
    parser.add_argument("--model", default="qwen3:4b", help="Ollama model name")
    parser.add_argument("--scenario", choices=("default", "valid", "factual", "cognitive"),
                        default="default")
    parser.add_argument("--pretty", action="store_true",
                        help="Print a concise human-readable report")
    args = parser.parse_args()

    pipeline = C4Pipeline.from_files(DATA / "knowledge_graph.json")
    learner = load_c2_learner(load_json(DATA / "learner_state.json"), args.learner)
    path = load_json(DATA / "verified_path.json")
    if args.target != path["target"]:
        path = build_verified_path(args.target, pipeline.kg)
    path["learner_id"] = learner["learner_id"]
    validate_c3_path(path)
    default_text = (DATA / "explanation.txt").read_text(encoding="utf-8").strip()
    explanation = scenario_text(pipeline, args.target, args.scenario, default_text)
    if args.ollama:
        explanation = OllamaExplanationGenerator(model=args.model).generate(
            path, learner, pipeline.kg
        )
    elif args.generated:
        explanation = TemplateExplanationGenerator().generate(path, learner, pipeline.kg)
    result = pipeline.run(path, learner, explanation)
    if args.pretty:
        print_report(result)
        return
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
