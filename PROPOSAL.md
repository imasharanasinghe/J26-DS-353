# PROPOSAL: Teach-Back Assessment and Graph Auditing for GenAir

**For the group (C1, C2, C3, C4). Draft for discussion. Nothing here is decided.**

J26-DS-353, "Pedagogy-Typed Knowledge Graphs for Verified Personalized Learning Path Generation".
Written by Amarasinghe S A R U (C4), 29 October 2026, after the PP1 panel asked every component for a deeper contribution.

This file is a proposal to you, not a plan I will carry out alone. I will not change your code or your branches. Every part that touches your component is marked **[ASK]** and is your decision. If you say no, the rest still works (see section 11).

---

## 1. Why I am writing this

The panel said our four components together look like about one normal final-year component, and asked each of us for something new and deeper. Right now:

- C4 (mine) checks an LLM explanation against the graph and the learner's state. It works, but it is mostly engineering, and everything it says is only as good as the graph and the learner model.
- None of our components checks the graph against real student behaviour.
- None of our components has a way to measure what a student really understands, except quiz right/wrong answers.

This proposal fills those two gaps and gives each of us something deeper, using the graph we all share.

## 2. The idea in plain words

Think of one student through one semester.

1. **Start.** The student does a short diagnostic quiz. We also look at last semester's marks. We get a first guess of what they know.
2. **Plan.** The lectures are the same for everyone (in the lecture hall). But the practice, notes and extra tasks are different. A student who is behind gets more practice on the concepts they are missing. A student who is ahead gets harder tasks. The goal: when the mid exam (lectures 1 to 7) and the final exam (lectures 8 to 14) come, **every student is above a minimum level, and the gap between students is smaller.** We do not promise "everyone equal". We promise "nobody left below the floor".
3. **Help.** On each module page there is a box: "Do you need help with any lecture or concept?" An AI answers using the knowledge graph. C4's verifier checks the answer, so it is true and fits the student's level.
4. **Teach-back exam.** In the mid or lab exam, for each lecture the student has about 10 minutes: "Explain what X is in your own words. Your answer must include Y and Z." Then an **AI novice** reads only the student's answer, trusts it, and takes a small hidden test. The novice's score shows how well the student understood and could explain. A student who explains badly or wrongly produces a novice that fails.
5. **Update.** The test result updates what we know about the student, concept by concept and Bloom level by Bloom level. The plan for the next half is rebuilt from that.
6. **Graph checking.** Using all the student results, a **Graph Auditor** asks: "Does the graph's prerequisite structure match what students actually do?" It proposes fixes. A lecturer approves or rejects them.

## 3. Does this fit our title?

Our title is "Pedagogy-Typed Knowledge Graphs for Verified Personalized Learning Path Generation". Honest answer: **the audit fits strongly, the teach-back exam fits moderately, the LMS parts fit only as a frame.**

| Part | Fit | Why |
|---|---|---|
| Graph Auditor | Strong | It tests our four pedagogy edge types (prerequisite-of, cognitive-load, bloom-level, common-misconception-of) against data. It is the "verified" part, aimed at the graph itself |
| Teach-back exam | Moderate to strong | It uses the graph as the answer key (symbolic ground truth), tags every question with Bloom level, and feeds the learner model (C2) and the path (C3). It is a measurement tool built on the typed graph |
| Help box | Strong | It is C4 as it is today |
| Automatic plan | Moderate | It is C3's job (path generation) extended with a time budget and exam dates |
| Dynamic graph | Moderate | It is C1's job. Our title says "pedagogy-typed", not "static" |

The sentence that ties it together: **the typed graph is used three ways: to build the path (C3), to check explanations (C4), and now to score what students teach back and to be checked by what they do.** One map, and every part of it is verified against something.

What we should avoid: describing this as "an LMS". We are a middleware, as the README says. The LMS is only the place where it would run.

## 4. What each component is today (as I found it on 29 October)

I read the four branches (`Component1_KG`, `component2-gnn-student-model`, `c3_pathplanner`, `c4`). Correct me if the branches are behind your real work.

**C1 (graph, `Component1_KG`).** Pipeline stages 0 to 5 produce CSVs and a Neo4j graph. From the C4 cross-check at commit `1118370`: 83 concepts, 77 prerequisite edges (75 are hand-written "domain knowledge seeds", only 2 come from the captions), 14 Bloom labels, 5 misconception pairs. The gold corpus and evaluation script are empty. No JSON export. Stage 5 wipes the Neo4j database before writing.

