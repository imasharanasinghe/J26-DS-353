# NEW: Teach-Back Assessment and Graph Auditing for Component 4

**Branch `c4-addition`. J26-DS-353, Component 4 (Amarasinghe S A R U, IT23216778). Written 23 November 2026.**

This file replaces two drafts that lived on branch `c4` (`NEW1.md`, the technical proposal, and `PROPOSAL.md`, the plain-English version for the group). It keeps their content, adds a second literature pass done on 23 November, and records what has now been **built and measured** on this branch.

**Status.** The supervisor has not approved this scope. Everything that was built runs on fixtures and simulated cohorts. **No real student has been tested, so nothing here says anything about real students.** Where a result looks good, section 9 says why that may be an artefact of the simulation.

---

## 0. Summary

| | |
|---|---|
| **The idea** | A knowledge-restricted AI "novice" reads only a student's written explanation, then takes a hidden test whose answers come from the verified knowledge graph. The novice's score, per concept and Bloom level, is evidence of what the student understood. A Graph Auditor checks the graph's prerequisite edges against what students actually do and feeds the result back into C4's verifier. |
| **Built (code, tests)** | Hidden test bank keyed to the graph; two novices (deterministic lexical control, Ollama LLM); the instrument gate (leakage, discrimination, reliability, fairness, depth); the teach-back pipeline with a C2 evidence message; the Graph Auditor with planted-error harness; the audit loop into the verifier; a block-plan simulation; the help box; a layered, versioned graph with lecturer-gated proposals; three workbench tabs; three experiment scripts. |
| **Main findings so far** | (1) The lexical control has no leakage and no run-to-run noise, ranks content correctly, but is blind to word order and paraphrase and is hurt by weaker English. (2) The auditor finds planted edge errors with precision 0.96 to 1.00 and recall about 0.6 to 0.7, and is far better than a raw co-occurrence baseline; a simple order-only baseline does as well on this generator because the generator builds in the curriculum-order confound. (3) Feeding the audit into the verifier cuts wrong "review first" detours from 0.36 to about 0.10 per (student, target) pair in simulation. (4) The evidence-driven plan did **not** beat a uniform plan on "nobody under the floor"; it lowered the spread slightly and left more students with at least one concept just under the floor. (5) A prompted `qwen3:4b` novice **fails** the gate: it leaks (0.385 on concepts it was never taught, chance 0.25), cannot tell half an explanation from a full one, and resists the planted misconceptions (0.71 on an explanation full of them). Counting only answers traceable to the student's text restores discrimination (section 9.1). |
| **Not done** | Human validity and fairness study (needs SLIIT ethics approval); real-data audit (ASSISTments or SLIIT data); calibration of item difficulty; Mode 2 (interactive teaching); agreement with C1, C2 and C3 on the interfaces. |
| **Risk to the claim** | The Waterloo group has publicly planned the same kind of exam since early 2025 (section 11). The contribution has to be framed as the **validation protocol and the graph integration**, not the idea. |

---

## 1. Why the scope changed

The PP1 panel (22 October 2026) said the four components together amounted to roughly one normal final-year component and asked each of us for something new and deeper. C4 before this branch (see `C4BEFORE.md`) is a verifier: it checks an LLM explanation against the knowledge graph (C1) and the learner's state (C2) and repairs what fails. That is mostly engineering, and every verdict it gives is only as good as the graph and the mastery estimates behind it. Two gaps were visible:

- Nothing checks the graph against real student behaviour.
- Nothing measures what a student understands except right/wrong quiz answers.

## 2. The idea in plain words

Follow one student through a semester.

1. **Start.** A short diagnostic quiz, plus last semester's marks (a weak prior only), gives a first guess of what the student knows.
2. **Plan.** Lectures are the same for everyone. Practice, notes and stretch tasks differ. The goal is not "every student equal" but: **every student reaches a minimum mastery floor on every concept in the block before the exam, and the spread between students shrinks.**
3. **Help.** Each module page has a "Do you need help with this concept?" box, answered from the graph and checked by C4's verifier. The student attempts first, then gets hints, then the explanation. Asking for help is never counted as mastery.
4. **Teach-back exam.** In the mid or lab exam, for each lecture the student has about 10 minutes: "Explain what X is in your own words. Your answer must include Y and Z." An AI novice that knows only that text takes a hidden test. A student who explains badly or wrongly produces a novice that fails.
5. **Update.** The result updates what is known about the student per concept and Bloom level, and the next plan is rebuilt.
6. **Graph checking.** A Graph Auditor asks whether the graph's prerequisite structure matches what students do, and proposes fixes. A lecturer approves or rejects each.

```text
   C1 graph (base -> lecturer overlay -> audited edge confidence)
        |                      |                       |
        v                      v                       v
 diagnostic + marks -> C2: mastery[concept][bloom] <- evidence: practice, quizzes,
        |                                                      TEACH-BACK EXAM
        v
 planner (per student, per 7-week block) -> practice, notes, stretch
        |
 help box -> LLM draft -> C4 verifier -> explanation shown to the student

 Teach-back:  student text -> coverage -> claim check (true vs graph?) ->
              knowledge-restricted novice -> hidden Bloom-tagged test -> score per (concept, level) -> C2
 Auditor:     graph edges + student evidence -> status per edge -> proposals -> lecturer -> verifier (edge_confidence)
```

**Fit with the project title** ("Pedagogy-Typed Knowledge Graphs for Verified Personalized Learning Path Generation"): the audit fits strongly (it tests the pedagogy edge types against data and is the "verified" part aimed at the graph itself); the teach-back exam fits moderately to strongly (the graph is the answer key and every item is Bloom-tagged); the help box is C4 as it is; the plan and the dynamic graph are moderate (they are C3's and C1's areas). The project is a **middleware**, not an LMS; the LMS is only where it would run.

## 3. Research questions and where each stands

| RQ | Question | Status after this branch |
|---|---|---|
| **RQ1 validity** | Does the novice's score track real understanding (conventional exam, human grading), and does it add information beyond the verifier and a plain quiz? | Only the synthetic part is done (known-gap explanations are ranked correctly by the lexical control). Real validity needs the pilot. |
| **RQ2 reliability and leakage** | How stable is the score across runs, and how much does the novice know before reading anything? | Lexical control: zero by construction. LLM novice: measured, section 9.1. |
| **RQ3 fairness and gaming** | Is the score biased by writing ability, and how easily is it gamed? | Style-perturbation gap measured on synthetic text (section 9.1). Gaming is design-only. |
| **RQ4 Bloom** | Do per-level scores behave like levels, or does the strict ladder fail? | The Bloom audit exists and is tested on planted mislabels; no real item data yet. |
| **RQ5 graph audit** | How well does the auditor recover planted graph errors as a function of data size, and do audited edges cut wrong "review first" instructions and missed prerequisites? | Done in simulation (section 9.2 and 9.3). Real data not done. |
| **RQ6 planning** | Does evidence-driven allocation reduce the share under the floor and the spread versus a uniform plan? | Done in simulation: mixed result (section 9.4). |

