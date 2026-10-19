# Component 4 Research Guidelines

This document records the methodological decisions and safeguards that must
guide Component 4 implementation, evaluation, documentation, and presentation.
It is intended to be understandable by every project member and by future
contributors working in any development environment.

## Project work-management process

All project work must follow the documentation and version-control process
below.

### `LOG.md` — completed work record

[LOG.md](./LOG.md) is the chronological record of work that has already been
completed. After every work session or meaningful change, add an entry with:

- Date
- Time and timezone
- What was changed, reviewed, implemented, tested, or decided
- Any relevant files, results, limitations, or follow-up items

Do not use `LOG.md` for future intentions. Record intentions in
[PLAN.md](./PLAN.md).

### `PLAN.md` — current work plan

[PLAN.md](./PLAN.md) records the planned scope, milestones, responsibilities,
dependencies, checklists, risks, and outstanding work. Update it when a task
is completed, reprioritized, split into subtasks, blocked, or newly identified.
Keep the plan consistent with the actual C4 proposal and the latest team
integration decisions.

### Required change sequence

For every project change, follow this sequence:

1. Make the requested implementation, documentation, configuration, or
   research change.
2. Update [LOG.md](./LOG.md) with the current date, time, timezone, and a
   precise description of the completed change.
3. Update [PLAN.md](./PLAN.md) when the change affects scope, milestones,
   status, dependencies, risks, checklists, or next steps.
4. Review the diff and run the smallest relevant validation.
5. Commit all related changes to the `c4` branch.

The documentation updates and the work they describe should be committed
together so that the repository history remains understandable.

### Commit requirements

- Use a concise, descriptive commit message.
- Commit only related changes; do not include unrelated work from another
  contributor.
- Never commit secrets, credentials, personal data, or restricted datasets.
- Do not add `Co-authored-by` trailers or any other tool attribution to commit
  messages or pull-request descriptions; commits carry the repository owner's
  name only.

Before finishing a work item, verify that:

- The current branch is `c4`.
- `LOG.md` describes the work.
- `PLAN.md` reflects any relevant plan change.
- The committed files match the intended change.
- Validation results and remaining untracked files are understood.

## Confirmed project facts and assumptions

The following facts were confirmed on 14 October 2026:

- PP1 is on 22 October 2026.
- The full assessment duration is 40 minutes: 10 minutes presentation,
  10 minutes demonstration, 15 minutes viva, and 5 minutes marking.
- Presentation and demonstration time are group-level allocations.
- A live demonstration is required; no backup recording is currently required.
- Every member presents their own component.
- No official slide template or slide count is currently confirmed.
- C1, C2, C3, and C4 had no implementation on 14 October 2026; by 19 October
  each has an incomplete prototype (see [PLAN.md](./PLAN.md)).
- The proposal panel (PP1 proposal presentation) asked for the research contribution to be
  strengthened by showing how the student's cognitive level can be raised over time; the
  response is described in [PLAN.md](./PLAN.md) and the Bloom-level progression section below.
- Inter-component JSON schemas and implementations have not been finalized.
- Component datasets or materials may exist individually, but are not officially
  integrated or used yet.

The following must remain explicit assumptions until confirmed by the group or
supervisor:

- Final implementation technologies and deployment approach.
- NLI model or deterministic factual-verification choice.
- Mastery and uncertainty thresholds.
- Bloom-ceiling calculation.
- Rewrite retry and unresolved-claim policy.
- Evaluation concepts, learner profiles, and corpus size.
- Ethics approval requirements.
- Additional PP1 submissions.
- Final shared JSON and REST contracts.

When information is unknown, use a mock or versioned fixture, document the
assumption, and avoid claiming that an integration or result is real.

## Research method

Use Design Science Research as the overall methodology:

1. Identify and motivate the problem.
2. Define the solution objectives.
3. Design and develop the Component 4 artifact.
4. Demonstrate it on representative DSA cases.
5. Evaluate it through controlled technical and learner-based experiments.
6. Communicate the artifact, evidence, limitations, and contribution.

Support the DSR process with comparative experiments. The main research
contribution is the post-generation verification of two dimensions:

- Factual entailment against relevant knowledge-graph evidence.
- Learner-relative cognitive appropriateness based on Bloom constraints and
  prerequisite mastery.

An explanation is faithful only when it satisfies both dimensions.

## Operational definitions to freeze before the main experiment

### Factual labels

Each atomic claim receives exactly one factual label:

- `ENTAILED`: the available graph evidence supports the claim.
- `CONTRADICTED`: available graph evidence conflicts with the claim.
- `UNSUPPORTED`: sufficient supporting or contradicting evidence is unavailable.