**C2 (learner model, `component2-gnn-student-model`).** GNN with Monte Carlo Dropout on ASSISTments. AUC 0.727 with the graph and 0.723 without it. The graph is a placeholder built from data, not C1's graph. The README's own findings: MC uncertainty only weakly shows when predictions are wrong (error-detection AUROC 0.56 against 0.65 for a simple probability-only baseline), and it does not rise for learners with less history (spread 0.0318 at 5 answers against 0.0316 at 40).

**C3 (path planner, `c3_pathplanner`).** LLM drafts a path, a symbolic critic checks five rules (R1 to R5), only the broken step is repaired, a topological-sort fallback guarantees a valid path. PP1 ablation with GPT-4o: 58.3% of drafts had a violation (36 cases), 0% after the critic (p about 1e-6). The topological-sort-only baseline also has 0% violations and in their table a better score, so the gain over a non-LLM baseline needs a clear argument.

**C4 (explanation verifier, `c4`, mine).** Section 5 explains it fully.

## 5. C4 today: everything the branch already has

### 5.1 The verifier

Input: C3's verified path, C2's learner state, C1's graph, and a draft explanation. Steps:

1. Split the draft into sentence-level claims with stable ids and detect concepts (longest-match).
2. **Factual label** per claim: `ENTAILED`, `CONTRADICTED`, `UNSUPPORTED`, with the graph evidence. Rule-based (content-word Jaccard similarity of at least 0.6; a `known_false` statement wins only if the claim is closer to it than to any true fact and the negation matches). It is not NLI.
3. **Cognitive label**: `APPROPRIATE`, `BLOOM_MISMATCH`, `UNMASTERED_PREREQUISITE`, `INCONCLUSIVE`. Mastered means mastery at least 0.70 and uncertainty at most 0.25. Near the threshold or missing history gives `INCONCLUSIVE`, never a silent pass. A verb-cue estimator gives each claim a Bloom level.
4. Typed violations and a confidence tier.
5. **Repair**: rewrite only the violating sentences (a graph fact that itself verifies for this learner, or "Review X first" guidance), then re-verify, at most 3 rounds. Unresolved claims are listed, never reported as verified.
6. Report in JSON (schema `c4-report/1.2`) with a trace.

Sentences C4 writes itself from graph data are marked `grounded` and left out of the hallucination rate so they cannot hide errors.

### 5.2 Drafting

Local Qwen3 4B through Ollama (GPT-4o is planned; the verifier does not depend on which model). The draft is a structured document: path diagram, what the concept is, what to know first, where the learner stands, a refresher, common mistakes. There is no offline template generator any more.

### 5.3 Bloom progression (the answer to the first panel comment)

Cognitive appropriateness is a trajectory, not a snapshot. Each learner has a demonstrated Bloom level per concept (1 Remember to 6 Create). Target level is demonstrated plus 1 when every direct prerequisite is mastered, otherwise stay and consolidate. A failed stretch is retried with full support, and demotion happens only after two failures. Support fades (full, partial, minimal). New violation type `BLOOM_STAGNATION` (no task at the target level), repaired by adding a "Check yourself" section.

### 5.4 Bloom estimator

Verb-cue matcher, two versions, 90 labelled items (dev, test, "hard" indirect phrasing). 100% on the in-vocabulary test split, 16.7% on indirect phrasing, one annotator, no kappa.

### 5.5 Evidence so far

- Stress test, 28 cases (7 concepts times 4 learner profiles), 84 claims. Hallucination 25.0% to 0.0%, cognitive mismatch 29.8% to 0.0%, all 44 violating claims fixed, no new violations. Factual-only and cognitive-only ablations each fix only their own half.
- Natural Qwen3 output, 28 explanations: the strict rule flags essentially every sentence, so read that as "not supported by two graph facts", not as true hallucination.
- Threshold sensitivity sweep (0.3 to 0.8).
- Progression: 84 runs (question at target level 0% to 100%); 300 simulated learners over 8 sessions: +0.36 levels (95% interval 0.29 to 0.43) under the ZPD model, 0.00 under a flat control, +0.02 under a matched control. The stretch is the active ingredient; fading adds nothing in this simulation; it needs enough sessions (about 0 at 4, +0.90 at 12).
- Statistics: paired designs, bootstrap intervals, Wilcoxon, Cohen's dz, McNemar.

