# Component 4 proof of concept

This package is an independent C4 implementation. It does not copy or depend
on another component's private code. Its adapters follow the actual branch
contracts currently available from C1, C2, and C3:

- C1 currently exports unverified candidate CSVs.
- C2 exposes mastery and uncertainty values, either for one learner or a
  `learners` collection.
- C3 exposes a verified-path JSON object and can optionally load its graph from
  Neo4j.

The fixtures under `c4/data/` reproduce the documented C3 hand-off shape:

- `knowledge_graph.json`: C1-compatible graph evidence
- `learner_state.json`: C2-compatible mastery and uncertainty state
- `verified_path.json`: C3 `PlanResult.to_json` output
- `explanation.txt`: deterministic explanation input for the pilot

## Run the demo

From the repository root:

```bash
python3 scripts/run_c4_demo.py
```

The demo rejects unverified C3 paths, can generate an offline
path/learner-aware explanation with `--generated`, and decomposes explanations into claims,
checks factual evidence and cognitive suitability, rewrites violating claims,
and re-verifies them.

## Run tests

python3 scripts/run_c4_demo.py --generated
```bash
python3 -m pytest -q tests/test_c4.py
```

## Pilot assumptions

The implementation currently uses deterministic local rules so it is
reproducible without API keys or external services. The following are pilot
assumptions, not final validated research parameters:

- Mastery threshold: `0.70`
- Uncertainty threshold: `0.25`
- Default Bloom ceiling: `2`
- Bloom ceiling when all target prerequisites are mastered and certain: `3`
- Maximum C4 rewrite attempts: `3`

The factual checker currently uses exact normalized evidence matching. It is a
baseline for the C4 pipeline, not the final NLI evaluation. The Bloom estimator
uses a small verb-based heuristic. These choices must be replaced or evaluated
against manually labelled data before final research conclusions are drawn.

The template generator is deliberately not presented as a personalized LLM.
It is an offline stand-in for the future LLM generation boundary, allowing the
verification pipeline to be tested while the upstream components and model
choice remain incomplete.
