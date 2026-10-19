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
  -> final explanation + report (c4-report/1.1): trace, review_first, metrics
```

Modules: `pipeline.py` (verify/repair), `service.py` and `server.py` (web API),
`web/` (frontend), `metrics.py` (frozen metric definitions),
`evaluation.py` (stress test, natural set, threshold sensitivity), `explainer.py`
(replaceable generators), `adapters.py`, `paths.py`, `models.py`.

## The explanation

The draft is a structured document, not a sentence: a path diagram, what the concept
is, what to know first, where the learner stands (from C2 mastery and the C3 path), a
refresher on concepts the learner has secured, and common mistakes from the graph.
There is no length limit; Markdown headings and bullets are supported (a heading is
structure, every sentence under it is a claim). The offline template builds it from
graph facts; Qwen writes the concept section and the same code writes the rest.

What the repair writes (only for the violating sentence; valid sentences are kept):

| Violation | Replacement |
|---|---|
| Contradicts a graph misconception | `Common mistake: "..." is false.` plus a graph fact that verifies for this learner |
| Unsupported claim | the closest graph fact that verifies for this learner |
| Relies on an unmastered prerequisite | `Review Binary Trees first: your mastery is 0.00, below the 0.70 this path needs, and it is a prerequisite of Heaps.` |
| Prerequisite with uncertain or missing history | `Take a quick check on Recursion first: ... (mastery 0.75, uncertainty 0.32).` |
| Above the Bloom ceiling | a sentence saying it is saved for later, then a graph fact at the learner's level |

Sentences C4 writes from C2/C3/C1 data (`c4/grounding.py`) are recognised by exact
regeneration and marked `source: "grounded"` in the report. They are excluded from the
hallucination and mismatch denominators so they cannot dilute the rates; a model
sentence that merely resembles one is verified like any other claim.

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

## Web workbench (frontend)

A local, dependency-free UI over the same pipeline (standard-library server,
vanilla HTML/CSS/JS; nothing is sent off the machine except the optional local
Ollama call):

```bash
python3 scripts/run_c4_server.py --open     # http://127.0.0.1:8765
```

- **Fully automatic:** "Draft + verify" (template or Qwen) generates the draft and
  runs verify, repair and report in one step (`POST /api/explain`); the draft is
  shown as the original and never delivered unverified.
- **Inputs tab:** the C3 verified path, C2 learner state, and C1 graph evidence
  used by the current run (fixtures, labelled as such).
- **Verification tab:** choose a target and learner state (presets or per-concept
  mastery/uncertainty sliders), load an example or draft with the template or
  Qwen, then verify. You see claim cards (factual and cognitive labels, typed
  violations, graph evidence), the before/after rewrite trace, re-verification,
  the final explanation, metrics, and the downloadable `c4-report/1.1` JSON.
- **Settings:** toggle factual verification, cognitive verification, or the
  rewrite loop to reproduce the ablations interactively.
- **Evaluation tab:** the committed stress-test and Qwen results with their caveats.
- Deep links: `/#run` runs the default case on load, `/#eval` opens the evaluation tab.
- The server binds to `127.0.0.1` and has no authentication; do not expose it.

API: `GET /api/health|meta|results`, `POST /api/verify|generate`
(see [c4/server.py](server.py) and [c4/service.py](service.py)).

### Suggested PP1 demo run-sheet

1. Start the server and open the page (Qwen chip green if Ollama is ready).
2. Heap + demo learner, **Mixed** example, Verify: walk through the three claims
   (supported, contradicted, true but too advanced), then the rewrite trace.
3. Edit Binary Trees mastery to 0.95 / uncertainty 0.05 and verify again: the
   cognitive violation disappears, showing the check is learner-relative.
4. Untick **Rewrite loop**: violations stay unresolved and are not presented as verified.
5. Optional: **Qwen (Ollama)** draft, then verify.
6. **Evaluation** tab: ablation bars, then say the caveats aloud.

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

## Third-party assets

- Josefin Sans (variable roman and italic), (c) The Josefin Sans Project Authors,
  SIL Open Font License 1.1 - see [web/fonts/OFL.txt](web/fonts/OFL.txt).
  Self-hosted; the UI makes no external requests.

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
