# Component 4 Work Plan

## Scope and responsibility boundary

Component 4 is the **Bloom-Level-Aware Faithfulness for Personalized LLM
Explanations** component (WBS 1.5: Explanation and Interface). Its individual
responsibility starts when the verified learning path, learner state, and
relevant knowledge-graph context are available.

## Current status

- Documentation foundation: **complete for the current proposal and PP1
  sprint-board scope**.
- Research method and evaluation safeguards: documented in
  [GUIDELINES.md](./GUIDELINES.md).
- Work tracking and commit process: documented in
  [GUIDELINES.md](./GUIDELINES.md) and recorded in [LOG.md](./LOG.md).
- C4 implementation: **runnable pilot prototype complete**; the current
  implementation uses deterministic local verification and interface-compatible
  fixtures derived from the documented C3 hand-off.
- C4 pilot validation: **28 tests pass**, Python compilation passes, and the
  offline demos produce readable reports and valid JSON output.
- C4 preliminary evaluation: controlled 28-case/84-claim stress test with
  baseline, factual-only, cognitive-only, and full-C4 conditions, plus a
  28-explanation cached Qwen3 4B natural set and a threshold sensitivity sweep
  ([c4/results/RESULTS.md](./c4/results/RESULTS.md)). Labels are recipe-built,
  not independently human-annotated.
- Local explanation generation: Ollama and Qwen3 4B are installed and the
  adapter uses a short prompt with schema-constrained JSON output. The model
  output remains untrusted and must pass C4 verification.
- C4 research-grade NLI evaluation, real upstream integration, and final
  threshold calibration remain outstanding.
- Untracked upstream proposal and sprint-board files are reference inputs and
  are not included in the C4 documentation commits unless explicitly requested.

### Confirmed PP1 logistics

- Official PP1 date: **22 October 2026**.
- Assessment duration: **40 minutes**.
- Presentation: **10 minutes for the entire group**.
- Demonstration: **10 minutes for the entire group**.
- Viva session: **15 minutes**.
- Marking: **5 minutes**.
- A live demonstration is required.
- No backup recording is currently required.
- Every member must present their own component.
- No official slide template or slide count has been confirmed.

### Confirmed project state

- C1 has an incomplete extraction prototype that currently exports unverified
  CSV candidate concepts and relations; final verification and graph storage
  are not implemented.
- C2 has an incomplete GNN/Monte Carlo Dropout prototype with experimental
  mastery and uncertainty outputs; its graph and data integration remain
  provisional.
- C3 has an incomplete path-planning prototype with a documented verified-path
  JSON hand-off and optional Neo4j loader.
- C4 has a deterministic pilot prototype; no final inter-component schemas,
  graph deployment, or end-to-end integration has been completed.
- Component-specific datasets or materials may exist with individual members,
  but none are officially integrated or being used by the project at present.

### External decisions still requiring confirmation

Do not silently treat these as finalized until the group or supervisor confirms
them:

- PP1 submission requirements beyond the live presentation, demonstration,
  viva, and marking session.
- The final implementation stack and deployment approach.
- The factual-verification implementation choice and NLI model, if any.
- Mastery and uncertainty thresholds.
- Bloom-ceiling calculation.
- Maximum rewrite attempts and unresolved-claim handling.
- C4 evaluation concepts, learner profiles, and corpus size.
- Ethics/Institutional Research Board requirements for the learner study.
- Exact shared JSON schemas and REST interface details.

Until these are confirmed, use versioned mock fixtures and label all
assumptions as pilot decisions.

### Individual C4 responsibility

- Define explanation faithfulness as both factual entailment and
  learner-relative cognitive appropriateness.
- Define factual violation categories and cognitive-appropriateness criteria.
- Define Bloom-ceiling and mastery-threshold logic.
- Generate personalized explanations for verified DSA learning paths.
- Decompose explanations into independently verifiable atomic claims.
- Retrieve relevant knowledge-graph evidence.
- Verify claims as supported/entailed, contradicted, or unsupported.
- Verify Bloom-level suitability and prerequisite mastery.
- Identify and classify typed factual and cognitive violations.
- Assign claim-level confidence tiers.
- Rewrite only violating content.
- Re-verify rewritten content and prevent new violations from being accepted.
- Produce the final explanation, grounding references, and faithfulness report.
- Prepare the technical evaluation corpus and manual claim-level annotations.
- Evaluate hallucination, cognitive mismatch, verifier performance, rewriting,
  baseline/ablation performance, robustness, and learner outcomes.