### 5.6 The product

- Web workbench (`python3 scripts/run_c4_server.py --open`): Inputs, Verification, Progression, Evaluation tabs, with ablation toggles and a downloadable report. Standard-library server, vanilla JS, local only, no authentication (never expose it).
- API: `GET /api/health|meta|results`, `POST /api/verify|generate|explain|session|answer`.
- CLI demo (`run_c4_demo.py`), evaluation script, progression script.
- Adapters for the C1 CSV format, C2 learner state, C3 `PlanResult.to_json` format, plus imported C3 fixtures (`c4/data/c3_import/`: 30-concept graph, learners, verified paths).
- CartoLEARN brand kit and UI skin.
- 161 automated tests, about 5,900 lines of code.

### 5.7 Methodology

Design Science Research with iterative prototyping. Frozen metric definitions and failure policy (`docs/GUIDELINES.md`), an ablation matrix, controlled stress corpus plus natural generation, simulated-learner experiment with flat and matched controls, and a written human pilot protocol (`docs/PILOT_STUDY.md`) that has not been run and needs SLIIT ethics approval.

### 5.8 Known weaknesses

Stress labels are built by recipe (not human-annotated, no kappa), and post-repair rates use the same verifier that did the repair. Factual matching is lexical. Progression results are simulated, so they partly return the simulator's own assumptions. No real C1 to C3 integration yet: concept ids differ between branches, so C4 uses compatible mocks. Novelty has not been checked with a literature search for the original scope.

## 6. My new C4 scope: the Teach-Back Exam and the Graph Auditor

The old C4 question was "is this explanation true and at the right level?" The new C4 has two connected questions:

> **Q1.** Can the score of a knowledge-restricted AI novice that has learned only from a student's explanation be used as a valid, reliable and fair signal of what that student understands, per concept and Bloom level?
>
> **Q2.** Can the graph's prerequisite edges, Bloom labels and misconceptions be checked against what students actually do, and does using the checked graph make C4's verdicts better?

The existing verifier stays. It becomes the tool that checks the student's explanation and the test answers against the graph.

### 6.1 The teach-back exam (Q1)

**How one exam question works (example: Heaps).**

1. Prompt to the student: "Explain what a heap is in your own words. Your answer must include 'complete binary tree' and 'stored in an array'."
2. The student writes 4 to 8 sentences (or a short list or diagram, see 6.3).
3. **Coverage check.** Are the required graph concepts there?
4. **Claim check (existing C4).** Are the student's sentences true against the graph? "A heap is always fully sorted" matches a known-false statement, so it is flagged.
5. **AI novice.** A language model that must answer only from the student's text. It sees nothing else. It takes a hidden test about heaps. Items are multiple choice or short answers, tagged by concept and Bloom level, with correct answers taken from the graph (not from an LLM's opinion).
6. **Score.** Per concept and per Bloom level. For example: Remember 3 of 3, Apply 1 of 2, Analyze 0 of 1. This goes to C2 as evidence.

**Timing.** 6 lectures times about 10 minutes = a 1 hour lab exam.

**Mode 2 (later).** The student teaches by answering the novice's questions, then the novice takes the test. It is richer but noisier, so it comes after Mode 1 works.

**Mapping task to Bloom level (a hypothesis we test, not assume):**

| Student task | Novice test item | Level evidenced |
|---|---|---|
| Explain X | Define or recognise X | Remember, Understand |
| Include an example | Apply X to a new case | Apply |
| Compare X and Y | Choose and justify | Analyze |
| Handle the novice's "why?" (Mode 2) | Judge a flawed design | Evaluate |

### 6.2 Why this can fail, and how we test it

This is the risky part. A score from a leaky or noisy AI proves nothing, so the first job is to test the instrument itself.

