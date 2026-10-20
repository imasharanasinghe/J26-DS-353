# Component 4 (C4) — PP1 Summary

**Explanation Verifier**: checks an AI-written explanation against the knowledge graph and the learner's state, repairs what is wrong, and reports the result.

---

## 1. The problem C4 solves

An LLM tutor writes fluent explanations, but it can:

- **Hallucinate**: state something the knowledge graph says is false or does not support.
- **Ignore the learner**: lean on a prerequisite the learner has not mastered, or explain above their level.

C4 sits between the LLM and the learner. Nothing reaches the learner until it has been checked.

## 2. How it works (one slide)

```text
C1 graph + C2 learner state + C3 verified path + draft explanation
   -> split into atomic claims
   -> FACTUAL check    ENTAILED | CONTRADICTED | UNSUPPORTED   (evidence from the graph)
   -> COGNITIVE check  APPROPRIATE | BLOOM_MISMATCH | UNMASTERED_PREREQUISITE | INCONCLUSIVE
   -> rewrite ONLY the violating sentences
   -> re-verify (max 3 rounds)
   -> final explanation + faithfulness report
```

Valid sentences are kept as written. Only bad ones are repaired.

## 2b. Panel feedback and our response

**Feedback (proposal presentation):** strengthen the research contribution rather than only building a product, and suggest how to raise the student's cognitive level over time.

**Response:** cognitive appropriateness is now a **trajectory, not a snapshot**. C4 verifies that each explanation is faithful *and* targets the learner's **next** Bloom level, records what the learner demonstrates, and we test whether this raises the demonstrated level across sessions. New research questions: **RQ4a** (faithful and at the target level) and **RQ4b** (progression across sessions). Full detail, talking points and slide text are in [PP1.md](PP1.md).

| Snapshot (before) | Trajectory (now) |
|---|---|
| Match the current level | Target current level + 1 when prerequisites are mastered |
| Violation: too high (`BLOOM_MISMATCH`) | Too high **and** no task at the target level (`BLOOM_STAGNATION`) |
| Filters bad explanations | Moves the learner forward, with support that fades |

## 3. What we built on the `c4` branch

### Stage 1 — Planning and research rules
- Work plan, research guidelines (frozen metric definitions, failure policy) and a work log.
- Confirmed the PP1 constraints and the marking criteria.

### Stage 2 — Core verifier (`c4/pipeline.py`)
- Claim extraction with stable claim IDs and longest-match concept detection.
- Factual and cognitive labelling, with typed violations and a confidence tier.
- Targeted repair that uses a graph fact that itself verifies.
- Validation of the C3 handoff before verification.

### Stage 3 — Connecting to C1, C2 and C3
- Adapters that follow each branch's current contract:
  - C1 exports a graph.
  - C2 exposes mastery and uncertainty.
  - C3 exposes a verified-path JSON.
- C4 mock data under `c4/data/` has the same shape as the real outputs.
- Multiple explanation targets, and concepts beyond heaps.
- Singular and plural concept names are normalised.

### Stage 4 — Local LLM draft generation (`c4/explainer.py`)
- Optional Ollama integration (`qwen3:4b`) to write the draft.
- The template generator that once worked offline was removed (2026-10-20): drafts come only from the language model.
- Prompts constrain the output, and repetitive model responses are cleaned.
- The generator can be swapped without touching the verifier.

### Stage 5 — Preliminary evaluation (`c4/evaluation.py`)
- **Stress test**: 28 cases (7 concepts × 4 learner profiles), 84 claims, with ablations (factual only, cognitive only, full C4).
- **Natural set**: 28 real Qwen3 explanations (cached).
- **Threshold sensitivity** sweep.
- Stats: 95% confidence intervals and McNemar tests.
- Results are saved in `c4/results/` (see `RESULTS.md`).

### Stage 6 — Web workbench (`c4/web/`, `c4/server.py`, `c4/service.py`)
- A validated service layer and a localhost HTTP API (health, meta, verify, generate, results).
- A single-page UI with:
  - Target and learner selection, with a learner editor for mastery and uncertainty.
  - Claim cards showing typed violations and graph evidence.
  - The before/after rewrite trace, with an unresolved-claims notice.
  - An **Evaluation** tab.
  - A **verdict banner**, tooltips and a keyboard shortcut.
- Design: navy theme, Inter font (self-hosted, licensed).
- Downloadable JSON report.

### Stage 7 — Draft, verify and repair in one call
- `explain` endpoint and UI button run the whole flow. A draft is never shown unverified.
- **Inputs tab**: shows the C1, C2 and C3 inputs behind a run, so the panel can see what C4 received.

### Stage 8 — Structured, learner-specific explanations
- The explanation is now a document:
  - Path diagram.
  - What the concept is.
  - What to know first.
  - Where the learner stands.
  - A refresher on secured concepts.
  - Common mistakes from the graph.
- Learner-specific repair messages:
  - Unmastered prerequisite → "Review Binary Trees first: your mastery is 0.00, below the 0.70 this path needs."
  - Above the Bloom ceiling → saved for later.
  - Misconception → "Common mistake: … is false."
- Document-style UI, with aligned icons and text.