- Prepare Component 4 documentation, evidence, results, and presentation
  material.

### Shared responsibility

- Agree and freeze inter-component JSON schemas.
- Integrate the REST API and middleware.
- Coordinate Neo4j connectivity and concept identifiers.
- Perform C1-to-C4 and end-to-end integration testing.
- Deploy and demonstrate the complete middleware.

### Explicitly outside individual C4 scope

- C1 constructs and evaluates the pedagogy-typed knowledge graph.
- C2 trains the mastery and uncertainty model.
- C3 generates and verifies the learning path.

Controlled fixtures may be used for development until the real upstream
outputs are available.

## System inputs and outputs

### Required upstream inputs

| Source | Data required | Use in C4 |
|---|---|---|
| C1 | Concept identifiers, relevant graph subgraph, typed relations, Bloom-related properties, prerequisites, evidence/source references | Factual grounding and cognitive checks |
| C2 | Concept-level mastery and uncertainty, learner identifier or anonymized profile | Learner-relative cognitive verification |
| C3 | Verified target concept/path, path metadata, reasoning trace where available | Explanation context and path-oriented generation |
| Shared middleware | JSON contract, REST access, Neo4j access | Interoperability and integration |

### Required C4 output

Return a structured response containing:

- Final verified personalized explanation
- Claim identifiers and claim text
- Factual status for each claim
- Cognitive status for each claim
- Typed violations and correction status
- Relevant knowledge-graph evidence or inline citations
- Confidence tier for each claim
- Rewrite and re-verification trace
- Aggregate faithfulness metrics
- Unresolved violations, if any

## Implementation milestones

### Milestone 1 — Foundation and contracts

- Create a modular C4 structure separating generation, decomposition,
  evidence retrieval, factual verification, cognitive verification,
  rewriting, reporting, and evaluation.
- Freeze versioned input/output JSON schemas with the team.
- Define concept identifiers and evidence references that survive every stage.
- Define claim, violation, confidence, rewrite, and report schemas.
- Define environment-based configuration and keep credentials out of source.
- Select representative DSA concepts with varied prerequisite depth and
  cognitive demand.
- Create controlled mock graph, learner profiles, and verified-path fixtures.
- Track actual upstream branch contracts through adapters rather than importing
  another component's private implementation.

Implementation note: the initial fixtures now exist under `c4/data/` and use
the C3 `PlanResult.to_json` path shape without copying the C3 working folder.

### Milestone 2 — Faithfulness criteria

- Define supported/entailed, contradicted, and unsupported factual labels.
- Define Bloom-level mismatch and unmastered-prerequisite violations.
- Define the learner Bloom ceiling and mastery thresholds as explicit,
  testable rules.
- Ensure the current target is not incorrectly treated as a violation merely
  because it is new to the learner.
- Define high, medium, and low/inconclusive confidence tiers.
- Finalize hallucination and cognitive-mismatch metric definitions.

### Milestone 3 — Explanation pipeline

- Implement the replaceable GPT-4o explanation-generation interface.
- Assemble C1, C2, and C3 context without unnecessary learner PII.
- Generate path-oriented explanations under controlled settings.
- Keep explanation generation replaceable: the offline template generator and
  local Ollama/Qwen3 generator are both available for demonstration.
- Implement structured, deterministic or constrained atomic-claim
  decomposition.
- Preserve claim IDs, source context, and provenance across all stages.

Pilot status: deterministic explanation input and atomic sentence claim IDs are
implemented. A path/learner-aware offline template generator and optional
local Ollama/Qwen3 generator provide replaceable generation boundaries; real
team-wide LLM configuration remains unintegrated.

### Milestone 4 — Factual verification