Formulation of the central question (a **question, not a result**): *we evaluate whether an LLM novice's test score is a valid, reliable and fair indirect indicator of the teaching student's mastery, and give a validation protocol against standard human post-tests.* Do not write "validated" until the data exist.

---

## 4. Design of the teach-back exam (Mode 1, written)

### 4.1 Pipeline

1. **Prompt.** `teachback.make_prompt`: "Explain what X is in your own words. Your answer must include: Y, Z." The required terms are the concept's direct graph prerequisites.
2. **Coverage.** Are the required graph concepts mentioned (longest-match concept detection, as in the verifier)?
3. **Claim check.** The existing C4 factual check (rule-based, content-word similarity against graph facts and known-false statements) labels each sentence `ENTAILED`, `CONTRADICTED` or `UNSUPPORTED`. A contradiction of a known-false statement is the diagnostic signal ("a heap is always fully sorted").
4. **Novice test.** A knowledge-restricted novice sees only the student's text and answers a fixed hidden test (multiple choice), or says "I don't know".
5. **Evidence.** Score per (concept, Bloom level), with item count and a Wilson interval, sent to C2 as an evidence message (section 6). Level scores with fewer than 2 items are flagged `thin`.
6. **Depth check.** A correct novice answer whose required graph statements are **not** found in the student's text came from the novice's own reasoning or memory; it is discounted. (`instrument.depth`.)

### 4.2 The hidden test

