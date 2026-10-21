# Component 4: PP1 Panel Response and Progress

**Bloom-Level-Aware Faithfulness for Personalized LLM Explanations**
J26-DS-353, Amarasinghe S A R U (IT23216778)

Written for: the PP1 presentation (talking points plus slide-ready text). Status as of 2026-10-20.

---

## 1. The panel comment

> "Need to enhance the research contribution rather than simply building a product. It is better to suggest a way to upscale the cognitive level of the student over the course of time."

### What we understood

- A working explanation generator with a verifier is an **engineering result**. It is not enough on its own as research.
- As first proposed, C4 checked cognitive appropriateness as a **snapshot**: is this explanation at or below the learner's level *right now*? Matching the learner's level keeps the learner where they are.
- The panel wants a **trajectory**: does C4 help the learner reach higher cognitive levels (Bloom's taxonomy) across repeated use, and can we show it?

### Our answer in one sentence

> C4 now treats cognitive appropriateness as a **trajectory, not a snapshot**: it verifies that each explanation is faithful *and* targets the learner's **next** Bloom level, records what the learner demonstrates, and we test whether this raises the demonstrated level across sessions, including where it does not help.

---

## 2. The revised research contribution

| Before (snapshot) | After (trajectory) |
|---|---|
| Appropriate = not above the learner's current Bloom level | Appropriate = at the learner's **next** Bloom level (zone of proximal development) on concepts whose prerequisites are mastered |
| One level violation: `BLOOM_MISMATCH` (too high) | Two: `BLOOM_MISMATCH` (too high) and **`BLOOM_STAGNATION`** (no task at the target level) |
| Verification is a filter | Verification is a **progression mechanism** |
| Learner state: mastery, uncertainty, misconceptions | Adds a per-concept **demonstrated Bloom level** with history |
| One explanation | A **sequence of sessions** with faded support |

### The mechanism (implemented)

1. **Demonstrated level** per concept (1 Remember to 6 Create), updated from check-question answers.
2. **Target level** = demonstrated + 1 when every prerequisite is mastered; otherwise consolidate at the demonstrated level; retry with full support after a failed stretch.
3. **Verification at the target level**: content above it is a `BLOOM_MISMATCH`; an explanation with no check question at it is a `BLOOM_STAGNATION`, repaired by adding a "Check yourself" section.
4. **Contingent scaffolding**: full support at the start and after a failure, partial after one pass, minimal after two.
5. **Closed loop**: the learner's answer updates the demonstrated level, which sets the next target.

### Research questions (extending the proposal's RQ1 to RQ3)

- **RQ4a.** Does level-targeted verification and repair keep explanations factually faithful while ensuring a check question at the learner's target level, compared with unverified and matched-level (static) explanation?
- **RQ4b.** Over several sessions, does targeting the next Bloom level raise the demonstrated level more than matched-level or unverified explanation, and under which assumptions about learners does it fail to?

---

## 3. What was implemented in response (all on the `c4` branch, tested)

| Piece | Where |
|---|---|
| Progression policy: demonstrated level, target level, scaffolding, demotion | `c4/progression.py` |
| Bloom record in the learner state, validated by the service | `c4/data/learner_state.json`, `c4/service.py` |
| Progressive mode, `BLOOM_STAGNATION`, task claims, grounded questions and hints, report schema 1.2 | `c4/pipeline.py`, `c4/grounding.py` |
| Scaffold fading and target-level check questions in the draft | `c4/explainer.py` |
| Bloom estimator (V1 and task-aware V2) and a 90-item labelled set | `c4/bloom.py`, `c4/data/bloom_items.json` |
| Seeded multi-session simulated-learner experiment with paired statistics | `c4/simulation.py`, `c4/metrics.py` |
| Reproducible results | `scripts/run_c4_progression.py`, `c4/results/PROGRESSION.md` |
| `/api/session`, `/api/answer`, Progression tab, evidence in the Evaluation tab | `c4/server.py`, `c4/service.py`, `c4/web/` |
| Human pilot protocol (not run) | `docs/PILOT_STUDY.md` |
| Proposal, guidelines, plan, WBS, log updated | `docs/` |

160 automated tests pass. The earlier results (stress test, natural set) are unchanged in static mode.

---

## 4. Results

### RQ4a: faithful and at the target level (84 runs on the stress corpus)

| Text measured | Question at target level | Runs with a violation | Hallucination | Cognitive mismatch |
|---|---|---|---|---|
| Unverified explanation | 0% | 84 / 84 | 25.0% | 29.8% |
| Static C4 (current) | 0% | 0 / 84 | 0.0% | 0.0% |
| **Progressive C4** | **100%** | **0 / 84** | **0.0%** | **0.0%** |

Same-verifier caveat: this shows the repair does what it is specified to do, not independent accuracy. The unverified text and static C4 never contain a check question, so that gap is expected by construction.

### RQ4b: simulated learners (300 learners, 8 sessions, seeded and paired)

Progressive C4 minus current C4, capability gain in Bloom levels:

| Learner model | Difference (95% bootstrap interval) | Cohen's dz | What it tells us |
|---|---|---|---|
| ZPD (design hypothesis) | +0.36 (0.29 to 0.43) | 0.59 | Progression helps |
| Flat control | 0.00 | none | Ties exactly: explanation level does not matter |
| Matched control | +0.02 (-0.05 to 0.09) | 0.03 | No advantage |

What the full results say (`c4/results/PROGRESSION.md`):

- **The stretch is the active ingredient**: dropping it loses +1.12 levels. **Contingent fading adds nothing** in this learner model (-0.02, within noise).
- **It does not reach level 3 sooner** (0.07 sessions saved, interval -0.11 to 0.23); it raises the level reached later.
- **It needs enough sessions**: about zero at 4 sessions, +0.36 at 8, +0.90 at 12.
- **If stretching does not help learners** (matched control), it is no better at 8 sessions and worse at 12 (-0.29).
- The policy starts every unseen concept at Remember, so learners who start high lose early sessions.

### Bloom-level estimator (needed because the whole contribution rests on it)

| Split | V1 (original) | V2 (task-aware) |
|---|---|---|
| Dev (36 items; used to extend the lexicon) | 52.8% | 97.2% |
| Test (36 items; scored once after freezing) | 52.8% | 100% |
| Hard (18 indirectly phrased items; never tuned on) | 16.7% | 16.7% |

---

## 5. Honest limitations (say these before the panel does)

- **The progression results are simulated.** The ZPD model partly returns its own assumption, which is why the flat and matched controls are reported. All learner-model parameters are pilot values, not fitted to data. The results support the design and its limits, **not a claim about real students**.
- **The human pilot has not been run.** The protocol is written ([docs/PILOT_STUDY.md](docs/PILOT_STUDY.md)); it needs SLIIT ethics approval first and is exploratory (18 to 24 learners).
- **The Bloom estimator is a verb-cue matcher.** One annotator labelled the 90 items (no Cohen's kappa); 100% on the test split reflects in-vocabulary coverage, and 16.7% on indirectly phrased items shows its limit. A second annotator and a learned classifier are needed.
- Earlier limitations still hold: recipe-built stress labels, post-repair rates from the same verifier, rule-based factual matching, fixture C1/C2/C3 inputs, and the GPT-4o generator not yet implemented (Qwen via Ollama is the temporary stand-in).
- The `bloom` learner-state field is a C4 extension that C2 does not provide yet; the check questions are generic templates.

---

## 6. Status and next steps

| Item | Status |
|---|---|
| Reframe as trajectory; RQ4a, RQ4b | Done (proposal updated) |
| Policy, learner Bloom state, target-level verification, stagnation, scaffolding, check questions | Implemented and tested |
| Bloom estimator evaluation | Done on one annotator's labels |
| Simulated multi-session experiment with controls | Done |
| Workbench Progression tab and evidence | Done |
| Human pilot protocol | Written; not run |
| Second annotator, kappa, learned Bloom classifier | Next |
| Agree the Bloom field with C2; placement check; concept-specific questions | Next |
| Ethics approval and the human pilot | Next (after approval) |
| GPT-4o generator (Qwen via Ollama used meanwhile); NLI factual matching; real C1 to C3 integration | Outstanding |

---

## 7. Slide-ready content

Each member presents two slides.

### Slide 1: Panel feedback and our response (snapshot to trajectory)

- **Feedback:** strengthen the research contribution; show how the student's cognitive level rises over time.
- **Response:** appropriateness becomes a trajectory. C4 verifies faithfulness *and* targets the learner's next Bloom level.
- **RQ4a:** faithful and at the target level, versus unverified and static C4?
- **RQ4b:** faster progression across sessions, versus matched-level and unverified, and when not?

| Snapshot (before) | Trajectory (now) |
|---|---|
| Match the current level | Target current level + 1 |
| Violation: too high | Violations: too high **and** no task at the target |
| Filters bad explanations | Moves the learner forward, support fades |

```text
check answer -> demonstrated level -> target level (+1 if prerequisites mastered)
   -> verified explanation + check question at the target level (support fades with passes)
   -> next session
```

Drafts come only from a language model. **Qwen (via Ollama) is the temporary stand-in for the planned GPT-4o generator**; the verifier and policy are generator-independent, so switching is a configuration change, but the numbers here were not produced with GPT-4o.

### Slide 2: Results, limitations and next steps

- RQ4a: question at target level 0% → **100%**, 0 violations, 0 unresolved (84 runs).
- RQ4b (simulated): **+0.36** capability levels (interval 0.29 to 0.43) under the ZPD model; **no gain** under the flat and matched controls; needs about 8 or more sessions. The stretch is the active ingredient; fading adds nothing in this model.
- **Limitations:** simulated learners are assumptions, not students; Bloom labels from one annotator; estimator misses indirect phrasing; generator is Qwen, not yet GPT-4o.
- **Next:** second annotator and classifier, C2 agreement, GPT-4o generator, ethics approval and the human pilot.

### Demo flow (live, in the workbench)

1. Progression tab, "All prerequisites mastered" preset: start a session. Show the target one level above the demonstrated level, the hints and the check question.
2. Answer well twice: the target rises and the support fades.
3. Answer "Not yet" once: the policy retries the level with full support.
4. Lower a prerequisite below 0.7 in the left panel: the policy consolidates instead of advancing.
5. Evaluation tab: RQ4a table, RQ4b chart with the learner-model switch (ZPD, flat, matched).

### Likely questions and short answers

- **"Is this just a product?"** The product is the vehicle. The contribution is level-targeted verification (stagnation as a violation) and a progression policy, evaluated across sessions against baselines, with the cases where it does not help reported.
- **"How do you know the level went up?"** In simulation we read the hidden capability; with students we score answers by Bloom level, blind, with two raters. The human pilot is the validation and is not run yet.
- **"Isn't your simulation rigged to favour you?"** It partly returns its assumptions, which is why we run a flat control (exact tie) and a matched control (no advantage, worse at 12 sessions). We state it is not evidence about students.
- **"Why doesn't it reach level 3 faster?"** The policy moves at most one level per session, and a new concept starts at Remember, so early sessions are spent climbing; the benefit appears in the level reached later.
- **"Why did fading not help?"** In our learner model there is no dependence effect for fading to protect against, so it cannot help; a real effect would only show in the pilot.
- **"Can you trust the Bloom level estimate?"** Partly: 100% on in-vocabulary items, 16.7% on indirectly phrased ones, one annotator. A second annotator and a learned classifier are next.
- **"Are your numbers real?"** The RQ4a and earlier numbers come from recipe-built labels and the same verifier; the RQ4b numbers come from simulation. We say so each time.
