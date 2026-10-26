# Component 4: Current State (as of 26 October 2026)

J26-DS-353, Component 4 (Amarasinghe S A R U, IT23216778). Branch `c4`.

This file records what C4 does today, what it contributes, what evidence exists and what is missing. It describes the **implemented, committed scope**. The draft Teachability extension is described in [NEW1.md](NEW1.md) and is not approved or implemented. Related files: [PP1.md](PP1.md) (panel response and slides), [c4/README.md](c4/README.md) (technical readme), [docs/C4.md](docs/C4.md) (proposal).

Status checks made when this file was written: 161 tests pass (about 5 s); about 5,900 lines across `c4/`, `tests/`, `scripts/` and the web UI.

---

## 1. In one sentence

C4 is a **verifier** that sits between an LLM tutor and the learner. It checks that an explanation is true (matches the knowledge graph) and suits this learner (matches their mastery and Bloom level), rewrites only the bad sentences, and never shows the learner an unchecked draft.

## 2. How it works

```text
C1 graph + C2 learner state + C3 verified path + draft explanation
  -> split into sentence-level claims (stable ids, longest-match concept detection)
  -> FACTUAL label    ENTAILED | CONTRADICTED | UNSUPPORTED  (with graph evidence)
  -> COGNITIVE label  APPROPRIATE | BLOOM_MISMATCH | UNMASTERED_PREREQUISITE | INCONCLUSIVE
  -> typed violations + confidence tier
  -> rewrite only the violating sentences, then re-verify (max 3 rounds)
  -> final explanation + report (JSON, schema c4-report/1.2)
```

### 2.1 Factual check

- A claim is matched to graph facts by content-word Jaccard similarity, threshold 0.6.
- A `known_false` statement wins only if the claim is closer to it than to any true fact and the negation polarity matches.
- This is rule-based, not NLI.

### 2.2 Cognitive check

- A concept is **mastered** when mastery >= 0.70 and uncertainty <= 0.25.
- Mastery within 0.05 of the threshold, uncertainty above 0.25, or missing learner history gives `INCONCLUSIVE`. It is never silently accepted.
- A verb-cue estimator assigns each claim a Bloom level.
- The Bloom ceiling is 2, raised to 3 only when every direct prerequisite of the target is mastered and certain.
- The target concept is exempt from the prerequisite check (being new is not a violation); every other concept a claim mentions must be mastered.

### 2.3 Repair

Only the violating sentence is replaced; valid sentences are kept as written.

| Violation | What C4 writes |
|---|---|
| Contradicts a graph misconception | `Common mistake: "..." is false.` plus a graph fact that verifies for this learner |
| Unsupported claim | The closest graph fact that verifies for this learner |
| Relies on an unmastered prerequisite | `Review Binary Trees first: your mastery is 0.00, below the 0.70 this path needs, and it is a prerequisite of Heaps.` |
| Uncertain or missing history | `Take a quick check on Recursion first: ... (mastery 0.75, uncertainty 0.32).` |
| Above the Bloom ceiling | A sentence saying it is saved for later, then a graph fact at the learner's level |

- Sentences C4 itself writes from C1/C2/C3 data are marked `source: "grounded"` and excluded from the hallucination and mismatch denominators so they cannot dilute the rates.
- Claims still unresolved after 3 rounds are listed in the report. They are never reported as verified.

### 2.4 Draft generation

- Drafts come only from a local Qwen3 4B model through Ollama. The offline template generator was removed on 20 October.
- The draft is a structured document: path diagram, what the concept is, what to know first, where the learner stands, a refresher on secured concepts, and common mistakes from the graph.
- The generator is replaceable (GPT-4o later) without touching the verifier. Verifying pasted text and all evaluation scripts need no model.

### 2.5 Bloom-level progression (the response to the proposal panel)

Cognitive appropriateness is treated as a trajectory, not a snapshot.

- Each learner has a per-concept `bloom` record: the **demonstrated level** (1 Remember to 6 Create) and the history of check-question results. C2 does not provide this field yet, so it is a C4 extension (`c4/progression.py`).
- **Target level** = demonstrated level + 1 when every direct prerequisite is mastered; otherwise the demonstrated level (consolidate).
- A failed stretch is retried with full support. A learner is demoted only after two failures at a demonstrated level.
- **Contingent scaffolding:** full support at the start and after a failure, partial after one pass, minimal after two.
- The verifier's Bloom ceiling becomes the target level. An explanation with no accepted check question at that level is a `BLOOM_STAGNATION` violation, repaired by appending a "Check yourself" section. A question above the target is a `BLOOM_MISMATCH` and is re-levelled.
- Check questions are tasks, not domain claims: outside the hallucination denominator, inside the cognitive-mismatch one.

## 3. The product (what can be run)