- **Answer keys come from the graph**, never from an LLM's opinion. Recognition items (Bloom 1 and 2) are generated from each concept's `facts`, with the concept's `known_false` statements and other concepts' facts as distractors. Apply and Analyze items (Bloom 3 and 4) are hand-written in `c4/data/teachback_items.json`. Every option lists the graph statements a reader needs in order to derive it; for a distractor these are the false belief that would make it look right, so a student who writes a false statement pulls the novice toward the matching distractor. `NOT: <statement>` means the text must deny a known-false statement.
- **Scoring has no LLM judge.** Fixed options, answers matched to the graph. The only variance is the novice's own.
- Current bank: 24 items over 7 concepts (13 recognition, 11 Apply or Analyze). **Pilot items; difficulty is not calibrated.** Waterloo's Chrysalis study found a ceiling effect on an easy quiz, so items must be piloted and the ones that do not spread students out removed.
- Distractor quality: confusable, misconception-based distractors are a known requirement for good items ([concept-map MCQ generation, 2025](https://arxiv.org/abs/2505.02850), [confusability, 2016](https://arxiv.org/abs/1610.09935)); those authors also note LLM-written distractors still need expert validation, which is why ours are taken from the graph's `known_false` statements.

### 4.3 Mapping student task to Bloom level (a hypothesis to test, not assume)

| Student task | Novice test item | Level evidenced |
|---|---|---|
| Explain X | Define or recognise X | Remember, Understand |
| Include an example | Apply X to a new case | Apply |
| Compare X and Y | Choose and justify | Analyze |
| Mode 2: handle the novice's "why?" | Judge a flawed design | Evaluate |

Bloom is **not assumed to be a strict ladder** (section 11.5). Which levels depend on which is tested by the Bloom audit, not hard-coded.

### 4.4 The two novices

- **`LexicalNovice`**: a deterministic reference reader. It derives an option only if the text states every graph statement that option needs (with polarity: "first-in-first-out" does not state "last-in-first-out", and "not always sorted" denies "always sorted"). It cannot know anything the text does not say, so **leakage is zero by construction** and there is no run-to-run noise. It is blind to word order and paraphrase. It is a control and a lower bound, **not the candidate instrument.**
- **`OllamaNovice`**: a local LLM (default `qwen3:4b`) told to know nothing except the text and to answer `UNKNOWN` otherwise. This is the candidate instrument. Prompting alone does not remove a model's own knowledge (section 11.2), so its leakage is measured before any score is used.

### 4.5 The instrument gate (Phase 1, no humans)

If the novice fails these, stop and report that:

| Test | Question | Implementation |
|---|---|---|
| **Leakage** | With an empty text, or text about other concepts, is the score near zero (or chance)? | `instrument.leakage` |
| **Discrimination** | Are controlled explanations ranked in the expected order? Variants built from the graph: `complete`, `missing_one` (one fact sentence left out), `half`, `wrong` (first fact replaced by a known-false statement), `garbled` (words shuffled), `paraphrased`, `empty`. | `instrument.discrimination`, `synthetic.explain` |
| **Reliability** | Same text, repeated runs: how much does the score move? (Temperature 0 does not remove run-to-run variation.) | `instrument.reliability` |
| **Fairness** | Same content, weaker English (articles dropped, letters swapped) or terse concept-list input: how much does the score fall? | `instrument.fairness`, `synthetic.weaker_writer` |
| **Depth** | How much of the score traces to the student's own sentences? | `instrument.depth` |

Scores reported: proportion correct (a "don't know" counts as wrong) and a **net score** (right minus wrong/(k-1)) so a confident wrong answer is worse than an honest "don't know".

### 4.6 Still needed that cannot be built without people

- **Criterion validity**: novice score against the conventional exam and against human marking on a sample.
- **Fairness with real writers**: whether weaker English writers score lower at equal understanding, and which mitigations work (marking content not style; concept-list or diagram input).
- **Gaming**: pasting an AI-written answer measures the AI. Supervised lab setting, unseen prompts, similarity checks, a short oral follow-up on a sample.
- **Stakes**: formative first; it counts towards a grade only after validity and fairness are shown.

### 4.7 Mode 2 (later)

The novice asks questions, the student answers, then the novice takes the test. Richer (it reaches Evaluate level) but noisier, and it needs the novice to ask good questions. Not built.

---

## 5. The Graph Auditor

The graph is treated as ground truth by C4, but nobody checks it against what students do. The auditor reads the graph (C1) and student evidence (C2) and writes a report for the lecturer. **It proposes; it never edits the graph.**

### 5.1 Edge audit, for each "A is a prerequisite of B"

- **Implication**: mastering B without A should be rare after allowing for guess and slip. Rate `v = P(not A | B)` with a Wilson interval.
- **Lift, controlling for ability**: success on B is more likely when A is mastered, *after stratifying by overall ability* (Mantel-Haenszel odds ratio over ability strata, bootstrap interval). Without this control any two concepts correlate, because strong students master everything. (A raw odds ratio is used as the co-occurrence baseline.)
- **Order**: among students who mastered both, A observed no later than B. Reported, not decisive, because the course is taught in prerequisite order.

Statuses (with the numbers behind each in `AuditConfig`): **Supported** (upper end of `v` at most 0.30 and odds-ratio lower bound at least 2), **Reversed** (mastering A without B is rare, B without A is common, and the two are associated), **Unsupported** (no association beyond ability and `v` clearly above the allowance, or `v` clearly above 0.30 whatever the association), **Contested** (everything else, including fewer than 40 students, or A or B mastered by under 5% or over 95%, which cannot be tested), and **Missing (candidate)** for unlinked pairs with a strong one-way dependency that no existing path already implies.

### 5.2 Other pedagogy edge types

| Type | What is tested |
|---|---|
| bloom-level | Items labelled higher should be empirically harder; disagreeing items are flagged. A disagreement is reported as a finding about the **label**, because Bloom is not a strict ladder. Bloom labels are tags on items and on a student's level within a concept, **not** prerequisite edges between concepts. |
| cognitive-load (prerequisite depth) | Does computed load predict how hard students actually find a concept? (rank correlation) |
| common-misconception-of | If the data records which wrong option was chosen, is the misconception really common (Wilson interval above chance)? Skipped if the data has no wrong-option information. |

### 5.3 Loop back into C4

`C4Pipeline(kg, edge_confidence=report["edge_confidence"])`: an **Unsupported** or **Reversed** direct prerequisite edge no longer produces `UNMASTERED_PREREQUISITE` or a "review X first" line; a **Contested** edge makes the claim `INCONCLUSIVE` instead of a hard violation; the report gains an `edge_confidence` block (`c4-report/1.3`). With no argument nothing changes.

### 5.4 Traps, stated honestly

- Students meet prerequisites first because the course is in that order, so order and implication tests can look like dependencies when they are only the timetable. Mitigations short of causal inference: control for ability (done), compare offerings that teach in a different order (not done), and test the method on planted errors (done). Instrumental-variable or counterfactual modelling is out of scope.
- ASSISTments is not Data Structures, and its skill tags are flat (no prerequisite ground truth). Auditing the DSA graph needs DSA performance data and ethics approval.
- Small classes give wide intervals: many edges will honestly be Contested.

---

## 6. Mastery, Bloom and the interfaces

State: `mastery[student][concept][bloom level]`, a probability and an uncertainty. A matrix, not one number, because the Bloom claim has to be testable. Mastered at level L: probability at least 0.70 and uncertainty at most 0.25 (as C4 uses today). Target Bloom level = demonstrated level + 1 when direct prerequisites are mastered (`c4/progression.py`, unchanged).

| Evidence | Weight | Note |
|---|---|---|
| Teach-back exam | High, once validated (provisional until then) | Per level |
| Checkpoint quiz | High | |
| Practice attempts | Medium | Lower if hints were used |
| Help-box use | None | Signal for the lecturer only |
| Last semester's marks | Prior only | Decays fast; never a label on a student |

**C4 to C2, evidence (implemented, `c4-evidence/1.0`)**, one message per (student, concept, Bloom level):

```json
{"schema": "c4-evidence/1.0", "student": "S001", "concept": "heap", "bloom": 3, "score": 0.5, "items": 2,
 "ci95": [0.09, 0.91], "thin": false, "source": "teachback_exam", "weight": "provisional",
 "graph_version": "2026-w07-v3"}
```

**C4 to C1, audit proposal (implemented in `auditor.proposals`)**:

```json
{"edge": ["binary_tree", "heap"], "status": "Contested", "evidence": "evidence is mixed or the intervals are wide",
 "proposal": "keep, lower confidence", "needs_lecturer": true}
```

**C1 to everyone, graph export (requested, not agreed)**: JSON with stable concept ids, the four edge types, per-concept `facts` and `known_false` statements, per-edge `source`, `status`, `confidence`, and a `graph_version`.

---

## 7. The demo parts: block plan, help box, layered graph

### 7.1 Block plan (`planner.py`, simulation)

For each 7-week block, gap = target mastery minus current estimate; spend the weekly budget in proportion to gap, weighted by how many later concepts depend on the concept and by whether its prerequisites look ready; re-plan from weekly checks; half the budget is a baseline nobody drops below. Compared against a **uniform** plan and a **tiered** plan (last semester's marks), all with the same total budget. This is C3's area; here it is a simulation inside C4, to be shown as such unless C3 wants it.

### 7.2 Help box (`helpbox.py`)

Attempt first; then up to three hints of growing strength (a prerequisite nudge, a prerequisite fact, a concept fact); then the explanation, which is the concept's graph facts run through the C4 pipeline for this learner (so an unmastered prerequisite is repaired into "review X first"). The explanation is refused until an attempt exists, so the box is not an answer lookup. A help request returns `mastery_evidence: null`; an attempt returns an evidence message with weight `medium`, or `low` if hints were used. `HelpLog` gives the lecturer a confusion map per concept.

### 7.3 Layered, versioned graph (`layers.py`)

"Dynamic" means layers, versions and gated proposals, not a graph that rewrites itself. Base graph (department level) + lecturer overlay (add or hide concepts, add or remove edges, emphasis, terminology) + audited edge confidence. Every automatic change (audit result, weekly transcript diff) is a **proposal**; a named lecturer approves or rejects; approved proposals become a new version with a changelog entry; the graph is **frozen** per block (commits are refused while frozen); a commit that would create a prerequisite cycle is refused and keeps the old version. Mastery migrates across concept changes: a split gives the children the parent's mastery with more uncertainty; a merge takes the lower mastery and the larger uncertainty; a new edge triggers a re-check, not a demotion.

---

## 8. What is built on this branch

| Part | Modules | Tests |
|---|---|---|
| Test bank, novices | `c4/testbank.py`, `c4/novice.py`, `c4/data/teachback_items.json` | `test_novice.py` |
| Synthetic explanations, instrument gate | `c4/synthetic.py`, `c4/instrument.py` | `test_instrument.py` |
| Teach-back pipeline | `c4/teachback.py` (+ `C4Pipeline.factual_check`) | `test_teachback.py` |
| Graph Auditor | `c4/auditor.py`, `c4/audit_sim.py` | `test_auditor.py` |
| Audit into the verifier, downstream study | `c4/pipeline.py` (`edge_confidence`), `c4/audit_loop.py` | `test_audit_loop.py` |
| Block plan | `c4/planner.py` | `test_planner.py` |
| Help box | `c4/helpbox.py` | `test_helpbox.py` |
| Layered graph | `c4/layers.py` | `test_layers.py` |
| API and workbench tabs | `c4/service.py`, `c4/server.py`, `c4/web/` | `test_addition_api.py`, `test_frontend.py` |
| Experiments | `scripts/run_c4_teachback.py`, `run_c4_audit.py`, `run_c4_planner.py` | |

Run: `python3 -m pytest -q` (all tests, no model needed); `python3 scripts/run_c4_teachback.py [--llm]`; `python3 scripts/run_c4_audit.py`; `python3 scripts/run_c4_planner.py`; `python3 scripts/run_c4_server.py --open` (tabs **Teach-back**, **Graph audit**, **Help box**). Results land in `c4/results/` (`TEACHBACK.md`, `AUDIT.md`, `PLANNER.md` and JSON).

---

## 9. Results so far (simulation and synthetic text only)

### 9.1 The novice instrument

**Lexical control** (24 items; 10 seeds per variant; synthetic explanations of all 7 concepts):

| Variant | Score | Net |
|---|---|---|
| complete | 1.000 | 1.000 |
| missing one fact sentence | 0.942 | 0.942 |
| half (one fact per concept) | 0.542 | 0.542 |
| wrong (misconception in first fact) | 0.000 | -0.153 |
| garbled (words shuffled) | 1.000 | 1.000 |
| paraphrased | 0.625 | 0.625 |
| empty | 0.000 | 0.000 |

- Leakage: empty text 0.000; text about other concepts scored on held-out concepts 0.000 (chance if forced to guess 0.25). Zero by construction.
- Reliability: run-to-run sd 0.0, item agreement 1.0 (deterministic).
- Discrimination: complete > missing one > half > empty, and complete and missing-one both above wrong (net), all with confidence intervals excluding zero. **Fails** `complete > garbled` (it cannot see word order) and `paraphrased ~ complete` (0.375 lower).
- Fairness: with 30% of eligible tokens altered (articles dropped, letters swapped) the score falls by 0.14 (95% CI 0.08 to 0.20); at 60%, by 0.32 (0.27 to 0.36). The terse concept-list input loses only 0.04. So a **lexical reader is style-sensitive**: that is the kind of bias the fairness study has to look for in an LLM novice too.
- Reading: the gate correctly reports `passed: False`. The control tells us the pipeline is wired correctly and gives the floor an LLM novice must beat on paraphrase and word order. It says nothing about the LLM.

**LLM novice** (`qwen3:4b` through Ollama, JSON-constrained reply, "know nothing except the text, answer UNKNOWN otherwise"; 24 items; **only 2 seeds per variant and 4 repeat runs, so the intervals are degenerate; treat as a first look, not a measurement**):

| Variant | Lexical control | LLM novice |
|---|---|---|
| complete | 1.000 | 1.000 |
| missing one fact sentence | 0.942 | 0.958 |
| half (one fact per concept) | 0.542 | **0.958** |
| wrong (misconception in first fact) | 0.000 | **0.708** |
| garbled | 1.000 | 0.979 |
| paraphrased | 0.625 | 0.917 |
| empty | 0.000 | 0.000 |

- **It leaks.** With an empty text it abstains on everything (score 0.000), but given text about *other* concepts it scores **0.385** on held-out concepts (chance if forced to guess 0.25). It uses its own knowledge as soon as it has some text to anchor on. The gate reports `leaks: True`.
- **It cannot tell half an explanation from a full one** (0.958 versus 0.958): with half the facts it answers the rest from its own knowledge or reasoning.
- **It resists wrong statements.** An explanation containing misconceptions scored 0.708, so the novice mostly did *not* adopt the false claims. This matches the misleading-context result in section 11.2 and is the failure that hides exactly the errors the exam is for.
- **It is style-robust and paraphrase-robust** (weaker-writer gap 0.00, concept-list gap 0.00, paraphrased 0.917), which the lexical control is not. But that robustness is mostly the same leak: a reader that ignores the text cannot be hurt by how the text is written.
- Reliability: no variation in 4 runs at temperature 0.7 (sd 0.0, item agreement 1.0). With a JSON-constrained, 40-token reply the answers are highly peaked; do not read this as proof of reliability under other prompts or models.
- **The depth check is what rescues it.** Counting a correct answer only when every graph statement the item requires is stated in the student's text (`instrument.depth`):

| Variant | Correct | Traced to the text | Untraced | Raw | Depth-adjusted |
|---|---|---|---|---|---|
| complete | 24 | 24 | 0 | 1.000 | 1.000 |
| half | 23 | 13 | 10 | 0.958 | **0.542** |
| wrong | 17 | 10 | 7 | 0.708 | **0.417** |
| empty | 0 | 0 | 0 | 0.000 | 0.000 |

  After the discount the LLM novice's "half" score (0.542) equals the lexical control's. The "wrong" score (0.417) is still above the control's 0.000 because the true facts left in that text are legitimately traced. The depth check uses the lexical statement matcher, so it would also penalise a genuine paraphrase; that is a cost of the discount.
- **Reading.** A prompted 4B model is not a usable novice as it stands: it fails leakage and discrimination on its own and only passes after the depth discount, which relies on the lexical matcher. **This is the negative result the proposal said to expect, and it is useful.** The plan stays: try retrieval-restricted answering, a stronger or weaker model, and unlearning (section 11.2), and rerun the gate at 10 or more seeds. Whether the exam is worth building on an LLM novice at all, rather than on the deterministic reader plus an LLM only for paraphrase, is now an open design question.

### 9.2 Graph Auditor, planted-error test (30-concept C3 graph, 51 true edges)

15% of edges deleted, 15% reversed, as many spurious ones added; cohorts simulated from the true graph (ability trait, guess 0.2, slip 0.1, 3% of students skip a prerequisite); mean over 5 seeds.

| Students | Precision | Recall | F1 | Co-occurrence baseline F1 | Order-only baseline F1 | Clean edges flagged | Clean edges Contested | Deleted edges recovered (recall) |
|---|---|---|---|---|---|---|---|---|
| 60 | 0.96 | 0.59 | 0.72 | 0.11 | 0.86 | 0.4 of 35 | 77% | 0.23 |
| 120 | 1.00 | 0.61 | 0.76 | 0.17 | 0.86 | 0.0 | 46% | 0.42 |
| 300 | 1.00 | 0.70 | 0.82 | 0.12 | 0.86 | 0.0 | 21% | 0.45 |
| 600 | 1.00 | 0.70 | 0.82 | 0.12 | 0.87 | 0.0 | 8% | 0.55 |

Reading it honestly:

- Strict flags (Reversed or Unsupported) are almost never wrong, and the raw co-occurrence baseline is useless because ability confounds everything. That is the case for controlling for ability.
- **The order-only baseline looks better than ours (F1 0.86) because this generator makes learning order follow prerequisite depth.** That is exactly the curriculum-order confound of section 5.4. A strong order baseline in simulation does not show order evidence survives a real timetable; our implication and adjusted-lift tests do not depend on order.
- Recall plateaus near 0.7: spurious edges between concepts that share prerequisites keep some association and end up Contested rather than Unsupported. That is the intended behaviour (evidence, not proof). Below about 120 students most edges are Contested.
- Missing-edge recovery is modest (recall 0.23 to 0.55, precision 0.17 to 0.43) but far above a top-k raw-odds-ratio baseline that is told how many edges were deleted.

### 9.3 E3: does the audit cut wrong "review first" detours?

Per (student, target) pair, 5 seeds. "Audit" drops Unsupported and Reversed edges, as the verifier now does. "Audit + approved" also applies the correct proposals; the lecturer is an oracle, so it is an upper bound.

| Students | Condition | Wrong detours | Missed prerequisites |
|---|---|---|---|
| 300 | no audit | 0.361 | 0.282 |
| 300 | audit | 0.098 | 0.282 |
| 300 | audit + approved | 0.098 | 0.117 |
| 600 | no audit | 0.360 | 0.282 |
| 600 | audit | 0.100 | 0.282 |
| 600 | audit + approved | 0.100 | 0.101 |

The audit alone removes about 70% of wrong detours but cannot recover deleted edges; missed prerequisites fall only when a lecturer approves the correct additions and flips.

### 9.4 Block plan (7 weeks, 200 students, 8 seeds starting at 100, floor 0.6)

| Budget (h/week) | Metric | Uniform | Tiered | Evidence |
|---|---|---|---|---|
| 8 | Students with any concept below floor | 0.227 | 0.221 | 0.268 |
| 8 | Concepts below floor (per student) | 0.179 | 0.170 | 0.174 |
| 8 | Exam spread (sd) | 0.144 | 0.139 | 0.136 |

Evidence minus uniform at 8 h: spread -0.0085 (95% CI -0.0106 to -0.0066); share of students with any concept under the floor **+0.041** (0.036 to 0.046). At 6 and 12 h/week the picture is the same or weaker. **The "nobody under the floor" goal is not met by this plan in this simulation**: with noisy weekly checks, spreading practice by gap shrinks the spread slightly and leaves more students with at least one concept just under the floor. The tiered plan (marks-based) is no better than uniform because marks only weakly predict learning rate in this model. The plan was tuned on seeds 0 to 5 (guess-corrected estimates, a baseline share, smoothing); the table uses fresh seeds. The student model is an assumption; nothing here shows the plan helps real students.

---

## 10. Mistakes found and corrected while building it

Kept here because a reader should be able to see how much of the early output was wrong.

| What | How found | Correction |
|---|---|---|
| Synthetic "missing one fact per concept" variant equalled the "half" variant (both left one fact per concept), so "missing > half" was meaningless | Instrument gate gave `missing_one < half` | `missing_one` now drops a single fact sentence |
| Denial of a known-false statement containing "never" became a double negation that the novice read as the original false claim, so complete explanations of recursion failed | Complete variant scored 0.83, not 1.0 | Such denials are made affirmative ("always") |
| `c4.metrics.wilson_interval` returns **percent**; the auditor treated it as a fraction, so every interval was 100 times too wide and almost every edge came out Contested | 91% of clean edges Contested in the first run | Converted in the auditor; same fix in the evidence message |
| Supported required only an odds-ratio lower bound above 1, so a weak edge was Supported; a strong implication violation left spurious edges Contested | Planted-error run | Supported needs a lower bound of at least 2; a clear implication violation is Unsupported |
| The "concept list" input was not terse (it restated full sentences) | Concept-list score exceeded complete prose | Subject, article and linking verb are removed |
| The planner compared raw quiz scores (guess floor 0.2) with a mastery-scale floor, so the evidence plan was biased against itself | Evidence plan was worst on every metric | Guess-corrected estimates, smoothing over the last three checks, a baseline share (the proposal's "nobody gets less than the baseline") |
| The plan was tuned on seeds 0 to 5 | Own review | Results reported on seeds 100 and up |
| The first API commit forgot to write the service file back | New tests failed on a missing method | Redone; all tests pass |

Not corrected, only recorded: the evidence plan still loses on "any concept below floor". I stopped tuning at that point rather than adjust the simulator until the plan won.

---

## 11. Prior work

**How this was checked.** Pass 1 (29 October 2026): web search, a NotebookLM check, and full or abstract reads of the Waterloo page, Chrysalis, Kucharavy et al. and Jin et al. Pass 2 (23 November 2026): searches on teachable agents with LLM assessment, leakage and knowledge restriction, prerequisite validation, Bloom, mastery learning and scoring fairness, followed by abstract fetches of the papers marked **A** below. Marks: **F** = read in full in pass 1; **A** = abstract page opened; **S** = seen only as a search result or snippet (not verified; check before citing); **B** = blocked, could not open. No meta-analysis of the protege effect was found. NotebookLM's verdicts ("Supported" for N1 to N4) rested on "not covered by the sources", which is absence of evidence in a small notebook, and it merged two papers; treat its list as leads.

### 11.1 Learning by teaching and teachable agents

- **Waterloo, "Learning by Teaching a Large Language Model"** (Poupart and Grossmann; Feb to Dec 2025; **A**, reopened 23 Nov): the page plans "Creation of a new evaluation method: exam to test the concepts learned by an LLM companion", "indicative of the concepts mastered by the student who taught the LLM". The page says the first iteration of the companion, Chrysalis, was completed in Winter 2025 and lists two course trials and two articles as planned. **No trial results or publications are reported on it.** [Project page](https://uwaterloo.ca/teaching-incubator/projects/learning-teaching-large-language-model). A Waterloo student-newspaper article (**S**, page blocked by a bot check) is reported by a search summary to say students' knowledge is judged by how well the LLM performs on a quiz afterward; open it by hand before relying on it: [Imprint, "Meet Chrysalis"](https://uwimprint.ca/meet-chrysalis-waterloos-new-ai-student-that-learns-from-you/).
- **Chrysalis** (Arun, Vader, Xu, McCready-Branch, Seabrook, Scholz, Crisan, Grossmann, Poupart; arXiv 2510.05271, 6 Oct 2025, v1 only, submitted to the EAAI-26 symposium, under review; **F** in pass 1, **A** in pass 2): 36 participants compared an AI tutor with a teachable-agent mode on preferences and intellectual humility. **It does not use the LLM's test score to assess the student**; student knowledge was a 20-item multiple-choice quiz taken by the humans (no difference between modes, ceiling effects, quiz too easy). [Paper](https://arxiv.org/abs/2510.05271). (A ResearchGate copy of the page contains text about a different trial; do not cite it.)
- **Quizzing the agent has a long history as a tutor-facing device**, not as validated assessment: in SimStudent/APLUS (Matsuda and colleagues) the tutor can quiz the agent at any time to see how well it learned, and the goal is to teach it well enough to pass; Betty's Brain (Biswas, Leelawong, Vanderbilt) works the same way (**S**, [APLUS follow-up study](https://par.nsf.gov/servlets/purl/10637589), [Betty's Brain, Leelawong and Biswas 2008](https://escholarship.org/content/qt5s81207k/qt5s81207k.pdf?t=op2l22)). This narrows what can be called new: the quiz exists; what has not been shown is its validity, reliability and fairness as a measure of the *teacher's* mastery.
- **Jin, Lee, Shin and Kim, "Teach AI How to Code"** (arXiv 2309.14534, CHI 2024; **A**): AlgoBo, an LLM tutee with configurable misconceptions and unawareness; 40 novices; its questions led to "knowledge-dense conversations" (effect size 0.71). Learning gain for the teacher, not assessment. [Paper](https://arxiv.org/abs/2309.14534).
- **Kucharavy, Vallez and Percia David, "LLMs Protégés"** (BEA 2025; **A**): students in an algorithms class diagnosed an LLM teachable agent prompted to make errors; they gained 0.72 points on a 1 to 6 scale; the authors project the second-midterm failure rate falling from 28% to 8% if fully adopted. The LLM does not take an exam; the outcome is the student's own midterm. [Paper](https://aclanthology.org/2025.bea-1.19/).
- **Yang, Pujara and Li, "Learning by Teaching: Engaging Students as Instructors of LLMs in CS Education"** (arXiv 2508.05979, COLM 2025; **A**): students teach an LLM to solve problems; significant improvement versus historical cohorts. A search summary claimed the LLM's performance is used as a measure; the abstract does not say so (**unresolved; read the paper**). [Paper](https://arxiv.org/abs/2508.05979).
- **Chen, Wei, Le and Zhang, teachable ChatGPT in programming** (arXiv 2412.15226; **A**): knowledge gains, self-regulated learning and self-efficacy improved; error-correction little, because the agent rarely errs. A search snippet says 41 C++ students (**S**). [Paper](https://arxiv.org/abs/2412.15226).
- **Protege effect**: [Chase, Chin, Oppezzo and Schwartz 2009](https://purl.stanford.edu/zm369yx3532) (teaching a virtual agent increased effort, most for lower achievers; **S**); a [2018 Lund poster](https://www.lucs.lu.se/fileadmin/user_upload/project/lucs/ETG-pub/etg2018-conference-AIED-poster.pdf) found a weak link between the effect and learning (**S**). Teachable-agent results overall are mixed (**S**).
- **Learning by teaching in the other direction**: TeachBench (Li et al., arXiv 2601.21375, Jan 2026; **A**) measures a *teacher LLM* by how much a student's performance improves, restricting the teacher to syllabus knowledge points to prevent leakage; EducationQ (arXiv 2504.14928; **S**) and INTERACT (arXiv 2412.11388; **S**) quiz a student LLM after instruction. These evaluate the teacher *model*, not a human teacher.
- **Self-explanation and the Feynman method**: [Learn Like Feynman bot](https://arxiv.org/abs/2506.09055) (14 participants, higher gains than passive learners; **S**); LLM-as-judge versus semantic similarity for scoring programming self-explanations (Lekshmi-Narayanan, Hassany and Brusilovsky, arXiv 2605.21614, 20 May 2026; **A**, abstract only; dataset and results not seen). [Paper](https://arxiv.org/abs/2605.21614).

### 11.2 Restricting an LLM to novice knowledge (the leakage problem)

- **Song, Guo and Lin, "Simulating Novice Students Using Machine Unlearning and Relearning in LLMs"** (arXiv 2603.26142, Mar 2026; **A**): prompt-engineered LLMs drift beyond novice level and give expert explanations; unlearning gives more novice-like responses and the agents relearn part of the removed knowledge under tutoring; Python multiple-choice questions; the abstract gives no numbers. [Paper](https://arxiv.org/abs/2603.26142).
- **Setiawan, "Prompt-Based Abstention Fails Under Misleading Context"** (arXiv 2608.22228, AACL-IJCNLP 2026; **A**): three small frozen models (3.8B to 8B); abstention is reliable when evidence is missing, but under an explicit abstention prompt the models still answered 41.6% of **misleading** questions, 63% of those wrong answers echoing the planted entity. "Prompt-based abstention asks whether context is sufficient, not whether it is correct." [Paper](https://arxiv.org/abs/2608.22228). **Why this matters here:** a novice must *adopt* a student's wrong statement for a misconception to show up as a low score. A model that resists the context with its own memory would hide exactly the errors we want to see. The `wrong` synthetic variant measures this.
- **Context-faithful prompting** (Zhou et al. 2023, arXiv 2303.11315; **S**): phrases such as "based on the given context" and abstention instructions improve faithfulness but do not remove reliance on parametric memory (Longpre et al. 2021, **S**). [Paper](https://arxiv.org/abs/2303.11315).
- **Leakage measures in student simulators**: "The Imperfect Learner" (arXiv 2511.05903; **A**, abstract fetched but it did not define the leakage ratio) is reported by a search summary to define a Leakage Ratio with values of about 0.51 for Qwen3-8B, 0.23 for Gemma-2-9B and about 0.11 for GPT variants (**S, unverified; check the paper**). HACHIMI-II (arXiv 2610.19654; **S**) calls the failure "competence leakage". "Towards Valid Student Simulation with LLMs" (arXiv 2601.05473; **S**) treats simulation as constrained generation within an explicit epistemic boundary.
- **Embracing Imperfection** (Wu et al., ACL 2025, arXiv 2505.19997; **A**): LLMs "often produce overly advanced answers" and struggle to simulate lower-ability students. [Paper](https://arxiv.org/abs/2505.19997).

### 11.3 LLM scoring: reliability and fairness

- Run-to-run variation remains at temperature 0; aggregating several trials is advised ([short-answer study](https://arxiv.org/abs/2310.18373), [Rating Roulette](https://preview.aclanthology.org/dashboard/2025.findings-emnlp.1361), [rubric-conditioned grading](https://arxiv.org/abs/2601.08843); all **S**).
- **Jadhav, Danve and Shaw, "Implicit Grading Bias in LLMs"** (arXiv 2603.18765, 19 Mar 2026; **A**): 180 student responses, three surface perturbations (grammar errors, informal language, non-native phrasing), maths, programming and essays. In essays LLaMA 3.3 70B deducted about 1.35 points and Qwen 2.5 72B about 0.90 on a 10-point scale for non-native phrasing (informal language 1.90 and 1.20); effect sizes ranged from d = 0.64 to 4.25; maths and programming showed minimal bias; **telling the models to grade content only did not remove the bias.** [Paper](https://arxiv.org/abs/2603.18765).
- A [Monash study (AIED 2025)](https://arxiv.org/abs/2504.21330) found scoring error rises for non-native writers when the model infers they are non-native (**S**); other first-language bias work on TOEFL essays (arXiv 2607.14605; **S**). Mostly essay tasks, less in maths and programming.
- **Implication for this design:** our novice answers fixed items, so there is no grader to be biased, but the novice *reads* the student's text and can be style-sensitive in the same way. That is what `instrument.fairness` measures, and why the lexical control's own style gap (section 9.1) matters.

### 11.4 Prerequisite discovery, graph audit and graph maintenance

- **Annabi and Nguyen, "Prerequisite Structure Discovery in Intelligent Tutoring Systems"** (arXiv 2402.01672, ICDL 2023; **A**): a knowledge-tracing model with a learnable knowledge structure, assessed by using the structure to recommend content to **simulated students**. Our planted-error harness validates on simulated data in the same spirit. [Paper](https://arxiv.org/abs/2402.01672).
- Other prerequisite work (**S**): [causal discovery, Scheines, Silver and Goldin, EDM 2014](https://www.stat.cmu.edu/~brian/nynke/726-2021/week06/HCI%20prereq%20discovery/ScheinesSilverGoldin-EDM2014.pdf); [E-PRISM metrics validated on synthetic data, EDM 2023](https://educationaldatamining.org/edm2023/proceedings/2023.EDM-posters.55/2023.EDM-posters.55.pdf); [ACE, expert-in-the-loop, JEDM 2024](https://jedm.educationaldatamining.org/index.php/JEDM/article/download/737/216); a knowledge-graph study that ranks concept pairs for expert review and tests the ranking on exam data; KnowEdu, reported F1 above 0.70 for concept extraction and AUC 0.95 for relation identification.
- **No ground truth for prerequisites in ASSISTments.** The 2009-10 skill-builder data is widely used for knowledge tracing (one paper reports 283,104 interactions, 4,151 students, 101 skills; another 123 skills; the counts depend on preprocessing), skills are flat tags, and I found no prerequisite graph and no licence statement on the official page or mirrors (**S**; check the Figshare record before redistributing). So an ASSISTments audit can show the method behaves sensibly on real behaviour; it cannot score edge accuracy.
- **Graphs from lectures and maintenance**: [InstructKG](https://www.arxiv.org/abs/2602.17111) and [LLM-assisted graph completion with teacher validation, arXiv 2501.12300](https://arxiv.org/abs/2501.12300) (human in the loop; live sessions made the model add concepts that were never taught); Curriculum Brain (arXiv 2610.05860; **S**) encodes a human correction as a standing rule for later runs; an ASEE paper names maintaining graphs as a course evolves as hard. **I found no paper on incremental, versioned course graphs** after two searches.
- **Question generation from concept maps with misconceptions**: [Harnessing Structured Knowledge, arXiv 2505.02850](https://arxiv.org/abs/2505.02850) (hand-built physics concept map with common misconceptions per subtopic, an LLM writes questions and distractors; **S**).

### 11.5 Bloom's taxonomy and mastery learning

- The strict cumulative, difficulty-ordered hierarchy has weak support in performance data (**S**, secondary summaries): a single underlying factor across levels (Madaus et al. 1973), process categories not aligned with the predicted hierarchy (Stoker and Kropp 1971), labels not aligned with item difficulty (Huxam and Naeraa 1980; Kibble and Johnson 2011); a looser hierarchy is more defensible ([review of performance studies, CBE-LSE](https://www.lifescied.org/doi/10.1187/cbe.20-08-0170)). A 2025 study of 1,000 English-test takers found cognitive complexity did contribute to item difficulty, with most items at lower levels ([Frontiers in Education](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2025.1644811/full); **S**). So difficulty-by-level is mixed and context-dependent.
- **Mastery learning**: Bloom (1984) reported about 1 sigma for mastery learning and 2 sigma for tutoring with mastery learning; the 2-sigma figure rests on two studies by his graduate students (Anania 1981; Burke 1980). Kulik, Kulik and Bangert-Drowns (1990) combined 108 controlled evaluations and found an average of about 0.52 SD; Slavin (1987) criticised Bloom's figure as far above the reviews; later reviews of intelligent tutoring systems found about 0.40 (all **S**, from secondary summaries). [Bloom 1984](https://Www.Gwern.net/doc/psychology/1984-bloom.pdf); [Slavin 1987](https://Www.Gwern.net/doc/psychology/1987-slavin.pdf). Do not quote "2 sigma" in the thesis; quote the review average.

### 11.6 What this means for the contribution

- **Not new:** LLM teachable agents; limiting an LLM to a novice level; learning gains from teaching them; quizzing the agent as feedback to the tutor; mastery learning; prerequisite discovery from data; validating a graph method on simulated students; misconception-based distractors from concept maps.
- **Probably open, to confirm with a proper search:** (1) treating the novice's score as a **validated assessment instrument** for the teacher, with reported validity, reliability and fairness; (2) a novice test whose answers are checked against a **verified knowledge graph** and scored **per concept and Bloom level**; (3) feeding that evidence into a planner and into a **graph auditor** that corrects the graph from data, with audit results gating a verifier.
- **Risk.** Waterloo's project publicly plans (1) and its trials may publish before PP2. As of 23 November 2026 I found no results from it. Re-check shortly before presenting (names: Arun, Poupart, Grossmann). Frame the contribution as the **validation protocol and the graph integration**, not the idea of a teach-back exam. A negative result is still a result: if the novice score fails validity or fairness, that is publishable here.
- **Wording of claims.** N1 is a question ("we evaluate whether..."), not a result. N2 (graph-keyed, per-concept and per-level test) and N3 (audit of a pedagogy-typed graph fed into a verifier) are stated as new pipelines, not "the first". N4 (one loop) is an architecture claim and is only as strong as N1 to N3. **Do not claim**: equal outcomes for every student; that the dynamic graph is a research result (it is engineering); that Bloom is a strict ladder; that any simulated number came from real students.

---

## 12. The other components (what was suggested, all their decisions)

Written for the group in the earlier proposal; condensed. I have not changed anyone's branch or code. Everything below is **[ASK]**.

**What each component is today** (read from the remote branches on 29 October; correct me if they are behind your real work). **C1:** 83 concepts, 77 prerequisite edges (75 are hand-written domain-knowledge seeds, only 2 come from captions), 14 Bloom labels, 5 misconception pairs; no JSON export; stage 5 wipes the Neo4j database before writing. **C2:** GNN with Monte Carlo Dropout on ASSISTments; AUC 0.727 with the graph and 0.723 without (placeholder graph); MC uncertainty only weakly signals errors (AUROC 0.56 versus 0.65 for a probability-only baseline) and does not rise with less history. **C3:** LLM drafts a path, a symbolic critic checks five rules, a topological-sort fallback guarantees validity; PP1 ablation: 58.3% of drafts violated a rule, 0% after the critic; the topological-sort-only baseline also has 0% violations.

| For | Suggestion |
|---|---|
| **C1** | A JSON export with stable ids; `facts` and `known_false` statements per concept (about 5 each; the novice's test and the verifier need them); fix the cross-check issues (no general `tree` concept; direction of `stack` to `recursion`; `array` versus `arrays`); edge `source`, `status`, `confidence` fields and a `graph_version`; a weekly update mode that produces a diff, not a rebuild. Gets back: a data-based check of every pedagogy edge type, evaluation evidence that needs no annotators. |
| **C2** | Mastery per Bloom level; accept the evidence message (section 6); test an evidence-count uncertainty (for example a Beta distribution per concept) against MC Dropout; use C1's real graph and re-run the cold-start test; a decaying prior from last semester's marks; forgetting. Gets back: a second kind of evidence besides clicks and a use for calibrated uncertainty. |
| **C3** | Plan a whole 7-week block with a time budget and a mastery floor; make the comparison with plain topological sort meaningful (personalisation quality, time to floor, share below floor in a simulated cohort); use audited edge confidence; carry a target Bloom level per step; use the cohort simulator. Gets back: a measurable goal, a simulator, checked edges. |

**If they say no:** C1 cannot add the extras: C4 keeps its own `knowledge_graph.json` and builds items from it; the auditor runs on planted-error graphs. C2 does not add per-Bloom mastery: C4 keeps its `bloom` block as an extension. C3 does not do the block plan: it stays a C4 simulation. No real student data: phases 1 to 3 need none. **The C4 core depends on nobody finishing.**

**Experiments each could own:** E1 novice validity (C4); E2 planted-error audit (C4); E3 audited edges versus wrong detours (C4 with C3's critic); E4 real C1 graph versus placeholder in C2's prediction (C2); E5 evidence-count uncertainty versus MC Dropout (C2); E6 block plan share below floor (C3); E7 LLM-extracted edges versus gold and versus student data (C1).

**Conflict with the team leader's Enhancement Plan** (received 4 November): his C1 Add-on 1.2 also audits edges against learner data (proposed split: C1 owns the curation console and applies approved changes; C4 supplies the audit method, the Bloom audit and the loop into verification); his `LearnerState` has one mastery value per concept (this needs a matrix per concept and Bloom level); his C3 replanning overlaps the block plan. His C4 add-ons (code-trace visuals, strategy switching, misconception diagnosis) are kept as supporting items, not the core. The mapping is in `docs/PLAN.md`; the revised page is `CartoLEARN Enhancement Plan - C4 revised.html`.

## 13. Risks and limits

1. **Scope explosion.** Core is the novice instrument and the auditor. Plan and dynamic graph are demos and simulation. The LMS is not being built.
2. **Validity may fail.** The novice may measure writing quality or LLM noise more than understanding. Plan to report a negative result.
3. **Leakage and misleading-context resistance.** Prompting alone does not make an LLM ignorant, and a model may resist a student's wrong statement with its own memory (section 11.2). Fallbacks: answer-only-from-context with retrieval, a model too weak to cheat, unlearning.
4. **Fairness.** Style bias is documented for LLM scoring; measure before any grading use. A lexical reader already shows a style gap (section 9.1).
5. **Gaming and AI-written answers.** Needs a supervised setting.
6. **Simulation is circular.** Auditor, plan and E3 results reflect the generator's assumptions (the order baseline shows it). Real claims need the pilot.
7. **Observational data traps** (section 5.4); ASSISTments has no prerequisite ground truth and is not Data Structures.
8. **Equity wording.** "Everyone equal" will be challenged; use the floor and spread wording.
9. **Dependencies.** The graph is C1's, the mastery model C2's, the path C3's; corrections go to owners as proposals; the mastery format and the evidence endpoint must be agreed.
10. **Ethics and data.** Any real student marks or answers need SLIIT ethics approval first; the written pilot protocol is `docs/PILOT_STUDY.md` and the novice study shares its consent and privacy rules.
11. **Novelty is not verified** and may shrink if Waterloo publishes first.
12. **Item bank is small and uncalibrated** (24 items); per-level scores have 1 to 3 items per concept and are thin evidence.

## 14. Open decisions and next steps

Decisions needed from people: supervisor approval of scope and title; the PP2 date (the effort guesses below are for one person part time); why the earlier Teachability draft was dropped and whether that reason still applies; formative only, or counting towards grades after validation; whether SLIIT DSA performance data and ethics approval are obtainable; agreement with the C1, C2 and C3 owners on the matrix-shaped mastery and the evidence interface; whether the verifier stays in the C4 title or becomes one component of the assessment; who presents which part at PP2.

Next, in order: (1) calibrate and enlarge the item bank, then rerun the gate; (2) run the LLM novice gate at more seeds and on a stronger model, and try retrieval-restricted answering if it leaks; (3) a human-annotated sample of student explanations to check the claim check and the novice (needs ethics approval); (4) audit on ASSISTments for sanity on real behaviour, then SLIIT data; (5) offerings with different teaching order, to test the order confound; (6) ethics application, shared with C1 to C3 if they want it; (7) the pilot; (8) Mode 2 only if time allows. Minimum viable thesis: phases 1 to 3 (novice instrument, teach-back pipeline, auditor).

| Phase | Deliverable | Humans? | Rough effort (guess) | State |
|---|---|---|---|---|
| 1 | Knowledge-restricted novice, hidden test, leakage, discrimination, reliability tests on synthetic explanations | No | 3 weeks | built; LLM run in 9.1 |
| 2 | Teach-back pipeline and per-level evidence message | No | 2 weeks | built |
| 3 | Graph Auditor: planted-error test, ASSISTments, loop into the verifier | No | 4 weeks | planted-error and loop built; ASSISTments not done |
| 4 | Plan simulation and help-box demo | No | 2 weeks | built (mixed plan result) |
| 5 | Layered, versioned graph demo | No | 2 weeks | built |
| 6 | Human validity and fairness study, lecturer agreement (Cohen's kappa) | Yes, ethics | unknown | not started |