### Cognitive labels

Each atomic claim receives one cognitive label:

- `APPROPRIATE`: the claim satisfies the learner-specific constraints.
- `BLOOM_MISMATCH`: the claim exceeds the applicable Bloom ceiling.
- `UNMASTERED_PREREQUISITE`: the claim depends on an insufficiently mastered
  prerequisite.
- `INCONCLUSIVE`: the available learner or pedagogical evidence is insufficient
  for a reliable decision.

A claim may have one factual label and one cognitive label at the same time.
This preserves the distinction between factual validity and cognitive
appropriateness.

### Mastery and uncertainty thresholds

The implementation must define and record:

- The mastery threshold for treating a prerequisite as sufficiently mastered.
- The uncertainty threshold for trusting that mastery estimate.
- The method used when mastery is near a threshold.
- The treatment of missing learner history.
- Whether uncertainty lowers the permitted Bloom ceiling.

Initial thresholds may be pilot parameters, for example:

```text
Prerequisite considered mastered when:
mastery_score >= 0.70 and uncertainty <= 0.20
```

The values must not be presented as universal educational truths. They must be
documented as operational parameters, justified, and tested through sensitivity
analysis.

### Bloom-ceiling calculation

Document an explicit reproducible rule for calculating the learner's Bloom
ceiling. The rule must specify:

- Which learner-state features are used.
- How concept mastery maps to a permitted cognitive level.
- How prerequisite gaps affect the ceiling.
- How uncertainty affects the decision.
- How claim cognitive demand is determined.
- What happens when the decision is inconclusive.

The current learning target must not automatically be labelled as a violation
merely because it is new to the learner.

### Retry and failure policy

Freeze the following before the main evaluation:

- Maximum rewrite attempts.
- Which claims are rewritten.
- Whether valid claims are preserved.
- What happens after the retry limit.
- Whether an unresolved claim is omitted, simplified, escalated, or returned
  as unresolved.
- How unresolved claims are counted in every metric.

The safe default is:

```text
Maximum retries: 3
After failure: do not present the unresolved claim as verified
```

## Bloom-level progression (added 2026-10-20)

The PP1 proposal panel asked for a way to raise the student's cognitive level over time rather
than only a product. The component therefore also treats cognitive appropriateness as a
trajectory. The definitions below extend the frozen definitions above; they are pilot
parameters and must be recorded, justified, and tested like the mastery thresholds.

### Definitions

- **Demonstrated level.** The highest Bloom level (1 Remember to 6 Create) at which the learner
  passed a check question on a concept; 0 means none yet. Stored per concept in the learner
  state under `bloom` (a C4-maintained extension; C2 does not provide it, so the field name and
  update rule need agreement with C2 at integration).
- **Target level.** Demonstrated level + 1 when every direct prerequisite of the concept is
  mastered (same mastery rule as above); otherwise the demonstrated level (consolidate). An
  unseen concept starts at level 1. After a failed attempt at the target level the target is
  retried with full support. The top level is maintained, not exceeded.
- **Progressive mode.** In progressive mode the Bloom ceiling used by the verifier is the target
  level. Static mode (the default) keeps the earlier ceiling rule, so earlier results are unchanged.
- **`BLOOM_STAGNATION`.** An explanation-level violation: no accepted check question at the
  target level. It is repaired by appending a "Check yourself" section and, when rewriting is off,
  reported but not repaired. A claim above the target level is still a `BLOOM_MISMATCH`.
- **Task claims.** In progressive mode a sentence ending in "?" is a task, not a domain claim: it
  asserts no fact (so it is outside the hallucination denominator) but it is judged against the
  Bloom ceiling (so it is in the cognitive-mismatch denominator). Questions, hints, and scaffolds that
  C4 writes itself are recognised by exact regeneration and marked grounded, like the other grounded
  sentences; a lookalike is verified as an ordinary claim.
- **Contingent scaffolding.** Support is full after a failure or at the start, partial after one
  consecutive pass, minimal after two. Support fades with demonstrated success and returns after a
  failure.
- **Demotion.** The demonstrated level drops only after two consecutive failures at a level
  already demonstrated; failing a stretch task above it never lowers the level.
- **Pilot thresholds.** Pass score 0.7, fail score 0.4, two failures to demote, scaffold changes
  after one and two passes. Sensitivity analysis is still required.

### Evaluation rules for progression

- Report RQ4a (faithful and at the target level) on the stress corpus with the same-verifier
  caveat, and RQ4b (progression across sessions) separately.
