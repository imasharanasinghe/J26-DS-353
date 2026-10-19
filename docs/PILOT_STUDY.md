# Component 4: Human Pilot Study Protocol (Bloom-level progression)

**Status: protocol only. The study has not been run, no participants have been recruited, and
SLIIT Institutional Research Board (IRB) / ethics approval has not been obtained or confirmed.**
Nothing in this document may be presented as a result. The simulated-learner experiment in
[c4/results/PROGRESSION.md](../c4/results/PROGRESSION.md) tests the mechanism under assumptions; this
study is the validation it cannot provide. It follows the learner-evaluation safeguards in
[GUIDELINES.md](./GUIDELINES.md).

## 1. Purpose and hypotheses

Answer RQ4b with real learners: **does explanation that targets the learner's next Bloom level
(progressive C4) raise the Bloom level of what learners can demonstrate over several sessions,
compared with matched-level explanation (current C4) and an unverified LLM baseline?**

Pre-specified hypotheses (stated before any data are collected):

- **H1 (primary).** After the final session, learners in the progressive condition show a higher
  mean Bloom level on the post-test than in the matched condition.
- **H2.** The progressive condition does not reduce comprehension of the target concepts compared
  with the matched condition (non-inferiority within the margin in section 6).
- **H3 (exploratory).** Clarity ratings do not differ between conditions.

The simulation suggests that any advantage is small in few sessions and larger in more, and
that it disappears if stretching does not help real learners. A null or negative human result is a
valid and reportable outcome.

## 2. Design

- **Within-subject, counterbalanced.** Each participant studies three concepts, one per
  condition, so every participant provides a paired comparison; the order of conditions and the
  assignment of concepts to conditions follow a Latin square (3 sequences, equal numbers per
  sequence). This avoids the very large sample a between-subject comparison would need.
- **Conditions.** A: unverified explanation (generator output, no verification). B: current C4
  (verified, capped at the static ceiling, no check question). C: progressive C4 (verified,
  target level from the progression policy, check question, contingent scaffolding).
- **Concepts.** Three DSA concepts from the graph that are similar in difficulty and prerequisite
  structure (proposed: stacks, queues, binary trees), confirmed by the supervisor; concept
  difficulty is balanced across conditions by the Latin square.
- **Sessions.** Four short sessions per concept (about 15 to 20 minutes each, three concepts, so
  about 3 hours per participant over 2 to 3 weeks), or fewer if the pilot's feasibility check
  shows this is too long. The number of sessions is fixed before the study begins.
- **Blinding.** Participants are not told which condition they have; the raters who score answers
  do not see the condition.
- **Generator.** The same generator and prompt for all conditions (GPT-4o if approved, otherwise the
  local model), with the model name, version, and parameters recorded.

## 3. Participants

- Undergraduate students who have completed an introductory data structures course, recruited by
  invitation within SLIIT. Target: **18 to 24 completers** (6 to 8 per sequence), exploratory.
- Inclusion: enrolled, completed the introductory course, adult, consents. Exclusion: prior
  exposure to the experimental system, or being a member of the research team.
- Participation is voluntary, withdrawal at any time without penalty, no academic benefit or
  penalty, and no data on course grades.

### Sample size, stated honestly

With 18 completers a paired comparison at a two-sided 5% level has 80% power only for a standardised
paired effect of about 0.7. The simulation's effect (dz about 0.6 at 8 sessions under the ZPD
model) is an assumption, not evidence about students, so this pilot is **exploratory**: the primary
output is effect sizes with 95% intervals, not a significance verdict. It also informs the sample
size of any larger study.

## 4. Measures

1. **Bloom level demonstrated (primary).** A short test per concept at the end of each session
   and a post-test, with items at each of Bloom levels 1 to 4 (levels 5 and 6 as optional open
   items). Each answer is scored pass or fail at its level by the rubric below; the demonstrated level is the
   highest level passed. Test items are written before the study and are not shown to participants
   in the explanations.
2. **Comprehension.** Concept-specific questions at levels 1 and 2, scored for correctness.
3. **Explanation clarity.** Three five-point Likert items after each session: "The explanation was
   clear", "The explanation matched what I already knew", "The explanation helped me think about the
   concept more deeply".
