# NEW1: The Teach-Back Exam, a graph-checked novice AI that assesses mastery and drives personalised practice

**Component 4 scope extension: from "verify explanations against the graph" to "assess what a student understands by what a knowledge-restricted AI novice can learn from them, and use that to plan their practice"**

J26-DS-353, Component 4 (Amarasinghe S A R U, IT23216778)
Status: **proposal draft, not yet approved by the supervisor.** Nothing in this file is implemented yet. Written 29 October 2026 after the PP1 result (22 October), where the panel asked for a deeper and more inventive scope. It replaces the earlier Teachability draft and the Graph Auditor draft; the Graph Auditor survives as a component (section 6). The literature review in section 10 was done on 29 October from search results and abstracts; papers marked "read abstract only" have not been read in full.

---

## 1. Why the scope changes

The PP1 panel said the four components together amounted to roughly one normal final-year component and asked for something new and deeper in each. C4 today is a verifier: it checks an LLM explanation against the knowledge graph (C1) and the learner's state (C2), and repairs what fails. That is an engineering result, and every verdict it gives is only as good as the graph and the mastery estimates behind it.

## 2. The idea in one paragraph

An LMS that, at the start of each semester, gives every student a plan for the module: the lectures are the same for everyone, but the **practice, notes and stretch tasks differ** according to a diagnostic and last semester's marks. The aim is that every student reaches the mid exam (lectures 1 to 7) and the final exam (lectures 8 to 14) above a common mastery floor. Each module page has a "need help with any lecture or concept?" box answered from the knowledge graph. In the mid and lab exams, students are not only asked questions: they **explain or teach** each lecture's concepts to a **knowledge-restricted AI novice**, which then takes a hidden test. The novice's score, broken down by concept and Bloom level, is evidence of what the student understands. The knowledge graph behind all of this is **layered and versioned**, so it can change per lecturer and over time without silently rewriting itself.

## 3. Research question

> **Can the test score of a knowledge-restricted AI novice that has learned only from a student's explanation serve as a valid, reliable and fair measure of that student's mastery, per concept and Bloom level, and does using it (with a data-audited knowledge graph) make practice planning more accurate?**

## 4. System overview

```text
        C1: knowledge graph  (base graph -> lecturer overlay -> data-audited edges)
              |                       |                         |
              v                       v                         v
   diagnostic + last-sem marks -> C2: mastery[concept][bloom level] <- evidence from:
              |                                                        practice, quizzes,
              v                                                        TEACH-BACK EXAM
   C3: planner (per student, per 7-week block) -> practice, notes, stretch
              |
   module page: "Need help?" -> LLM draft -> C4 verifier -> explanation shown to student

   Teach-back exam:
   student explanation -> [coverage of required graph concepts]
                       -> [C4 claim check: true vs graph?]
                       -> [AI novice: knows ONLY the explanation] -> hidden Bloom-tagged test
                       -> score per (concept, level) -> C2
```

## 5. Components

### 5.1 Semester plan and equalisation (planner)

- **Goal wording.** Do not promise "every student equal". Promise: **every student reaches a minimum mastery floor on every concept in the block before the exam, and the spread between students shrinks.** This is mastery learning. Measurable outcomes: the share of students under the floor, and the variance of exam scores.
- **Inputs.** Week 0 diagnostic, last semester's marks (as a prior only, with high uncertainty, decaying fast; never used to label a student), then ongoing evidence.
- **Allocation.** For each concept, gap = target mastery minus current mastery at the target Bloom level. Spend the weekly practice budget in proportion to the gap, weighted by how many later concepts depend on it in the graph, ordered by the graph's prerequisite order.
- **Projection.** Estimate each student's learning rate. If projected mastery at the exam is under the floor, escalate (more practice, a nudge, a lecturer alert). Re-plan at each checkpoint (weeks 3 and 10).
- **Strong students get stretch, not less work.** They move up Bloom levels, using the existing C4 progression policy.
- **Transparency.** The student sees why they got their plan and can ask for more. No one gets less than the baseline.

### 5.2 "Do you need help with any concept?" (module page)

- Retrieve graph facts and lecture transcript chunks, draft with an LLM, verify with the existing C4 pipeline (factual and cognitive), repair, and show with "review X first" guidance. This is what C4 already does.
- Ask the student to attempt first, then tiered hints, then the explanation.
- Aggregated questions give the lecturer a confusion map per concept.
- **Asking for help is never mastery evidence.** Only attempts count.