- **A simulation cannot validate the claim about real students.** Simulated learners encode
  assumptions about how learners learn, so the simulation must include control learner models in
  which progression has no advantage (a flat model) or a disadvantage (a matched model), report where
  the mechanism does not help, and state that learner-model parameters are not fitted to data.
  Paired conditions share random streams. Present simulated results as evidence about the design,
  never as an effect size for students.
- Report the ablations that isolate each part of the mechanism (no stretch, no fading) and the
  sensitivity to study length.
- Evaluate the Bloom-level estimator against labelled items before relying on it, keep a split
  that is never used to tune the lexicon, and state that one annotator's labels have no kappa until a
  second annotator labels the items. Do not present in-vocabulary accuracy as generalisation.
- The human pilot ([PILOT_STUDY.md](./PILOT_STUDY.md)) is the validation. It needs ethics approval
  before any recruitment and must not be described as done until it is.

## Ground truth and evaluation integrity

The verifier must not be evaluated solely by another LLM. Use:

1. Knowledge-graph evidence and explicit rules as the structured authority.
2. Independent human annotations as the primary reference labels.
3. NLI as an automated verification mechanism.
4. LLM judgement only as a secondary exploratory comparison.

Human annotators must receive written guidelines and label factual and
cognitive dimensions independently. Report Cohen's kappa for an independently
annotated subset. If agreement is below the pre-specified `0.70` threshold,
revise the guidelines and re-annotate the affected cases before final
evaluation.

Record:

- Number of explanations and atomic claims.
- Number of DSA concepts and learner profiles.
- Number of cases in every label category.
- Annotator agreement and disagreement resolution.
- Annotation version and dataset version.
- Any excluded or ambiguous cases and the reason for exclusion.

## Experimental matrix

Use matched cases across the following conditions:

| Condition | Factual verification | Cognitive verification |
|---|---:|---:|
| Unverified LLM baseline | No | No |
| Factual-only ablation | Yes | No |
| Cognitive-only ablation | No | Yes |
| Full Component 4 | Yes | Yes |

Keep these factors constant wherever technically possible:

- Generator model and model version.
- Target DSA concept.
- Learner profile.
- Verified learning path.
- Input context.
- Prompt structure.
- Generation parameters.
- Evaluation corpus.

The controlled difference should be the verification and rewriting condition.

## Natural and controlled evaluation cases

Keep two evaluation sets separate:

### Natural-generation evaluation

Use explanations generated under controlled conditions without deliberately
inserting errors. This estimates performance on realistic model output.

### Controlled violation stress test

Inject known examples of:

- Unsupported facts.
- Contradicted facts.
- Incorrect prerequisite relationships.
- Bloom-level mismatches.
- Dependencies on unmastered prerequisites.

Use this set to verify detection of known violation types. Do not use it as a
replacement for the natural-generation evaluation.

Include multiple concepts and learner states:

- All prerequisites mastered.
- One important prerequisite missing.
- Several low-mastery prerequisites.
- Learner ready for higher-order reasoning.
- Factually correct but deliberately too advanced.
- Unsupported or contradicted factual content.

## Metrics and statistical analysis

Use the following definitions:

