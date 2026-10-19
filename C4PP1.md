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
- A template generator works offline.
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
- Design: navy theme, Josefin Sans font (self-hosted, licensed).
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

## 5. Honest limitations (expect these in the VIVA)

- Stress-test labels are built from a recipe, not human-annotated, so there is no Cohen's kappa. The perfect detection scores show the rules behave as specified. They are not evidence of generalisation.
- Post-repair rates use the same verifier that did the repair, so they are not independent.
- Factual matching is rule-based, not NLI.
- C1, C2 and C3 are not yet integrated end to end. Concept IDs differ between branches, so C4 uses interface-compatible mocks.
- Parameters are pilot values, not validated research values.

## 6. Next steps (after PP1)

- Integrate with the real C1, C2 and C3 outputs.
- Independent human annotation of the evaluation labels.
- NLI-based factual matching.
- Evaluate on more concepts and learners.

## 7. How to demo

See [c4/README.md](c4/README.md) for the run-sheet. Start the server, open the workbench, and use the **Inputs**, **Verify**, and **Evaluation** tabs.

## 8. Where things are

| Path | What |
|---|---|
| `c4/` | Verifier, service, server, web UI, evaluation |
| `tests/` | Automated tests |
| `scripts/` | Evaluation runner and server runner |
| `docs/` | Plans, log, guidelines, component proposals (C1–C4), PP1 marking criteria, WBS |