### 5.3 The teach-back exam (the research core)

**Mode 1, written (build first).** Per lecture, a prompt such as "Explain what X is in your own words. Your answer must include Y and Z." The required terms are graph nodes. A 1 hour lab exam of 6 lectures gives about 10 minutes each.

**Mode 2, interactive (later).** The novice asks questions, the student answers, then the novice takes the test. Richer but noisier; it also needs the novice to ask good questions.

**Scoring pipeline (Mode 1):**

1. **Coverage:** are the required graph concepts present?
2. **C4 claim check:** are the student's claims true against the graph? Contradictions of known-false statements are flagged.
3. **Novice test:** a knowledge-restricted LLM that may answer only from the student's text (with an "I don't know" path) takes a fixed hidden test, tagged by concept and Bloom level, with answers taken from the verified graph rather than from an LLM's opinion.
4. **Evidence:** score per (concept, Bloom level), passed to C2 with an uncertainty.

**Bloom mapping (hypothesis to test, see section 8):**

| Student task | Novice test item | Level evidenced |
|---|---|---|
| Explain X | Define or recognise X | Remember, Understand |
| Include an example | Apply X to a new case | Apply |
| Compare X and Y | Choose and justify | Analyze |
| Mode 2: handle the novice's "why?" | Judge a flawed design | Evaluate |

**Validity requirements (a score from a leaky or noisy model proves nothing):**

- **Leakage test.** With an empty explanation the novice must score near chance on the restricted concepts. Prompting alone is known to leave the model's real knowledge intact (section 10), so also try stronger restriction (answer-only-from-context with retrieval, or unlearning).
- **Discrimination test.** Controlled explanations (complete, missing a step, shuffled, subtly wrong, empty) must be ranked in the expected order.
- **Reliability.** Repeated runs on the same answer must give nearly the same score. Temperature 0 does not remove run-to-run variation, so aggregate several runs and report the spread.
- **Criterion validity.** Compare with the conventional exam and with human marking on a sample.
- **Fairness.** Test whether weaker English writers are scored lower than stronger writers at the same level of understanding (section 10 shows this bias is documented for LLM scoring). Report the gap, and test mitigations (marking content rather than style, allowing diagrams or short bullet answers).
- **Gaming.** Pasting an AI-written answer measures the AI. Supervised lab setting, unseen prompts, similarity checks and a short oral follow-up on a sample.
- **Stakes.** Formative first. Count towards a grade only after validity and fairness are shown.

**Design decisions added after the literature check:**

- **Deterministic scoring.** The novice answers fixed items (multiple choice or short answers matched against graph facts), so the scoring step has no LLM judge and no scoring variance. Only the novice's own answers vary, and those are measured by repeated runs.
- **Hard knowledge bound.** The novice sees only the student's text, supplied as retrieved context. Leakage is measured with the empty-explanation test; unlearning is a fallback if prompting leaks.
- **Self-explanation depth check.** A brief keyword answer must not let the novice's own reasoning supply the missing content. Score how much of the novice's correct answers can be traced to sentences in the student's text, and discount the rest.
- **Structured input option.** Besides prose, allow a concept list or labelled diagram, so weaker English writers are not penalised for style. Compare the two modes in the fairness study.
- **Test difficulty.** Chrysalis found a ceiling effect on an easy quiz. Calibrate the hidden test so scores spread across students (pilot items, check item difficulty).

### 5.4 Dynamic knowledge graph

"Dynamic" must mean **layers, versions and gated proposals**, not a graph that rewrites itself.

1. **Base graph:** department-level canonical concepts and prerequisites. Changes rarely.
2. **Lecturer overlay**, per lecturer and offering: reorder, add local concepts, mark concepts as not covered, re-weight emphasis, add terminology. Inherits from the base.
3. **Audited edge confidence**, per offering, from the Graph Auditor (section 6).

Update triggers: weekly re-reading of lecture transcripts (diff, then propose), student-data audit results, and direct lecturer edits.

Governance: every automatic change is a **proposal**, a lecturer approves it, and each graph has a version and a changelog. The graph is **frozen** for each 7-week block so a student is not assessed against a moving target.

Mastery under change (stable concept ids): a split gives the children the parent's mastery with added uncertainty; a merge takes the lower mastery and combined uncertainty; a new edge triggers a re-check, not a demotion.