- Retrieve the smallest relevant C1 subgraph for each claim.
- Implement hybrid NLI and rule-based factual verification.
- Classify every factual claim as supported/entailed, contradicted, or
  unsupported.
- Attach the evidence used for each decision.
- Make insufficient evidence explicit; do not silently accept it.

Pilot status: exact normalized evidence matching is implemented as a baseline.
It is not yet the final NLI-based verifier.

### Milestone 5 — Cognitive verification

- Process C2 mastery and uncertainty data.
- Apply Bloom-ceiling constraints to claim cognitive demand.
- Traverse prerequisite relations needed by each claim.
- Detect unmastered-prerequisite dependencies.
- Distinguish factual validity from cognitive appropriateness.
- Record the rule and evidence behind every cognitive decision.

Pilot status: prerequisite mastery and a documented pilot Bloom-ceiling
heuristic are implemented. Thresholds and Bloom classification require
evaluation and later calibration.

### Milestone 6 — Violation handling and targeted repair

- Generate typed factual and cognitive violation records.
- Rewrite only affected claims or segments and preserve valid content.
- Re-run all relevant verification stages after every rewrite.
- Support a bounded retry policy and explicit unresolved-violation handling.
- Reject, omit, escalate, or safely ground low-confidence claims rather than
  presenting them as verified.
- Calculate rewrite success and detect newly introduced violations.
- Generate the final explanation, citations, and faithfulness report.

Pilot status: bounded targeted replacement, re-verification, unresolved-claim
reporting, and initial/final claim records are implemented.

### Milestone 7 — Technical evaluation

- Build a corpus covering multiple DSA concepts, prerequisite depths, and
  learner states.
- Include mastered-prerequisite, missing-prerequisite, higher-order-ready,
  overly advanced, unsupported-fact, and contradicted-fact cases.
- Generate naturally occurring outputs under controlled settings.
- Inject known violations as a supplementary stress test.
- Prepare independent manual labels for factual and cognitive violations.
- Report Cohen's kappa; revise guidelines and re-annotate if κ is below 0.70.
- Compare the primary unverified GPT-4o baseline with the full C4 pipeline.
- Run factual-only and cognitive-only ablations.
- Where feasible, repeat a reduced corpus with an open-weight generator while
  holding the verification pipeline constant.
- Measure hallucination rate, cognitive-mismatch rate, precision, recall, F1,
  rewrite success, confidence outcomes, latency, and LLM call count.
- Report descriptive statistics and suitable paired tests, including a
  non-parametric alternative when distributional assumptions are not met.
- Report practical effect sizes and limitations, not only statistical
  significance.

### Milestone 8 — Learner evaluation

- Prepare explanation pairs, clarity instrument, comprehension questions,
  consent material, and anonymized data-collection procedures.
- Obtain the required SLIIT Institutional Research Board/ethical approval
  before participant recruitment.
- Conduct the undergraduate learner evaluation.
- Compare clarity ratings and comprehension scores for verified and
  unverified explanations.
- Analyse and document participant, privacy, and study limitations.

### Milestone 9 — Integration and final outputs

- Replace controlled fixtures with actual C1, C2, and C3 outputs.
- Validate REST and JSON contracts and Neo4j evidence retrieval.
- Test concept-ID exchange and complete C1–C4 execution.
- Measure end-to-end performance, reliability, scalability, and API usage.
- Prepare technical documentation, experiment artefacts, result tables,
  architecture diagrams, and reproducibility instructions.
- Complete dissertation sections, final system demonstration, and viva/
  presentation material.

## PP1 priority and demonstration

PP1 is worth 15% and evaluates proof of concept as well as the research gap,
technology application, design, implementation progress, best practices,
requirements, risks, communication, and commercialization.

The group leader's sprint board set the PP1 target at approximately 60%
component progress and placed the PP1 presentation window at 22–27 October
2026. Its C4 tasks are included below and have been transcribed into this plan.

The minimum convincing C4 demonstration is:

1. Input a verified-path step, learner profile, Bloom ceiling, and graph
   context.