4. **Process data (no personal identifiers).** Time on task, number of sessions completed, answers to
   check questions.

### Scoring rubric for Bloom level (draft)

| Level | An answer passes when the learner... |
|---|---|
| 1 Remember | states the correct fact or definition |
| 2 Understand | explains it in their own words, with a correct reason or example |
| 3 Apply | produces the correct result on a new small instance |
| 4 Analyze | identifies the relevant parts or differences and how they relate |
| 5 Evaluate | justifies a choice with criteria and trade-offs |
| 6 Create | produces a new, valid design or problem |

Two raters score every answer independently, blind to condition. Report Cohen's kappa on the
Bloom-level scores; if kappa is below the pre-specified **0.70** threshold, revise the rubric and
re-score the affected answers before analysis, as required by the guidelines. Disagreements are
resolved by discussion and the resolution is recorded.

## 5. Procedure

1. Consent and a short background form (course taken, self-rated familiarity); no names stored with
   data, only a participant code.
2. Pre-test on all three concepts.
3. For each concept in the participant's sequence: sessions 1 to S. Each session: read the
   explanation, answer the check questions (progressive condition) or the end-of-session test (all
   conditions), rate clarity.
4. Post-test on all three concepts, a short debrief, and the option to see the other conditions.

## 6. Analysis plan (pre-specified)

- **Primary.** Paired difference in post-test Bloom level, progressive minus matched; 95% bootstrap
  interval, Cohen's dz, and a Wilcoxon signed-rank test (the distribution is ordinal and small).
  Also report progressive minus unverified and matched minus unverified.
- **H2 non-inferiority.** Mean comprehension difference (progressive minus matched) with a 95%
  interval; non-inferior if the lower bound is above -0.5 on the 0 to 1 scale of items passed
  (margin to be confirmed by the supervisor before the study).
- **Order and concept effects.** Report the mean by sequence and by concept; if an effect of order
  or concept is large, say so and analyse within sequence.
- **Missing data.** Analyse completers and report the number who did not finish and why; do not
  impute.
- **Multiplicity.** One primary comparison; everything else is exploratory and labelled so.
- **Reporting.** Participant count, completion, rater agreement, effect sizes with intervals, all
  deviations from this protocol, and limitations.

## 7. Ethics, privacy, and data handling

- **Approval first.** The SLIIT IRB or equivalent ethics approval must be obtained and the approval
  reference recorded here **before** recruitment. Until then no participant contact takes place.
- **Participant information and consent.** Written information sheet and consent form stating the
  purpose, tasks, time, voluntary participation, withdrawal, data use, storage, and who to contact.
- **Minimisation.** Participant codes only; no names, emails, or student numbers with responses.
  The key linking a code to a contact detail, if one is needed to schedule, is kept separately and
  deleted at the end of the study.
- **External services.** No personal data are sent to any external model API; explanations use only
  concept and (coded) learner-state data.
- **Storage and deletion.** Data on a university-approved or encrypted drive; deleted on the
  schedule in the approval. Withdrawn participants' data are removed on request.
- **Risks.** Minimal: time and mild frustration with a hard question. Check questions at a higher
  level than the learner has shown are intended to be difficult; the interface states that wrong
  answers are expected.

## 8. Materials still to prepare

- [ ] Concept and prerequisite confirmation with the supervisor.
- [ ] Test items at each Bloom level for three concepts, reviewed by a second person.
- [ ] Participant information sheet and consent form.
- [ ] Rater guidelines and a calibration set.
- [ ] Ethics application and approval reference.
- [ ] Feasibility run with two to three volunteers from the research group (not counted as data).
- [ ] Decision on the generator (GPT-4o access or the local model).

## 9. Limitations to state in any report

- A small, exploratory sample from one institution; results may not generalise.
- Within-subject order and concept effects are controlled by design but not eliminated.
- The Bloom level of an answer is judged by raters and by a rubric designed by the researcher.
- Short sessions measure short-term change; no claim about retention.
- Self-selected participants may be more motivated than typical students.