| Risk | Test |
|---|---|
| The AI already knows the answers (a language model knows Data Structures) | **Leakage test.** With an empty answer the novice must score near chance. If not, use a stricter restriction |
| It cannot tell good from bad explanations | **Discrimination test.** Complete, missing-a-step, shuffled, subtly wrong and empty explanations must rank in that order |
| The score changes from run to run | **Reliability test.** Repeat the same answer many times and report the spread (even at temperature 0 results can vary) |
| It does not match real understanding | **Validity test.** Compare with a normal exam and with a human marker on a sample (needs ethics approval and real students) |
| It punishes weaker English writers | **Fairness test.** Compare scores of students with equal understanding but different writing ability. Offer a concept-list or diagram input as an alternative |
| Students paste an AI-written answer | Supervised lab, unseen prompts, similarity check, a short oral follow-up on a sample |
| The novice reasons its way to correct answers from a few keywords | **Depth check.** Count how much of each correct novice answer can be traced to the student's own sentences. Discount the rest |
| The test is too easy (Waterloo's Chrysalis study had a ceiling effect on an easy quiz) | Pilot the items and keep only those that spread students out |

**Scoring has no LLM judge.** The novice answers fixed items and the answers are matched against the graph. That removes grading noise. Only the novice's own answers can vary, and we measure that.

**Not a grade at first.** The score is evidence for learning support. It only counts for a grade if validity and fairness are shown.

### 6.3 Input options

Prose is the default. A concept list or labelled diagram is allowed too, so weaker English writers are not marked down for style. We compare both in the fairness study.

### 6.4 The Graph Auditor (Q2)

It reads the graph (C1) and student evidence (C2 mastery, plus quiz and exam data), and writes a report for the lecturer. It never edits the graph itself.

**Edge audit.** For each "A is a prerequisite of B":

- **Implication test.** If A is needed for B, then mastering B without A should be rare (after allowing for guessing and slips).
- **Order test.** Students should usually succeed on A before B.
- **Lift test.** Success on B should be clearly more likely when A is mastered.

Each edge gets a status with an interval: **Supported, Contested, Reversed, Unsupported**, plus **Missing (candidate)** for unlinked concept pairs with a strong dependency.

**Audit of the other pedagogy types.**

| Type (from C1) | What we test |
|---|---|
| prerequisite-of | The edge audit above |
| bloom-level | Items labelled higher should be harder, and success at higher levels should depend on lower ones. A disagreement is reported as a finding about the label, because Bloom is not a strict ladder in the research |
| cognitive-load (computed from prerequisite depth) | Does the computed load predict how hard students actually find the concept? |
| common-misconception-of | If the data records which wrong option was picked, is the misconception really common? Skipped if the data has no wrong-option information |

**Feedback into C4.** A claim that depends on a *Contested* prerequisite becomes `INCONCLUSIVE` with a note, instead of a hard violation. An *Unsupported* edge no longer sends a student to "review X first". The report gets an `edge_confidence` block.

**Traps we must state honestly.**
- Students meet prerequisites first, because the course is in that order. So order and implication tests can look like dependencies when they are only the timetable. The result is evidence, not proof. We reduce the problem by comparing lecturers or offerings who teach in a different order, by controlling for prior mastery, and by the planted-error test below. Heavy causal inference is out of scope.
- ASSISTments is not Data Structures. It tests the method on real student behaviour. Auditing the DSA graph needs DSA performance data and ethics approval.
- Small classes give wide intervals. Many edges will honestly be "Contested".

### 6.5 The help box

Same as today's C4: retrieve graph facts and transcript chunks, draft with the LLM, verify and repair, show with "review X first" guidance. We add:
- Attempt first, then hints, then the explanation.
- Help requests are logged as a confusion signal for the lecturer. **Asking for help is never counted as mastery.**

### 6.6 What stays from the old C4

Verifier, repair, Bloom progression, simulation and the workbench all stay. Progression gets better inputs (audited prerequisites, evidence from the exam).

## 7. How the pieces connect (interfaces)

Everything below can run on mock files first. Nothing needs the other components to be finished.

```text
C1 graph (versioned) ──► C2 mastery[concept][bloom] ◄── evidence ── quizzes, practice, TEACH-BACK EXAM (C4)
        │  ▲                      │                                            │
        │  └── audit proposals ◄──┼── student data ──► Graph Auditor (C4)      │
        ▼                         ▼                                            │
   C3 planner (path + practice plan per student) ──► C4 verifier ──► student ◄─┘
```

**7.1 C1 to everyone: graph export.** JSON with stable concept ids, the four edge types, and per-concept `facts` and `known_false` statements. Each edge carries `source` (seed, caption, lecturer), `status` and `confidence` fields, empty at first. A `graph_version` string on top.

**7.2 C4 to C2: evidence.** One message per (student, concept, Bloom level):

```json
{"student":"S001","concept":"heap","bloom":3,"score":0.5,"items":2,
 "source":"teachback_exam","weight":"high","graph_version":"2026-w07-v3"}
```

**7.3 C2 to everyone: mastery.** `mastery`, `uncertainty` per concept (as today) plus per Bloom level (new).

**7.4 C4 to C1: audit proposals.**

```json
{"edge":["binary_tree","heap"],"status":"Contested","evidence":"lift 1.1 (0.8 to 1.6), n=120",
 "proposal":"keep, lower confidence","needs_lecturer":true}
```

**7.5 C3 to C4:** unchanged (`PlanResult.to_json`).

## 8. Mastery and Bloom, simply

- The state is a table: for each student, each concept, each Bloom level: a mastery probability and an uncertainty. Not one number per concept, because the Bloom question has to be testable.
- Update with knowledge tracing that allows for guessing, slips and forgetting (uncertainty grows with time).
- A concept is mastered at level L when probability is at least 0.70 and uncertainty at most 0.25 (as C4 uses today).

| Evidence | Weight |
|---|---|
| Teach-back exam | High, once validated |
| Checkpoint quiz | High |
| Practice attempts | Medium (less if hints were used) |
| Help-box use | None |
| Last semester's marks | Prior only, fades fast, never a label on the student |

- Target Bloom level = demonstrated level plus 1 when direct prerequisites are mastered (already built in `c4/progression.py`).
- Levels above are not assumed to need the levels below. We test which levels depend on which.

## 9. The automatic plan and the dynamic graph

### 9.1 Plan (C3's area, optional for them)

- Goal for each 7-week half: every student at or above mastery floor θ on every concept in the half, at the Bloom level the course sets.
- Gap = target minus current mastery. Spend the practice budget in proportion to the gap, weighted by how many later concepts depend on that concept, in the graph's prerequisite order.
- Project each student's progress to the exam date. If it ends below the floor, escalate (more practice, a message, a lecturer alert). Re-plan at checkpoints (week 3 and week 10).
- Strong students get stretch, not less work.
- The student sees why they got their plan and can ask for more. Nobody gets less than the baseline.
- Measured by: share of students below the floor, and spread of exam scores.

### 9.2 Dynamic graph (C1's area, optional for them)

"Dynamic" does not mean the graph rewrites itself. It means layers, versions and proposals.

1. **Base graph** (department level). Changes rarely.
2. **Lecturer overlay** per lecturer and offering: reorder, add local concepts, mark "not covered", change emphasis, add terms. Inherits from the base.
3. **Audited confidence** per offering, from the Graph Auditor.

Changes come from three places: weekly re-reading of lecture transcripts, audit results, and lecturer edits. Every change is a **proposal** a lecturer approves, with a version and a changelog. The graph is frozen for each 7-week half so students are not tested against a moving target. If a concept is split, merged or renamed, mastery moves with it: a split gives the children the parent's mastery with more uncertainty; a merge takes the lower mastery.

## 10. What I suggest each of you could do **[ASK]**

These are ideas, based on what I saw in your branches and on the panel comment. Take what helps you, drop what does not.

### 10.1 C1 (graph)

Things C4 needs, which also help your own evaluation:

1. **A JSON export with stable ids**, not only CSV and Neo4j. Right now stage 5 deletes the Neo4j database before writing, so a safe export (or a versioned write) would stop surprises.
2. **`facts` and `known_false` statements per concept** (about 5 each). C4 needs them for checking explanations and for building the novice's test. Misconceptions are now concept pairs (heap and stack), which cannot be used as statements.
3. **Fix known cross-check issues**: no general `tree` concept; the direction of `stack` to `recursion` (C1 says stack is a prerequisite of recursion, C4 treats recursion as a root); id mapping (`array` and `arrays`).
4. **Edge `source`, `status`, `confidence` fields** and a `graph_version`, so audit results and lecturer approvals have somewhere to live. That is also the first step of the layered graph.
5. **A gold corpus subgraph check**. You already have panel feedback on subgraph-level checking. Our audit gives a second, independent kind of check on the same edges (against student behaviour). You can compare the two.
6. **Only 2 of 77 edges come from captions.** The panel may ask what the LLM actually contributed. Reporting this honestly, and increasing the caption-derived share, would help your contribution claim.
7. **Weekly update mode**: re-run on one new lecture and produce a diff, not a rebuild (supports the dynamic graph).

What C1 gets from us: a data-based check of every pedagogy edge type, which is real evaluation evidence that does not need annotators.

### 10.2 C2 (learner model)

1. **Mastery per Bloom level**, not only per concept. C4's progression already keeps a `bloom` block that C2 does not provide, and the panel comment is about cognitive level over time, so this is the natural next step.
2. **Accept evidence from the teach-back exam** (message in 7.2), with weights. This gives C2 a second, richer kind of data besides right/wrong answers.
3. **Uncertainty that really grows when evidence is small.** Your results say MC Dropout uncertainty does not rise for learners with less history, and a probability-only baseline detects errors better. A simple evidence-count-based uncertainty (for example a Beta distribution per concept or an ensemble) may do better. Testing this against MC Dropout would be a strong honest result either way.
4. **Use C1's real graph** and re-run the cold-start test. Right now the graph gain is +0.004 AUC on a placeholder graph, and the cold-start benefit is not established.
5. **A prior from last semester's marks**, decaying quickly, for the start-of-semester cold start.
6. **Forgetting** (uncertainty grows with time), needed for a 14-week semester.

What C2 gets from us: new evidence that is not just clicks, per-Bloom targets to model, and a use for calibrated uncertainty (the planner and verifier both use it).

### 10.3 C3 (path planner)

1. **Plan for a whole 7-week block, not one path to one target.** Add a time budget, the exam date and a mastery floor as the goal. Spend practice on the largest gaps first (section 9.1).
2. **Make the comparison with plain topological sort meaningful.** In the PP1 ablation the non-LLM topological baseline also has 0 violations. The extra value of the LLM has to be shown on something else: personalization quality, time to reach the floor, practice allocated to real gaps, or the share of students below the floor in a simulated cohort.
3. **Use audited edge confidence.** A path rule R1 ("prerequisites first") on an edge the auditor calls *Unsupported* may be asking students to do unnecessary work; on a *Missing* edge it may be missing one. Compare path validity before and after audit.
4. **Bloom-aware steps.** Each step carries a target Bloom level from C4's progression policy.
5. **Cohort simulation.** C4's `simulation.py` already makes simulated learners. A simulated class of 300 with a floor makes the equalisation claim testable before any real student.
6. **Keep the rule that RL chooses only among verified paths.**

What C3 gets from us: a measurable goal (floor and spread), a cohort simulator, and checked edges.

### 10.4 C4 (me)

Teach-back exam (6.1 to 6.3), Graph Auditor (6.4), help box (6.5), progression kept. I will do the work on mock files and tell you before changing any format that touches you.

## 11. What stays safe if you say no

| If | Then |
|---|---|
| C1 cannot add the extras | C4 keeps its own `knowledge_graph.json` fixture and builds the test items from it. The auditor runs on planted-error graphs |
| C2 does not add per-Bloom mastery | C4 keeps its `bloom` block as a C4 extension, as now |
| C3 does not do the whole-block plan | The plan is shown as a simulation inside C4's workbench, not as C3's work |
| No real student data | Phases 1 to 3 (below) need none. The pilot waits for ethics approval |

My core (teach-back instrument plus Graph Auditor) depends on nobody else finishing.

## 12. Experiments (for everyone's evaluation chapter)

| # | Question | Who | How |
|---|---|---|---|
| E1 | Is the novice score valid, reliable and fair? | C4 | Leakage, discrimination, repeat-run, then (with ethics) normal-exam comparison and writer-ability bias |
| E2 | Can the auditor recover errors we plant in a good graph? | C4 (data from C2's setup) | Delete, reverse and add edges, measure precision, recall and F1 across data sizes, then run on ASSISTments against simple co-occurrence and ordering baselines |
| E3 | Do audited edges cut wrong "review first" instructions and missed prerequisites? | C4 with C3's critic | With and without audit, on simulated and real data |
| E4 | Does the graph change how well the learner model predicts? | C2 | Real C1 graph versus placeholder; per-Bloom mastery |
| E5 | Does an uncertainty based on evidence count beat MC Dropout? | C2 | Error detection and calibration, history size sweep |
| E6 | Does a block plan reduce the share of students below the floor and the spread? | C3 | Simulated cohort, then pilot |
| E7 | Do LLM-extracted edges agree with gold and with student data? | C1 | Subgraph gold check plus the audit report |

A negative result is a valid result. If the novice score is not valid or not fair, saying so, with the measurements, is still useful.

## 13. What is new, and what is not

I ran a first literature search on 29 October. It is a start, not a full review. Details and links are in NEW1.md section 10.

- **Not new:** LLM teachable agents; keeping an LLM at a novice level; the "protégé effect"; mastery learning; discovering prerequisites from student data.
- **Close to ours:** the University of Waterloo project page plans an exam on what an LLM companion learned, as an indirect sign of what the student knows (no published results found). Their Chrysalis paper itself measured the human students with a normal quiz. They may publish before PP2, so we must re-check just before we present.
- **What we claim, carefully:**
  1. We *evaluate* whether the novice's score is a valid, reliable and fair indicator, and give a protocol. We do not say "validated" until we have data.
  2. A novice test whose answers are checked against a verified graph and scored per concept and Bloom level.
  3. A data-based audit of a pedagogy-typed LLM-built graph (including Bloom labels and misconceptions) fed back into an explanation verifier.
  4. Putting the pieces in one loop is the architecture claim. It is only as strong as 1 to 3.
- **We must not claim:** equal outcomes for every student; that the dynamic graph is a research result (it is good engineering); that Bloom is a strict ladder.

## 14. Risks

1. **Scope.** This is big. Core is the novice instrument and the auditor. Plan and dynamic graph are demos and simulation.
2. **The score may not be valid.** The model might be measuring writing quality or its own noise. We plan for a negative result.
3. **Leaky novice.** Prompting alone does not make an LLM forget what it knows. If it leaks, we test a stricter restriction or a model that is too weak to cheat.
4. **Fairness and gaming.** Documented for LLM scoring. Measure first, then decide whether any score may count for a grade.
5. **Simulation is circular.** Plan and Bloom results in simulation reflect the simulator's assumptions. Real claims need the pilot.
6. **Ethics and data.** Anything with real marks or answers needs SLIIT ethics approval first.
7. **Dependencies.** Graph is C1's, mastery is C2's, path is C3's. Nothing changes in your component without your agreement.
8. **Novelty may shrink.** If Waterloo publishes first, the contribution narrows to the validation, the graph check and the loop.

## 15. Phases (my part)

| Phase | What | Humans? | Rough effort* |
|---|---|---|---|
| 1 (must) | Knowledge-restricted novice, hidden test, leakage, discrimination and reliability tests on synthetic explanations | No | 3 weeks |
| 2 (must) | Teach-back pipeline: coverage, claim check, novice test, per-level evidence message | No | 2 weeks |
| 3 (must) | Graph Auditor: planted-error test, then ASSISTments, then feedback into the verifier | No | 4 weeks |
| 4 (should) | Plan simulation and help-box demo | No | 2 weeks |
| 5 (should) | Layered, versioned graph demo with proposals | No | 2 weeks |
| 6 | Human pilot: validity, fairness, lecturer agreement | Yes, ethics | Unknown |

*Guesses for one person working part-time. The PP2 date is not known and must be fitted in.

**Smallest version that is still a thesis:** phases 1 to 3.

## 16. What I need from you

1. Your own panel feedback and what you plan to build next. Does anything above overlap with it? If yes, tell me and I will drop my version.
2. **C1:** can you provide the JSON export and the `facts` / `known_false` statements, even for 7 concepts first? Do you want the edge `source`, `status`, `confidence` fields?
3. **C2:** do you agree to per-Bloom mastery and the evidence message? Are you open to testing evidence-count uncertainty against MC Dropout?
4. **C3:** would you like the block plan and cohort simulation as your deeper contribution, or is that outside what you want?
5. All: agree the shared concept ids and the graph version field.
6. All: do we ask the supervisors for ethics approval together (one application, shared consent and privacy rules)?
7. Who should present which part at PP2, so the story is one story.

## 17. What I am not doing

- I am not building an LMS.
- I am not changing your branches or your code.
- I will not present any number from a simulation as if it came from real students.
- I will not say the novice score is valid until it has been tested.
- I am not running anything on students before ethics approval.

## 18. Open decisions

- Supervisor approval of the scope and title (this is still a draft).
- The PP2 date.
- Why the earlier Teachability draft was dropped, and whether that reason still applies.
- Whether SLIIT DSA performance data and ethics approval can be obtained.
- Whether the novice score is only for learning support, or may count for a grade after validation.
- Whether the verifier stays in the C4 title or becomes one part of the assessment.
