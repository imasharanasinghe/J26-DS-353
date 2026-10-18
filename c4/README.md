# Component 4 proof of concept

Independent C4 implementation: claim-level verification of a personalized
explanation against graph evidence (factual) and learner state (cognitive),
with targeted repair and a faithfulness report. It does not copy or depend on
another component's private code. Its adapters follow the branch contracts
currently available from C1, C2, and C3:

- C1 currently exports unverified candidate CSVs.
- C2 exposes mastery and uncertainty values, for one learner or a `learners`
  collection.
- C3 exposes a verified-path JSON object (`PlanResult.to_json`).

None of these is integrated end to end yet; concept identifiers differ between
the branches. The fixtures under `c4/data/` are C4's interface-compatible mocks:

- `knowledge_graph.json`: C1-compatible graph with `facts` and `known_false`
  statements per concept (temporary C4 test data)
- `learner_state.json`: C2-compatible mastery and uncertainty state
- `verified_path.json`: C3 `PlanResult.to_json` shape
- `explanation.txt`: three-sentence demo input
- `natural_cache.json`: cached Qwen3 outputs for the natural-generation set

## Pipeline

```text
verified C3 path + C2 learner + C1 graph + explanation
  -> sentence-level atomic claims (stable claim ids, longest-match concept detection)
  -> factual label  ENTAILED | CONTRADICTED | UNSUPPORTED  (+ graph evidence)
  -> cognitive label APPROPRIATE | BLOOM_MISMATCH | UNMASTERED_PREREQUISITE | INCONCLUSIVE
  -> typed violations + confidence tier
  -> rewrite ONLY violating sentences (graph fact that itself verifies, else review guidance)
  -> re-verify, bounded to 3 rounds, unresolved claims reported
  -> final explanation + report (c4-report/1.0): trace, review_first, metrics
```

Modules: `pipeline.py` (verify/repair), `metrics.py` (frozen metric definitions),
`evaluation.py` (stress test, natural set, threshold sensitivity), `explainer.py`
(replaceable generators), `adapters.py`, `paths.py`, `models.py`.

## Run the demo

From the repository root. The three contrasting examples use the unmodified
learner (arrays mastered, binary tree unmastered):

```bash
python3 scripts/run_c4_demo.py --pretty                       # all three in one explanation
python3 scripts/run_c4_demo.py --scenario valid --pretty      # supported + appropriate
python3 scripts/run_c4_demo.py --scenario factual --pretty    # contradicted claim
python3 scripts/run_c4_demo.py --scenario cognitive --pretty  # true but unmastered prerequisite
python3 scripts/run_c4_demo.py --target stack --pretty        # other targets: arrays, recursion, tree, binary_tree, stack, queue
python3 scripts/run_c4_demo.py                                # full JSON report
python3 scripts/run_c4_demo.py --generated --pretty           # offline template generator
```

Optional local Qwen3 generator (no API key; output is untrusted text that must
pass the same verification):

```bash
ollama serve
ollama pull qwen3:4b
python3 scripts/run_c4_demo.py --ollama --model qwen3:4b --pretty
```

## Run tests and evaluation

```bash
python3 -m pytest -q tests
python3 scripts/run_c4_eval.py            # writes c4/results/RESULTS.md and JSON
python3 scripts/run_c4_eval.py --refresh  # regenerate missing Qwen outputs into the cache
```

## Pilot parameters (assumptions, not validated research values)

- Mastered: `mastery >= 0.70` and `uncertainty <= 0.25`
- Mastery within `0.05` of the threshold, uncertainty above `0.25`, or missing
  learner history is `INCONCLUSIVE`, never silently accepted
- Bloom ceiling `2`, raised to `3` only when every direct prerequisite of the
  target is mastered and certain; uncertainty therefore lowers the ceiling
- The current target is exempt from the prerequisite check (being new is not a
  violation); every other concept a claim mentions must be mastered
- Entailment: content-word Jaccard `>= 0.6` against a graph fact; a
  `known_false` statement wins only when the claim is closer to it than to any
  true fact and negation polarity matches
- Maximum rewrite rounds: `3`; unresolved claims are listed, never reported as verified

## Limitations (read before presenting results)

- Factual checking is rule-based graph-statement matching, not NLI. It cannot
  tell a faithful paraphrase from an invention; on natural Qwen output it
  flags essentially every sentence as "not graph-supported".
- Claims are whole sentences, not atomic propositions.
- The Bloom estimator is a verb-cue heuristic and is not yet evaluated against
  manual labels.
- Stress-test labels are built by recipe plus a hand-written mention table.
  There are no independent human annotations and no Cohen's kappa.
  Post-repair rates use the same verifier and are not independent evidence.
- Real C1/C2/C3 integration, Neo4j retrieval, and the learner study remain pending.