2. Generate or load an explanation containing valid and invalid claims.
3. Decompose it into atomic claims.
4. Show factual and cognitive verification results.
5. Show typed violations and supporting evidence.
6. Rewrite only the violating claim(s).
7. Re-verify the revised content.
8. Show the final explanation and faithfulness report.

### PP1 evidence checklist

- [ ] Problem and research gap explained
- [ ] C4 architecture and responsibility boundary shown
- [ ] Versioned input/output schema shown
- [x] Working end-to-end proof-of-concept pipeline
- [x] Successful supported-claim case
- [x] Unsupported or contradicted factual case
- [x] Bloom-level mismatch case
- [x] Unmastered-prerequisite case
- [x] Typed violation report shown
- [x] Targeted rewrite and re-verification shown
- [x] Confidence tier and KG grounding shown
- [x] Initial test/evaluation results shown
- [x] Technology choices justified
- [ ] Functional and non-functional requirements summarized
- [ ] Risks and mitigations explained
- [ ] Commercial/user value explained
- [ ] Completed, delayed, and next tasks stated honestly

### C4 sprint-board commitments

These commitments align the detailed C4 plan with the group leader's sprint
board:

| Sprint-board task | C4 plan location | Required evidence |
|---|---|---|
| Explanation generator prompt taking C3's path | Milestone 3 | Prompt and one structured input/output example |
| Choose NLI model or rule-based edge mapping | Milestone 4 | Decision record, rationale, and initial comparison or configuration |
| KG entailment checker flags unsupported claims | Milestone 4 | Claim-level supported/contradicted/unsupported output |
| Bloom-ceiling check prototype | Milestone 5 | At least one appropriate and one mismatch case |
| Sentence-level rewrite loop | Milestone 6 | Only the violating sentence/claim changes, followed by re-verification |
| Preliminary faithfulness on 20–30 explanations | Milestone 7 | Corpus count, initial metrics, and limitations |
| Tune entailment-checker thresholds | Milestone 7 | Threshold selection and sensitivity results |
| Evaluate Bloom-level classifier | Milestone 7 | Classifier evaluation against manual labels |
| Full faithfulness evaluation | Milestone 7 | Final technical evaluation report |
| Ablation with versus without rewrite loop | Milestone 7 | Rewrite-loop ablation results |
| Explanation-clarity questions in user study | Milestone 8 | Approved instrument and collected clarity responses |
| C4 report chapter and novelty defence | Milestone 9 | Individual report section and viva Q&A preparation |

The sprint board's shared tasks also apply to C4: agree the JSON hand-off
schemas, use the shared mock Neo4j graph, use REST endpoint stubs, check each
handoff weekly, contribute to the end-to-end mock demo, prepare unified slides,
rehearse, record a backup demonstration, and complete the supervisor dry run.

## Immediate seven-day execution plan

This is the highest-priority plan for the week before PP1. Complete the
smallest end-to-end path first; defer optional sophistication until the
demonstration works.

### Day 1 — Freeze the contract and fixtures

- [ ] Create the C4 implementation structure.
- [ ] Freeze the input JSON schema for C1 evidence, C2 learner state, and C3
  verified path.
- [ ] Freeze the output JSON schema for claims, statuses, violations,
  confidence, rewrites, evidence, and the final report.
- [ ] Create mock inputs for one target concept and one learner profile.
- [ ] Add a simple valid path and a path-oriented explanation target.

### Day 2 — Generate and decompose

- [ ] Implement a replaceable explanation-generator interface.
- [ ] Use a deterministic fixture generator if an API is unavailable.
- [ ] Implement atomic-claim decomposition with stable claim IDs.
- [ ] Add schema validation and a readable intermediate result.

### Day 3 — Implement factual verification

- [ ] Implement graph-evidence lookup over the mock KG fixture.
- [ ] Implement the initial NLI/rule-based mapping decision.
- [ ] Support `ENTAILED`, `CONTRADICTED`, and `UNSUPPORTED`.
- [ ] Demonstrate at least one supported and one unsupported/contradicted claim.

### Day 4 — Implement cognitive verification