### Stage 9 — Bloom-level progression (response to the panel)
- **Policy** (`c4/progression.py`): demonstrated level per concept (1 Remember to 6 Create), target level = demonstrated + 1 when prerequisites are mastered, retry with full support after a failed stretch, demotion only after two failures on a demonstrated level, contingent scaffolding (full, partial, minimal).
- **Learner state**: a per-concept `bloom` record with history (a C4 extension; C2 does not provide it yet).
- **Verifier**: opt-in progressive mode. The Bloom ceiling is the target level; an explanation with no check question at that level is `BLOOM_STAGNATION` and is repaired; questions are task claims, not domain claims. Report schema 1.2.
- **Generator**: faded detail and a target-level check question with hints.
- **Estimator evaluation** (`c4/bloom.py`, `c4/data/bloom_items.json`): 90 labelled items with dev, test and indirect-phrasing splits.
- **Simulated multi-session experiment** (`c4/simulation.py`): paired conditions A (unverified), B (current C4), C (progressive), ablations, and three learner models including flat and matched controls; bootstrap intervals, Wilcoxon signed-rank, Cohen's dz.
- **Workbench**: a **Progression** tab (sessions, simulated answers, trajectory) and progression evidence in the **Evaluation** tab; `/api/session` and `/api/answer`.
- **Human pilot protocol** ([docs/PILOT_STUDY.md](docs/PILOT_STUDY.md)): written, not run, needs ethics approval.
- Run `python3 scripts/run_c4_progression.py` to reproduce; results are in `c4/results/PROGRESSION.md`.

## 4. Results (preliminary, 28-case stress test)

| | Hallucination | Cognitive mismatch | Cases with a violation |
|---|---|---|---|
| Unverified baseline | 25.0% | 29.8% | 28 / 28 |
| Factual check only | 0.0% | 28.1% | 12 / 28 |
| Cognitive check only | 24.5% | 0.0% | 13 / 28 |
| **Full C4** | **0.0%** | **0.0%** | **0 / 28** |

- All 44 violating claims were corrected, and no new violations were introduced.
- On real Qwen3 text, hallucination went from 100% to 0% (28 explanations).
- The verifier alone takes under 1 ms per case.

### Progression results (pilot; simulated learners)

**RQ4a, stress corpus (84 runs, same-verifier caveat):**

| Text | Question at target level | Runs with a violation |
|---|---|---|
| Unverified explanation | 0% | 84 / 84 |
| Static C4 (current) | 0% | 0 / 84 |
| **Progressive C4** | **100%** | **0 / 84** |

**RQ4b, 300 simulated learners, 8 sessions (capability gain, progressive minus current C4):**

| Learner model | Difference (95% interval) | Reading |
|---|---|---|
| ZPD (design hypothesis) | +0.36 (0.29 to 0.43), dz 0.59 | Helps, but reaches level 3 no sooner |
| Flat control | 0.00 | Ties exactly: level does not matter |
| Matched control | +0.02 (-0.05 to 0.09) | No advantage; worse at 12 sessions (-0.29) |

- The stretch above the demonstrated level is the active ingredient (+1.12 versus no stretch). Contingent fading adds nothing in this learner model.
- The effect is about zero at 4 sessions and grows with more (+0.90 at 12), so a short study can miss it.
- The Bloom estimator reaches 100% on its in-vocabulary test split and 16.7% on indirectly phrased items; there is one annotator and no kappa.

## 5. Honest limitations (expect these in the VIVA)

- Stress-test labels are built from a recipe, not human-annotated, so there is no Cohen's kappa. The perfect detection scores show the rules behave as specified. They are not evidence of generalisation.
- Post-repair rates use the same verifier that did the repair, so they are not independent.
- Factual matching is rule-based, not NLI.
- C1, C2 and C3 are not yet integrated end to end. Concept IDs differ between branches, so C4 uses interface-compatible mocks.
- Parameters are pilot values, not validated research values.
- **The progression results are simulated.** The learner models encode assumptions (the ZPD model partly returns its own assumption), so we also report flat and matched controls and where progression does not help. They are evidence about the design, not about students. The human pilot is the validation and has not been run.
- The Bloom estimator is a verb-cue matcher scored on items labelled by one annotator; it cannot read indirectly phrased questions.
- The per-concept Bloom record is a C4 extension that C2 does not provide yet; the policy starts every unseen concept at Remember (no placement check), and the check questions are generic templates.

## 6. Next steps (after PP1)

- Integrate with the real C1, C2 and C3 outputs.
- Independent human annotation of the evaluation labels.
- NLI-based factual matching.
- Evaluate on more concepts and learners.
- Second annotator and kappa for the Bloom items; a learned or NLI-based Bloom classifier.
- Agree the Bloom learner-state field with C2; add a placement check and concept-specific check questions.
- Ethics approval and the human pilot for RQ4b ([docs/PILOT_STUDY.md](docs/PILOT_STUDY.md)).

## 7. How to demo

See [c4/README.md](c4/README.md) for the run-sheet. Start the server, open the workbench, and use the **Verification**, **Progression**, **Inputs** and **Evaluation** tabs. For the progression demo: pick the "All prerequisites mastered" preset, start a session, answer well twice (target rises, support fades), answer "Not yet" once (retry with full support), then lower a prerequisite below 0.7 (the policy consolidates).

## 8. Where things are

| Path | What |
|---|---|
| `c4/` | Verifier, service, server, web UI, evaluation |
| `tests/` | Automated tests |
| `scripts/` | Evaluation runner, progression runner and server runner |
| `docs/` | Plans, log, guidelines, component proposals (C1–C4), PP1 marking criteria, WBS, pilot-study protocol |
| `PP1.md` | Panel response, talking points and slide text |