### 5.5 Mastery and Bloom model

- State: `mastery[student][concept][bloom level]`, a probability and an uncertainty. A matrix, not one number, because the Bloom claim has to be testable.
- Update with a knowledge-tracing model with guess and slip, uncertainty growing with time (forgetting).

| Evidence | Weight | Note |
|---|---|---|
| Teach-back exam | High, once validated | Per level |
| Checkpoint quiz | High | |
| Practice attempts | Medium | Lower if hints were used |
| Help-box use | None | Signal for the lecturer only |
| Last semester's marks | Prior only | Decays fast |

- Mastered at level L: probability >= 0.70 and uncertainty <= 0.25 (as in C4 today).
- Target Bloom level = demonstrated level + 1 when direct prerequisites are mastered (existing `c4/progression.py`).
- Bloom is **not assumed to be a strict ladder** (section 10). Which levels depend on which is tested, not hard-coded.

## 6. The Graph Auditor (kept from the earlier draft)

The graph is treated as ground truth by C4, but nobody checks it against what students actually do. The auditor reads the graph (C1) and student evidence (C2) and produces a report for the lecturer. It proposes; a lecturer decides.

- **Edge audit.** For each "A is a prerequisite of B": implication test (mastering B without A should be rare after allowing for guess and slip), order test, lift test. Status with an interval: Supported, Contested, Reversed, Unsupported, or Missing (candidate).
- **Bloom audit.** Items labelled higher should be empirically harder, and success at higher levels should depend on success at lower ones. Disagreeing items are flagged. Bloom labels are tags on items and on a student's level within a concept; they are **not** prerequisite edges between concepts, and the edge audit does not use them. Given the evidence that Bloom is not a strict ladder, the audit reports a disagreement as a finding about the label, not as an error to correct.
- **Misconception audit** (only if the data records which wrong option was chosen).
- **Loop back into C4.** A claim that relies on a contested prerequisite becomes `INCONCLUSIVE` instead of a hard violation; an unsupported edge no longer sends a student to "review X first"; the report gains an `edge_confidence` block.

This is also the mechanism that makes the graph dynamic in a controlled way.

## 7. Research questions

- **RQ1 (validity).** Does the novice's score track the student's real understanding (conventional exam, human grading)? Does it carry information the verifier and a plain quiz do not?
- **RQ2 (reliability and leakage).** How stable is the score across runs, and how much does the novice know before reading anything?
- **RQ3 (fairness and gaming).** Is the score biased by writing ability or language, and how easily is it gamed?
- **RQ4 (Bloom).** Do per-level scores behave like levels, or does the strict ladder fail on this data?
- **RQ5 (graph audit).** How well does the auditor recover planted graph errors as a function of data size, and does using audited edges reduce wrong "review first" instructions and missed prerequisites?
- **RQ6 (planning).** In simulation, then in a pilot, does evidence-driven allocation reduce the share of students under the floor and the spread, compared with a uniform plan?

## 8. Evaluation