- [ ] Implement the Bloom-ceiling rule using documented pilot thresholds.
- [ ] Implement prerequisite mastery checks.
- [ ] Support `APPROPRIATE`, `BLOOM_MISMATCH`,
  `UNMASTERED_PREREQUISITE`, and `INCONCLUSIVE`.
- [ ] Demonstrate a factually correct but cognitively inappropriate claim.

### Day 5 — Implement repair and reporting

- [ ] Rewrite only violating claims or sentences.
- [ ] Re-run factual and cognitive verification after each rewrite.
- [ ] Enforce the retry limit and unresolved-claim policy.
- [ ] Produce the final explanation and faithfulness report.
- [ ] Add focused tests for each violation type and the no-violation case.

### Day 6 — Produce initial evidence

- [ ] Run the preliminary corpus of 20–30 explanations or clearly document
  why a smaller pilot was necessary.
- [ ] Record claim counts, violation counts, rewrite success, and unresolved
  cases.
- [ ] Record latency and LLM-call counts if an external model is used.
- [ ] Capture reproducible terminal output or screenshots for the demo.
- [ ] Compare at least an unverified baseline with the repaired pipeline.

### Day 7 — Presentation readiness

- [ ] Prepare the C4 problem and research-gap slide.
- [ ] Prepare the C4 architecture and data-flow slide.
- [ ] Prepare the before/after claim-verification demonstration.
- [ ] Prepare technology and design-justification slides.
- [ ] Prepare implementation progress, risks, and next-work slides.
- [ ] Prepare the commercialization/value slide.
- [ ] Rehearse the demo and record a backup.
- [ ] Complete the supervisor dry run.

### Definition of PP1 readiness

C4 is ready to demonstrate when one command or one documented execution can
show:

```text
structured inputs
  -> explanation
  -> atomic claims
  -> factual + cognitive statuses
  -> typed violations
  -> targeted rewrite
  -> re-verification
  -> final explanation + faithfulness report
```

If the full external integrations are unavailable, present the mock fixtures
honestly as an interface-compatible proof of concept and label real
integration as pending.

## Evaluation definitions

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

The primary comparison is the complete C4 pipeline versus an unverified
GPT-4o explanation using equivalent inputs and generation settings. Secondary
conditions are factual-only and cognitive-only verification. No arbitrary
performance threshold is assumed before pilot testing; success is assessed
through relative improvement, reliable detection, safe rewriting, and
maintained or improved clarity and comprehension.

## Requirements and quality controls

- **Usability:** evaluate clarity and comprehension with undergraduate DSA
  learners.
- **Reliability:** report precision, recall, and F1 against manual labels.
- **Factual faithfulness:** reduce unsupported and contradicted claims.
- **Cognitive appropriateness:** reduce learner-inappropriate claims.
- **Efficiency:** measure LLM calls, processing stages, and latency; avoid
  full-response regeneration when targeted repair is sufficient.
- **Scalability:** keep modules replaceable and observe performance as cases
  and graph context grow.
- **Privacy:** transmit and store only the learner state needed for C4; omit
  unnecessary personal identifiers from external API requests.
- **Interoperability:** validate agreed REST/JSON contracts.
- **Traceability:** map every decision to a claim, rule, evidence, and action.
- **Maintainability:** keep generation, verification, rewriting, and reporting
  independently testable.
- **Reproducibility:** script preprocessing, fixtures, experiments, metrics,
  and result generation; cache controlled outputs where appropriate.

## Commercialization and research outputs

- Position C4 as an API-oriented verification layer for universities, LMS/
  MOOC providers, EdTech companies, and corporate learning platforms.
- Explain value through reduced hallucination, learner-appropriate content,
  auditable evidence, selective repair, and model-agnostic verification.
- Measure prototype API usage and execution cost before proposing pricing.
- Document open-source, patent, dataset, institutional ownership, and
  third-party dependency considerations with the team.
- Preserve evaluation corpora, annotations, user-study instruments, reports,
  and decision logs according to SLIIT policy.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| C1–C3 interfaces are delayed | Use versioned fixtures and replace them during integration |