| Piece | How to use it |
|---|---|
| Web workbench | `python3 scripts/run_c4_server.py --open` (http://127.0.0.1:8765) |
| Demo CLI | `python3 scripts/run_c4_demo.py --pretty` (scenarios valid, factual, cognitive; `--target`; `--ollama`) |
| Evaluation | `python3 scripts/run_c4_eval.py` (writes `c4/results/RESULTS.md`) |
| Progression experiment | `python3 scripts/run_c4_progression.py` (writes `c4/results/PROGRESSION.md`) |
| Tests | `python3 -m pytest -q tests` |

Workbench tabs: **Inputs** (the C1/C2/C3 data behind a run), **Verification** (claim cards with evidence, learner sliders, rewrite trace, ablation toggles, downloadable JSON report), **Progression** (sessions with simulated answers and the learner's trajectory), **Evaluation** (committed results with caveats).

- API: `GET /api/health|meta|results`, `POST /api/verify|generate|explain|session|answer`.
- Local only: standard-library server, vanilla JS, self-hosted fonts, no external requests, bound to 127.0.0.1 with no authentication (do not expose it).
- Branding: CartoLEARN (Outfit typeface, mark, palette).

## 4. Evidence so far

### 4.1 Controlled stress test (28 cases = 7 concepts x 4 learner profiles; 84 claims)

| Condition | Hallucination | Cognitive mismatch | Cases with a violation |
|---|---|---|---|
| Unverified baseline | 25.0% | 29.8% | 28 / 28 |
| Factual check only | 0.0% | 28.1% | 12 / 28 |
| Cognitive check only | 24.5% | 0.0% | 13 / 28 |
| **Full C4** | **0.0%** | **0.0%** | **0 / 28** |

- All 44 violating claims corrected; 0 new violations introduced.
- Detection precision, recall and F1 are 1.0 against the reference labels.
- About 0.5 ms per case (verifier only, no model calls).

### 4.2 Natural Qwen3 output (28 explanations, cached)

- Hallucination 100% to 0%, cognitive mismatch 23.5% to 0%.
- Read the 100% as "not supported by the two graph facts", not as true hallucination: the strict rule flags essentially every sentence of natural text.
- Threshold sensitivity (0.3 to 0.8) is in `c4/results/RESULTS.md`.

### 4.3 Progression (simulated learners)

**RQ4a**, stress corpus (84 runs, same-verifier caveat):

| Text | Question at target level | Runs with a violation |
|---|---|---|
| Unverified | 0% | 84 / 84 |
| Static C4 | 0% | 0 / 84 |
| **Progressive C4** | **100%** | **0 / 84** |

**RQ4b**, 300 simulated learners, 8 sessions (gain of progressive over current C4):

| Learner model | Difference (95% interval) | Reading |
|---|---|---|
| ZPD (design hypothesis) | +0.36 (0.29 to 0.43), dz 0.59 | Helps, but reaches level 3 no sooner |
| Flat control | 0.00 | Ties: level does not matter |
| Matched control | +0.02 (-0.05 to 0.09) | No advantage; worse at 12 sessions (-0.29) |

- The stretch above the demonstrated level is the active ingredient (+1.12 versus no stretch). Contingent fading adds nothing in this learner model.
- The effect is about zero at 4 sessions and grows with more (+0.90 at 12), so a short study can miss it.
- Statistics: paired conditions, bootstrap intervals, Wilcoxon signed-rank, Cohen's dz.

### 4.4 Bloom estimator

- 90 labelled items across 6 levels, dev, test and indirect-phrasing splits (`c4/data/bloom_items.json`).
- 100% on the in-vocabulary test split, **16.7% on indirectly phrased items**. Single annotator, no kappa.

## 5. Contributions

### 5.1 Research contribution (currently claimed)

1. **Faithfulness as two axes.** Factual faithfulness and learner-relative cognitive appropriateness are verified at claim level; a true but too-advanced sentence counts as a violation.
2. **Cognitive appropriateness as a trajectory.** The target is the learner's next Bloom level; `BLOOM_STAGNATION` is a new violation type; scaffolding fades with success.
3. **A simulated test of whether this helps**, with flat and matched controls that show where it does not.
4. **Method pieces:** frozen metric definitions and failure policy, an ablation design, a labelled Bloom item set, and a human pilot-study protocol ([docs/PILOT_STUDY.md](docs/PILOT_STUDY.md)).

### 5.2 Product contribution

- The verify, repair and report middleware, the final layer of the four-component framework.
- Claim-level, auditable output: evidence per claim, a rewrite trace and a machine-readable report.
- The workbench as a demonstration surface.

## 6. Honest weaknesses (say these before the panel does)

- **Circular evidence.** Stress labels are built by recipe, not annotated by people, and post-repair rates use the same verifier that did the repair. Perfect scores show the rules behave as specified, not that they generalise.
- **No human annotation and no Cohen's kappa** for the stress corpus or the Bloom items.
- **Factual matching is lexical, not NLI**; it cannot tell a faithful paraphrase from an invention.
- **Claims are whole sentences**, not atomic propositions.
- **No end-to-end integration.** C1, C2 and C3 are not integrated; concept ids differ between branches, so C4 uses interface-compatible mocks.
- **The progression results are simulated.** The ZPD model partly returns its own assumption. No human pilot has been run and it needs SLIIT ethics approval.
- **Smaller gaps:** no placement check for unseen concepts (every one starts at Remember); check questions are generic templates; parameters are pilot values.
- **Novelty is unchecked.** No literature search has been done.

## 7. Where the project stands

- PP1 is over. The panel said the four components together amounted to roughly one normal final-year component and asked for something deeper in each. The next milestone is **PP2, the final presentation**.
- The committed scope is what this file describes.
- [NEW1.md](NEW1.md) is a draft, unapproved extension: a knowledge-restricted AI novice produces a **teachability score** (how much understanding transfers), with explanation survivability (A -> B -> C chains) as the recommended single discovery. Tutor-tutee distance and groups of four are a research pilot, and the stretch experiments are future work. The verifier would remain as the correctness instrument.
- Outstanding work is listed in [docs/PLAN.md](docs/PLAN.md) and in section 6 above.

## 8. Other files

- [docs/C4.md](docs/C4.md) and the PP1 files describe the pre-Teachability scope and have not been updated for it, deliberately, until the new scope is approved.