1. **Novice instrument, no humans needed first.** Generate synthetic student explanations with known gaps (using the existing simulated learners and controlled corruptions). Run leakage, discrimination and reliability tests. This is the first gate: if the novice cannot pass these, stop.
2. **Planted-error test for the auditor.** Corrupt a known fraction of edges (delete, reverse, add), measure recovery with precision, recall and F1 across data sizes. Then run on ASSISTments (the dataset C2 uses) against simple co-occurrence and ordering baselines.
3. **Planner in simulation.** Compare uniform, performance-tiered and evidence-driven plans on simulated cohorts. Same-model circularity applies (as in the current progression results); state it.
4. **Human pilot (needs SLIIT ethics approval).** One module, consenting students: novice score versus conventional exam, human grading sample, fairness comparison, lecturer agreement on audited edges (Cohen's kappa).
5. **Downstream effect in the C4 workbench:** wrong detours and missed prerequisites with and without audited edges.

## 9. Reuse, new work and phasing

| Existing | Reused as |
|---|---|
| Verifier and claim pipeline (`c4/pipeline.py`) | Checks the student's explanation and builds the hidden test answers' ground truth |
| Bloom estimator and items (`c4/bloom.py`, `c4/data/bloom_items.json`) | Tags test items and prompts by level |
| Progression (`c4/progression.py`) | Target level and stretch in the plan |
| Simulated learners (`c4/simulation.py`) | Synthetic explanations and planted-error data |
| Adapters, report schema, workbench (`c4/adapters.py`, `c4/web/`) | New evidence output, `edge_confidence`, Exam and Audit tabs |
| Mock C1, C2, C3 fixtures (`c4/data/`) | First inputs; no upstream change to start |

| Phase | Deliverable | Humans? | Rough effort* |
|---|---|---|---|
| 1 (must) | Knowledge-restricted novice plus leakage, discrimination and reliability tests on synthetic explanations | No | 3 weeks |
| 2 (must) | Mode 1 pipeline: coverage, claim check, novice test, per-level evidence into the C2 format | No | 2 weeks |
| 3 (must) | Graph Auditor: planted-error harness, then ASSISTments, then loop into the verifier | No | 4 weeks |
| 4 (should) | Planner simulation and the help-box demo | No | 2 weeks |
| 5 (should) | Layered and versioned graph with a proposal flow (small demo) | No | 2 weeks |
| 6 (pilot) | Human validity and fairness study, lecturer agreement | Yes, ethics | Unknown |
| Later | Mode 2 interactive teaching | Yes | |

*Guesses for one person working part-time. The real PP2 deadline is not known and must be fitted in.

**Minimum viable thesis:** phases 1 to 3. The planner, help box and dynamic graph are shown as simulation and demo, not as a built LMS. **Do not build the LMS**; this is one component of four.

## 10. Prior work (what exists, and what is left for us)

Status of these notes: from web search results on 29 October 2026, plus a NotebookLM check the same day. Opened in full or as abstracts: the Waterloo project page, the Chrysalis paper, the Kucharavy et al. abstract and the Jin et al. abstract. The rest are search results only. Check each against the original before citing. No meta-analysis of the protege effect was found.

**NotebookLM check (29 October).** It rated N1 to N4 "Supported", but every rating rests on "not covered by the sources", meaning the sources it had did not contain the idea; that is absence of evidence in a small notebook, not proof of novelty. It also merged two papers (see Chrysalis below) and gave several quotes and figures I could not match to a source (for example a "15 to 20% score fluctuation" and the "TA could not fully comprehend" quote). Treat its list of 10 papers as leads, not citations, until each is opened.

**Learning by teaching and teachable agents**

- Betty's Brain (Biswas and colleagues, Vanderbilt): students taught an agent and learned more than students taught by an agent, with benefits for transfer and metacognition; small classroom studies in science. [Leelawong and Biswas 2008 and related](https://escholarship.org/content/qt5s81207k/qt5s81207k.pdf?t=op2l22); [Biswas et al. 2010](https://archive.isis.vanderbilt.edu/sites/default/files/Biswas-etal_MeasuringSRL_RPTEL2010.pdf).
- Protege effect, [Chase, Chin, Oppezzo and Schwartz 2009](https://purl.stanford.edu/zm369yx3532): teaching a virtual agent increased effort, most for lower achievers. A [2018 Lund poster](https://www.lucs.lu.se/fileadmin/user_upload/project/lucs/ETG-pub/etg2018-conference-AIED-poster.pdf) found a weak link between the effect and learning outcome.
- [Jin, Lee, Shin and Kim, "Teach AI How to Code" (arXiv 2309.14534)](https://arxiv.org/abs/2309.14534), read abstract only: an LLM tutee (AlgoBo) with limited knowledge that asks why and how questions; 40 novices; more knowledge-dense conversations (effect size about 0.71). This is **learning gain for the teacher, not assessment**.
- [Song, Guo and Lin, "Simulating Novice Students Using Machine Unlearning and Relearning in LLMs" (arXiv 2603.26142)](https://arxiv.org/abs/2603.26142): prompting leaves expert knowledge intact; unlearning gives more novice-like responses (Python multiple-choice questions).
- **Closest to this proposal:** [University of Waterloo "Learning by Teaching a Large Language Model"](https://uwaterloo.ca/teaching-incubator/projects/learning-teaching-large-language-model) (Poupart and Grossmann, Feb to Dec 2025). The project page **plans** an "exam to test the concepts learned by an LLM companion, indicative of the concepts mastered by the student who taught the LLM", with two course trials. This is a plan on a project page, not a published result. I found no paper reporting it.
- [Chrysalis (Arun, Vader and Poupart, arXiv 2510.05271)](https://arxiv.org/html/2510.05271v1), the Waterloo system, opened in full: 36 participants compared an AI tutor with a teachable-agent mode. **It does not use the LLM's test score to assess the student.** Student knowledge was measured by a 20-question multiple-choice quiz taken by the humans (no difference between modes, ceiling effects, quiz too easy). The authors say future knowledge assessments should be better calibrated. So the exam-as-assessment idea is still unpublished as far as I can find.
- [Kucharavy, Vallez and Percia David, "LLMs Protégés" (BEA 2025)](https://aclanthology.org/2025.bea-1.19/), abstract only: students diagnosed an LLM teachable agent prompted to make errors; a gain of 0.72 points on a 1-6 scale, and a projected drop in second-midterm failure from 28% to 8%. The LLM does not take an exam; the outcome is the student's own midterm. **NotebookLM wrongly merged this paper with Chrysalis** and described a system where the LLM takes an exam post-teaching. I could not find that in either paper.

**Simulating students with LLMs**

- LLMs overestimate weak students and miss their typical errors ([Embracing Imperfection, ACL 2025, arXiv 2505.19997](https://ar5iv.labs.arxiv.org/html/2505.19997)); one model does not simulate all ability levels ([ACL Findings 2026](https://aclanthology.org/2026.findings-acl.1807.pdf)); [reviews](https://arxiv.org/pdf/2511.06078) and a [validity survey](https://arxiv.org/pdf/2601.05473) report gaps in errors, memory and consistency.
- [Stochastic Student Knowledge Graphs (arXiv 2608.21668)](https://arxiv.org/pdf/2608.21668): mastery-profile-conditioned simulation; accuracy 44.1% to 85.2% from low to high mastery. A candidate way to restrict the novice.

**Scoring explanations with LLMs: reliability and fairness**

- Run-to-run variation remains at temperature 0 and multi-trial aggregation is advised ([short-answer study](https://arxiv.org/pdf/2310.18373); [Rating Roulette](https://preview.aclanthology.org/dashboard/2025.findings-emnlp.1361); [rubric-conditioned grading](https://arxiv.org/html/2601.08843)).
- Bias against non-native writers is reported in prompted and fine-tuned scorers ([Monash, AIED 2025](https://arxiv.org/pdf/2504.21330); [ESL bias mitigation](https://arxiv.org/html/2601.16724); [implicit grading bias 2026](https://arxiv.org/pdf/2603.18765)), mostly in essay tasks and less in maths and programming.
- LLM scoring of self-explanations beats semantic similarity on a binary code-explanation task ([2026 preprint](https://arxiv.org/pdf/2605.21614)), but the data were imbalanced.

**Prerequisite discovery and graph construction**

- Prerequisite structure from performance data: [knowledge-tracing based (arXiv 2402.01672)](https://arxiv.org/pdf/2402.01672); [causal discovery, Scheines, Silver and Goldin, EDM 2014](https://www.stat.cmu.edu/~brian/nynke/726-2021/week06/HCI%20prereq%20discovery/ScheinesSilverGoldin-EDM2014.pdf); [E-PRISM metrics validated on synthetic data, EDM 2023](https://educationaldatamining.org/edm2023/proceedings/2023.EDM-posters.55/2023.EDM-posters.55.pdf); [ACE, expert-in-the-loop, JEDM 2024](https://jedm.educationaldatamining.org/index.php/JEDM/article/download/737/216).
- Graphs from lectures: [InstructKG](https://www.arxiv.org/pdf/2602.17111), [LLM-assisted graph completion from lecture recordings](https://arxiv.org/pdf/2501.12300). Live sessions made the model add concepts that were never taught. Maintaining graphs as a course evolves was named as hard in an [ASEE paper](https://peer.asee.org/problem-generation-to-personalized-tutoring-leveraging-generative-ai-and-knowledge-components-in-engineering-education.pdf); I found no paper on incremental, versioned course graphs.

**Bloom's taxonomy and mastery learning**

- The strict cumulative, difficulty-ordered hierarchy has weak support in performance data (a single underlying factor across levels, adjacent levels not ordered, labels not aligned with item difficulty); a looser hierarchy is more defensible. [Review of performance studies](https://www.lifescied.org/doi/10.1187/cbe.20-08-0170), secondary summaries only.
- Mastery learning: Bloom reported about 1 sigma for mastery learning and 2 sigma for tutoring with mastery learning; later reviews found smaller effects (about 0.5 sigma average). [Bloom 1984](https://Www.Gwern.net/doc/psychology/1984-bloom.pdf). Figures come from secondary summaries and must be checked.

### What this means for the contribution

- **Not new:** LLM teachable agents, limiting an LLM to a novice level, learning gains from teaching them, mastery learning, prerequisite discovery from data.
- **Probably open, to confirm with a proper search:** (1) treating the novice's score as a **validated assessment instrument** for the teacher, with reported validity, reliability and fairness; (2) a novice test whose answers are checked against a **verified knowledge graph**, scored **per concept and Bloom level**; (3) feeding that evidence into a **planner** and into a **graph auditor** that corrects the graph from data.
- **Risk:** Waterloo's project overlaps with (1) in plan, and its trials may publish before PP2. Re-check for their results (author names Arun, Poupart, Grossmann) shortly before presenting. Frame the contribution as the validation protocol and the graph integration, not the idea of a teach-back exam.
- **How to word the claims (agreed after the NotebookLM check).** N1 is a question, not a result: "we evaluate whether an LLM novice's test score is a valid, reliable and fair indirect indicator of the teaching student's mastery, and give a validation protocol against standard human post-tests." Do not write "validated" before the data exist. N2 and N3 are stated as new pipelines, not as the first of their kind. N4 is presented as a combination (architecture) claim and is only as strong as N1 to N3. The "Supported" verdicts do not change this.
- **Negative results are publishable here.** If the novice score fails validity or fairness, that finding is useful.

## 11. Risks and limits

1. **Scope explosion.** The biggest risk. Keep to phases 1 to 3; show the rest as demo.
2. **Validity may fail.** The novice may measure writing quality or LLM noise more than understanding. Plan to report a negative result.
3. **Novice leakage.** Prompting alone does not make an LLM ignorant.
4. **Fairness.** Language and writing-style bias is documented; measure it before any grading use.
5. **Gaming and AI-written answers.** Needs a supervised setting.
6. **Simulation is circular.** Planner and Bloom results in simulation reflect the simulator's assumptions; the pilot is needed for real claims.
7. **Observational data traps (auditor).** Curriculum order confounds order and implication tests; statuses are evidence, not proof. Practical mitigations short of full causal inference: compare lecturers or offerings that teach the same concepts in a different order, control for prior mastery, and rely on the planted-error test for the method's accuracy. Instrumental-variable or counterfactual modelling is out of scope unless a real intervention exists. ASSISTments is not Data Structures; auditing the DSA graph needs DSA performance data.
8. **Equity wording.** "Everyone equal" will be challenged; use the floor and spread wording.
9. **Dependencies.** The graph is C1's, the mastery model C2's, the path C3's. Corrections go to owners as proposals and the mastery format (matrix per concept and level, an evidence endpoint) must be agreed.
10. **Ethics and data.** Any real student marks or answers need SLIIT ethics approval first.
11. **Novelty is not yet verified** (section 10).

## 12. Open decisions

- Supervisor approval of the scope and title.
- The PP2 date, to fit the phases.
- Why the earlier Teachability draft was dropped, and whether that reason still applies.
- Whether the thesis centre is the novice instrument, the auditor, or both (recommended: both, with the novice instrument as the lead).
- Formative only, or counting towards grades after validation.
- Whether SLIIT DSA performance data and ethics approval are obtainable.
- Agreement with the C1, C2 and C3 owners on the matrix-shaped mastery and the evidence interface.
- Whether the verifier stays in the title or becomes a component of the assessment.

## 13. Fit with the team leader's Enhancement Plan (added 2026-11-05)

The leader's plan (received 2026-11-04) gives C4 code-trace visuals, strategy switching and misconception diagnosis. Those are kept here as supporting add-ons, not the core. Known conflicts: his C1 Add-on 1.2 also audits edges against learner data (split to agree: C1 owns the console and applies approved changes, C4 supplies the audit method, the Bloom audit and the loop into verification); his `LearnerState` has one mastery value per concept (this proposal needs a matrix per concept and Bloom level); his C3 replanning overlaps section 5.1. The revised page is [CartoLEARN Enhancement Plan - C4 revised.html](CartoLEARN%20Enhancement%20Plan%20-%20C4%20revised.html). The mapping is in [docs/PLAN.md](docs/PLAN.md).