| LLM output is nondeterministic | Control prompts/settings, cache evaluation outputs, and use deterministic checks |
| Claim decomposition is inconsistent | Constrain structured output and validate its schema |
| NLI evidence is insufficient | Combine NLI with graph/rule checks and report inconclusive status |
| Bloom classification is subjective | Define explicit rules, manual labels, and agreement checks |
| Rewriting introduces new errors | Re-verify every rewrite and cap retries |
| Learner state contains PII | Minimize, anonymize, protect, and avoid unnecessary external transmission |
| User-study approval is delayed | Prepare technical evaluation independently; do not recruit before approval |
| API/GPU budget is exceeded | Cache outputs, limit pilot scale, monitor calls/cost, and use local/open tools where suitable |
| Performance is too slow | Measure call count and latency; use targeted repair and bounded context |
| Low evaluation agreement | Revise annotation guidance and re-annotate affected cases |

## Working conventions

- [LOG.md](./LOG.md) records completed work chronologically with date and time.
- This file records planned, completed, and outstanding work.
- Check an item only after implementation or verification evidence exists.
- [GUIDELINES.md](./GUIDELINES.md) records the frozen
  methodological definitions, evaluation safeguards, PP1 priorities, and
  reproducibility rules that guide this plan.
- Every work change must update [LOG.md](./LOG.md) and this plan where relevant.
- Every work change must be committed to the `c4` branch with a descriptive
  commit message and no co-author or tool-attribution trailer.

## Decision record (pilot, 2026-10-19)

| Decision | Choice | Rationale | Revisit when |
|---|---|---|---|
| Factual verifier | Rule-based graph-statement mapping (content-word Jaccard >= 0.6, `known_false` statements, negation polarity) instead of an NLI model | Deterministic, inspectable, no GPU/API, evidence is a graph statement; stress F1 is stable for thresholds 0.4-0.6 | PP2: add NLI as a second stage and compare against human labels; natural Qwen output is currently over-flagged |
| Claim granularity | One sentence = one claim | Simple, stable claim ids | PP2: atomic-proposition decomposition |
| Mastery rule | mastery >= 0.70 and uncertainty <= 0.25; +/-0.05 margin and missing history INCONCLUSIVE | Conservative, never accepts unknown state | PP2 sensitivity analysis with real C2 output |
| Bloom ceiling | 2, or 3 if all direct target prerequisites mastered and certain | Uncertainty lowers the ceiling; target exempt | PP2: evaluate classifier against manual labels |
| Repair | Graph fact that itself verifies, else review guidance, else drop duplicate; 3 rounds; unresolved reported | Preserves valid claims; true-but-inappropriate claims are not silently swapped | PP2: LLM-assisted rewrite compared in the rewrite-loop ablation |
| Generator | Qwen3 4B via Ollama, schema-constrained JSON | Local, free, reproducible; GPT-4o remains the planned primary generator | When Azure/OpenAI access is agreed |

## Completed since the PP1 review (2026-10-19)

- [x] Demo defects fixed (clean valid/factual/cognitive scenarios; separated
  before/after report).
- [x] Cognitive-violation repair (review guidance) and rewrite trace.
- [x] INCONCLUSIVE cognitive status implemented.
- [x] Metrics module and preliminary stress-test evaluation with ablations.
- [x] Natural Qwen3 evaluation set (28 explanations, cached) and threshold sweep.
- [x] Statistical comparison: exact McNemar and Wilson intervals (paired
  Wilcoxon deferred; needs per-claim continuous scores).

## Outstanding after PP1 preparation

- [ ] Independent human annotation of a corpus subset and Cohen's kappa
  (stress labels are currently recipe-built).
- [ ] NLI second-stage verifier and atomic-claim decomposition; re-measure the
  natural set against human labels.
- [ ] Evaluate the Bloom estimator against manual labels.
- [ ] GPT-4o baseline and open-weight generalisation comparison.
- [ ] Real C1/C2/C3 integration and shared concept identifiers (the branches
  use different identifiers: C1 text names, C2 ASSISTments skill ids, C3
  `mock_kg.json` ids).
- [ ] Learner study (needs ethics approval) and clarity/comprehension measures.
- [ ] Unified slides, supervisor dry run, and viva preparation (the workbench
  run-sheet is in [c4/README.md](./c4/README.md)).
