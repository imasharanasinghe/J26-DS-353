# Component 4 Work Plan

## Scope and responsibility boundary

Component 4 is the **Bloom-Level-Aware Faithfulness for Personalized LLM
Explanations** component (WBS 1.5: Explanation and Interface). Its individual
responsibility starts when the verified learning path, learner state, and
relevant knowledge-graph context are available.

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
- Implement structured, deterministic or constrained atomic-claim
  decomposition.
- Preserve claim IDs, source context, and provenance across all stages.

### Milestone 4 — Factual verification

- Retrieve the smallest relevant C1 subgraph for each claim.
- Implement hybrid NLI and rule-based factual verification.
- Classify every factual claim as supported/entailed, contradicted, or
  unsupported.
- Attach the evidence used for each decision.
- Make insufficient evidence explicit; do not silently accept it.

### Milestone 5 — Cognitive verification

- Process C2 mastery and uncertainty data.
- Apply Bloom-ceiling constraints to claim cognitive demand.
- Traverse prerequisite relations needed by each claim.
- Detect unmastered-prerequisite dependencies.
- Distinguish factual validity from cognitive appropriateness.
- Record the rule and evidence behind every cognitive decision.

### Milestone 6 — Violation handling and targeted repair

- Generate typed factual and cognitive violation records.
- Rewrite only affected claims or segments and preserve valid content.
- Re-run all relevant verification stages after every rewrite.
- Support a bounded retry policy and explicit unresolved-violation handling.
- Reject, omit, escalate, or safely ground low-confidence claims rather than
  presenting them as verified.
- Calculate rewrite success and detect newly introduced violations.
- Generate the final explanation, citations, and faithfulness report.

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
- [ ] Working end-to-end proof-of-concept pipeline
- [ ] Successful supported-claim case
- [ ] Unsupported or contradicted factual case
- [ ] Bloom-level mismatch case
- [ ] Unmastered-prerequisite case
- [ ] Typed violation report shown
- [ ] Targeted rewrite and re-verification shown
- [ ] Confidence tier and KG grounding shown
- [ ] Initial test/evaluation results shown
- [ ] Technology choices justified
- [ ] Functional and non-functional requirements summarized
- [ ] Risks and mitigations explained
- [ ] Commercial/user value explained
- [ ] Completed, delayed, and next tasks stated honestly

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
- Every work change must update [LOG.md](./LOG.md) and this plan where relevant.
- Every work change must be committed to the `c4` branch with a descriptive
  commit message and the required Copilot co-author trailer.