```text
Hallucination Rate =
  (Unsupported Claims + Contradicted Claims) / Total Factual Claims × 100

Cognitive-Mismatch Rate =
  Cognitively Inappropriate Claims / Total Evaluated Claims × 100

Rewrite Success Rate =
  Successfully Corrected Violating Claims /
  Claims Sent for Rewriting × 100

F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

Report:

- Precision, recall, and F1 for factual violations.
- Precision, recall, and F1 for cognitive violations.
- Results for Bloom mismatches and unmastered prerequisites separately where
  sample size permits.
- Hallucination rate and cognitive-mismatch rate before and after C4.
- Rewrite success and newly introduced violation rate.
- Confidence-tier distribution.
- End-to-end latency, LLM call count, and processing stages.
- Number of failed, inconclusive, and unresolved cases.
- Sample sizes and category counts.

Report descriptive statistics including mean, median, standard deviation where
appropriate, and confidence intervals where feasible. Use paired comparisons
for matched conditions. Select a parametric or non-parametric test only after
checking the data distribution and measurement assumptions. Consider the
Wilcoxon signed-rank test when parametric assumptions are not satisfied.
Report effect sizes and practical relevance in addition to p-values.

Do not impose arbitrary success thresholds before pilot testing. Judge success
through relative improvement over the unverified baseline, reliable detection,
safe rewriting, and maintained or improved clarity and comprehension.

## Learner-based evaluation

Treat the learner study as a final-evaluation activity, not a prerequisite for
the PP1 technical proof of concept.

Before recruitment:

- Prepare participant information and consent documents.
- Obtain the required SLIIT Institutional Research Board or ethics approval.
- Define withdrawal, anonymization, storage, and deletion procedures.
- Minimize learner data and remove unnecessary personal identifiers.
- Avoid sending unnecessary personally identifiable information to external
  model APIs.

Collect:

- Explanation clarity ratings, using a defined Likert instrument.
- Concept-specific comprehension responses.
- Participant and condition identifiers that do not reveal personal identity.

Report participant count, study design, limitations, clarity results,
comprehension results, statistical comparisons, and practical interpretation.

## PP1 implementation priority

For the progress presentation, prioritize a working technical proof of concept:

1. Freeze the input and output schemas.
2. Create mock C1, C2, and C3 fixtures.
3. Implement atomic claim decomposition.
4. Implement factual verification.
5. Implement Bloom and prerequisite verification.
6. Implement typed violation output.
7. Implement targeted rewriting.
8. Implement re-verification and failure handling.
9. Create valid, factual-violation, and cognitive-mismatch demonstrations.
10. Capture initial results and implementation evidence.
11. Prepare slides, demonstration flow, and likely Q&A answers.

Do not allow the open-weight generator comparison, advanced optimization, or
learner recruitment to delay the PP1 prototype.

The group leader's sprint board set an approximate 60% PP1 progress target and
a 22–27 October 2026 presentation window. The board's C4 PP1 evidence,
transcribed into this document, is therefore:

- A generation prompt that explicitly receives the verified path from C3.
- An explicit decision between an NLI model and rule-based graph-edge
  mapping, with rationale.
- A KG entailment checker that flags unsupported claims.
- A Bloom-ceiling prototype.
- A sentence-level targeted rewrite loop.
- Preliminary faithfulness results on 20–30 explanations.

The board's PP2 and PP3 C4 follow-up evidence is:

- Tune entailment-checker thresholds.
- Evaluate the Bloom-level classifier.
- Complete the full faithfulness evaluation.
- Compare the system with and without the rewrite loop.
- Include explanation-clarity questions in the learner study.
- Complete the individual C4 report chapter and novelty-defence preparation.

Shared sprint-board work remains shared: JSON hand-off schemas, mock Neo4j
graph, REST endpoint stubs, weekly hand-off checks, end-to-end demonstration,
unified slides, backup recording, and supervisor dry run.

## Required PP1 demonstration

Show one complete execution:

1. Receive a target path step, learner state, Bloom ceiling, and graph context.
2. Generate or load an explanation.
3. Decompose it into atomic claims.
4. Show factual and cognitive verification results.
5. Show claim-level evidence and typed violations.
6. Rewrite only violating claims.
7. Re-verify the revised content.
8. Show the final explanation and faithfulness report.

The local web workbench (`python3 scripts/run_c4_server.py`) may be used for
this demonstration; it runs the same pipeline as the command-line demo.

Include three contrasting examples:

1. Factually supported and cognitively appropriate.
2. Factually incorrect or unsupported.
3. Factually correct but cognitively inappropriate.

The third example demonstrates the distinctive research contribution.

After the panel comment, add a short progression demonstration in the workbench's Progression tab:
start a session for a learner whose prerequisites are mastered, show the target level one above the
demonstrated level, the faded hints and the check question, simulate an answer, and show the next
session respond (advance after a pass, retry with full support after a failure). Then set a
prerequisite below the mastery threshold to show the policy consolidate instead of advancing.

## Reproducibility and engineering practice

- Version schemas, fixtures, prompts, annotations, and evaluation scripts.
- Keep model credentials in environment variables or a secret manager.
- Do not commit secrets, personal data, or unlicensed datasets.
- Make preprocessing, evaluation, and result generation executable scripts.
- Cache controlled model outputs and record model version and parameters.
- Record all unresolved limitations rather than silently converting failures
  into successful results.
- Keep generation, verification, rewriting, reporting, and evaluation modules
  independently testable.

## Research contribution statement

The contribution is not the independent use of Bloom's taxonomy, LLM
generation, knowledge graphs, or factuality checking. The contribution is the
inspectable post-generation mechanism that treats an explanation as faithful
only when its claims are both knowledge-grounded and appropriate for the
learner's cognitive state, then selectively corrects violations and reports
the evidence and decisions. Following the PP1 panel comment, that appropriateness
is a trajectory: the mechanism verifies that each explanation targets the learner's
next Bloom level and records what the learner demonstrates, so the study can ask
whether verified, level-targeted explanation raises demonstrated cognitive level across
sessions.