- [ ] Frontend follow-ups: group-level integration page once the shared REST
  contract exists, and an accessibility pass with a screen reader.

## Web workbench (frontend) - added 2026-10-19

A local, dependency-free web UI so the C4 pipeline can be demonstrated
interactively (standard-library server + vanilla HTML/CSS/JS; no npm, no cloud).

- [x] Step 1: transport-independent service layer (`c4/service.py`) with input
  validation, tested without a server.
- [x] Step 2: HTTP API server (`/api/meta`, `/api/verify`, `/api/generate`,
  `/api/results`, `/api/health`) bound to localhost.
- [x] Step 3: frontend shell (layout, theme, input panel).
- [x] Step 4: verification views (claim cards, rewrite trace, metrics, final text).
- [x] Step 5: scenarios, learner editor, and generator (template/Qwen) controls.
- [x] Step 6: evaluation tab (stress test, ablations, sensitivity, caveats).
- [x] Step 7: documentation, demo script, and final validation.
- [x] Visual redesign (2026-10-19): white editorial theme, serif/mono typography,
  hairline rules, no cards, pills, gradients, or dark mode.
- [x] Navy-blue palette (cool blue-grey background, navy masthead and accent) and UX pass (verdict banner, tooltips, empty-state
  action) replacing the stark white theme (2026-10-19).
- [x] One-call draft + verify + repair (`Workbench.explain`, `POST /api/explain`,
  "Draft + verify" buttons) so the generation stage is part of the automatic
  flow (2026-10-19).
- [x] "Inputs (C1, C2, C3)" tab showing the path, learner state, and graph
  evidence behind a run, labelled as fixtures (2026-10-19).
- [x] Structured explanation and concrete repair (path diagram, learner-specific
  review/check guidance, misconception correction, Bloom deferral); grounded
  sentences excluded from rate denominators; report schema 1.1; document-style
  UI (2026-10-19).
- [ ] Replace the rule-based word matching with an NLI second stage so faithful
  paraphrases are not flagged unsupported; re-measure against human labels.
- [ ] GPT-4o generator (`c4/explainer.py`, key via environment variable) for the
  primary baseline and experiments; Qwen is the PP1 stand-in.
- [x] Typography (2026-10-19): Josefin Sans everywhere, self-hosted under
  `c4/web/fonts/` with its SIL OFL licence (no external font requests).

## Bloom-level progression (response to the PP1 proposal-panel comment) - added 2026-10-20

Panel comment: strengthen the research contribution and suggest how the student's
cognitive level can be raised over time, rather than only building a product. Response:
cognitive appropriateness becomes a **trajectory**. C4 verifies that an explanation is
faithful *and* targets the learner's next Bloom level, and the study asks whether this
raises demonstrated levels across sessions (RQ1 faithfulness at the target level; RQ2
progression across sessions). Design and status are in [PP1.md](./PP1.md).

- [x] Step 1: progression policy (`c4/progression.py`): demonstrated level, target level
  (current + 1 when prerequisites are mastered), contingent scaffolding, demotion rule.
- [x] Step 2: per-concept Bloom state in the learner state (`bloom` block), validated by the
  service; fixture extended. C2 does not provide this field yet: C4 keeps it as an
  extension and the shared contract must be agreed.
- [x] Step 3: target-level verification (`progressive` mode), `BLOOM_STAGNATION`, task
  claims, report schema 1.2.
- [ ] Step 4: check questions at the target level and scaffold fading in the generator.
- [ ] Step 5: Bloom-level classifier evaluation against a labelled item set (dev/test split).
- [ ] Step 6: simulated-learner multi-session experiment (conditions A, B, C) with paired
  statistics and learner-model sensitivity.
- [ ] Step 7: result files and `RESULTS.md` section from a reproducible script.
- [ ] Step 8: service and API support for sessions; workbench Progression tab.
- [ ] Step 9: human pilot-study protocol (cannot run without ethics approval).
- [ ] Step 10: update the proposal (`docs/C4.md`), WBS, guidelines, README, and PP1 summaries.
