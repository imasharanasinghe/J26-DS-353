# Work Log

This log records the work completed for Component 4 and the associated project activities.

## 2026-10-14

### 15:42:51 +05:30
- Created and switched to the `c4` Git branch.

### 15:43:49 +05:30
- Read [README.md](./README.md).
- Identified the project purpose, overall architecture, four research components, shared pedagogy-typed knowledge graph, and Component 4 responsibility.

### 15:47:49 +05:30
- Read [c4.md](./c4.md).
- Reviewed the Component 4 proposal, including its research problem, objectives, methodology, architecture, dependencies, evaluation metrics, implementation responsibilities, and planned schedule.

### 15:47:49 +05:30
- Located and read [pp1marks.md](./pp1marks.md).
- Identified the Progress Presentation 1 assessment criteria: research gap and proof of concept, knowledge and technology application, solution implementation, communication, and commercialization.
- Determined that the presentation requires evidence of an implemented proof of concept, not only proposal material.

### 15:49:40 +05:30
- Created this `LOG.md` file.
- Established the practice of recording each subsequent work item with its date, time, and a concise description.

### 15:50:39 +05:30
- Created [PLAN.md](./PLAN.md) as the forward-looking work plan for Component 4.
- Added PP1 priorities, implementation milestones, upstream dependencies, evidence requirements, risk controls, and working conventions.

### 15:53:55 +05:30
- Read [C1.md](./C1.md), [C2.md](./C2.md), [C3.md](./C3.md), and [c4.md](./c4.md) completely for a cross-component responsibility audit.
- Compared the three upstream component proposals and the complete Component 4 proposal against [PLAN.md](./PLAN.md).
- Identified omitted Component 4 responsibilities and planning details, including confidence tiers, KG citations, exact schemas and requirements, privacy and efficiency controls, manual annotation and agreement, controlled violation cases, ablations, open-model generalization, learner-study approval, statistical analysis, documentation, and shared integration boundaries.
- Replaced [PLAN.md](./PLAN.md) with a complete C4 work plan aligned with the proposal documents and PP1 marking criteria.
- Documented the rule that every future work change must update the log and relevant plan items, then be committed to branch `c4`.

### 15:59:37 +05:30
- Created [GUIDELINES.md](./GUIDELINES.md).
- Documented the recommended research method, operational claim labels, Bloom-ceiling and mastery-threshold decisions, retry policy, ground-truth safeguards, experimental matrix, natural versus injected evaluation, metrics, statistical analysis, learner-study controls, PP1 priorities, demonstration requirements, reproducibility rules, and research contribution statement.
- Linked the research guidelines from [PLAN.md](./PLAN.md) so future contributors can follow the same methodological decisions.

### 16:01:28 +05:30
- Updated the renamed [GUIDELINES.md](./GUIDELINES.md) references in [PLAN.md](./PLAN.md) and [LOG.md](./LOG.md).
- Added the project work-management process to [GUIDELINES.md](./GUIDELINES.md), covering the roles of `LOG.md` and `PLAN.md`, the required change sequence, validation, branch usage, and commit requirements.

### 16:03:50 +05:30
- Read the group leader's shared PP1–PP3 sprint board HTML file.
- Compared the shared C4 sprint tasks with [PLAN.md](./PLAN.md) and [GUIDELINES.md](./GUIDELINES.md).
- Confirmed that the overall C4 plan is aligned and added the board's concrete requirements: C3-path prompt, NLI/rule-mapping decision, 20–30 explanation PP1 sample, sentence-level rewriting, PP2 threshold and Bloom-classifier evaluation, rewrite-loop ablation, learner clarity questions, report chapter, and novelty-defence preparation.
- Recorded the shared team tasks that C4 must support: schema agreement, mock Neo4j graph, REST stubs, hand-off checks, end-to-end demo, unified slides, backup recording, and supervisor dry run.

### 16:06:31 +05:30
- Reviewed the current documentation set and confirmed that the proposal, research safeguards, sprint-board alignment, work-log process, and commit process are sufficiently documented for the current PP1 scope.
- Added a current-status section and an immediate seven-day PP1 execution plan to [PLAN.md](./PLAN.md).
- Prioritized implementation evidence over creating additional planning documents.
- Defined daily deliverables for schemas and fixtures, claim decomposition, factual verification, cognitive verification, targeted repair, preliminary evaluation, and presentation readiness.

### 16:11:05 +05:30
- Staged and committed all remaining reference documents: [C1.md](./C1.md), [C2.md](./C2.md), [C3.md](./C3.md), [C4.md](./C4.md), and [PP1MARKS.md](./PP1MARKS.md), together with the group leader's sprint-board HTML file.
- Pushed branch `c4` to the GitHub remote and configured it to track `origin/c4`.

### 16:13:11 +05:30
- Confirmed that the group sprint-board requirements had already been transcribed into [PLAN.md](./PLAN.md) and [GUIDELINES.md](./GUIDELINES.md).
- Removed the redundant sprint-board HTML file and its broken markdown links while preserving the captured PP1–PP3 requirements.

### 17:11:37 +05:30
- Clarified PP1 logistics: 22 October 2026; 40-minute assessment consisting of 10-minute group presentation, 10-minute group demonstration, 15-minute viva, and 5-minute marking.
- Confirmed that a live demonstration is required, no backup recording is currently required, every member presents their own component, and no official slide template or slide count is confirmed.
- Confirmed that C1, C2, C3, and C4 currently have no implementation and that shared JSON schemas and interfaces are not finalized.
- Recorded that component-specific datasets or materials may exist individually but are not officially integrated or used.
- Recorded unresolved external decisions in [PLAN.md](./PLAN.md) and [GUIDELINES.md](./GUIDELINES.md) instead of making unsupported assumptions.

### 20:46:47 +05:30
- Inspected the C3 working folder at `/Users/reshi/Downloads/c3-path-planner` without copying or modifying it.
- Read its README, hand-off interface documentation, schemas, pipeline, learner and knowledge-graph loaders, fixtures, tests, and demo output.
- Confirmed the C3-to-C4 path contract and reused only that documented contract in new C4 fixtures.
- Created the independent C4 pilot package under `c4/`, including models, deterministic verification pipeline, C3-compatible fixtures, demo script, README, and focused tests.
- Implemented verified-path gating, atomic claim decomposition, factual status checks, cognitive prerequisite/Bloom checks, typed violations, bounded targeted rewriting, re-verification, unresolved-claim reporting, and initial/final claim records.
- Installed the missing pytest runner for validation; 4 focused C4 tests passed, Python compilation passed, and the demo produced valid JSON.
- Recorded that the current deterministic checker and Bloom heuristic are pilot baselines, not final research-grade NLI or calibrated models.

### 14:45:00 +05:30
- Audited the available remote component branches: `origin/Component1_KG`,
  `origin/component2-gnn-student-model`, and `origin/c3_pathplanner`.
- Confirmed that C1 currently exports unverified CSV candidates, C2 exposes
  experimental mastery/uncertainty outputs, and C3 provides the verified-path
  JSON contract plus an optional Neo4j loader; none of the branches is complete.
- Added C4 adapters for the current C1 CSV shape, C2 single/collection learner
  shapes, and C3 path validation.
- Added an offline path/learner-aware explanation-generation boundary and
  optional generated-demo mode without claiming that an external LLM is
  integrated.
- Updated the plan to reflect the actual incomplete upstream branch status.

## 2026-10-18

### 14:45:00 +05:30
- Audited the three available component branches directly from Git:
  `origin/Component1_KG`, `origin/component2-gnn-student-model`, and
  `origin/c3_pathplanner`.
- Confirmed that all three are incomplete: C1 exports unverified CSV
  candidates, C2 has an experimental learner model, and C3 has a path-planning
  prototype with a documented verified-path contract.
- Added C4 adapters, C3 hand-off validation, an offline explanation generator,
  focused demo scenarios, a readable report, and graph-evidence factual repair.
- Committed each logical change separately and pushed the changes to
  `origin/c4`.

### 15:10:00 +05:30
- Added an optional local Ollama explanation generator using the Qwen3 model
  through Ollama's local HTTP API.
- Added `--ollama` and `--model` options to the C4 demo.
- Added tests for the personalization context included in the Ollama prompt.
- Confirmed that Ollama is not currently installed on this Mac; the integration
  is implemented but requires local installation and model download before use.
- Documented the offline fallback and Ollama setup in [c4/README.md](./c4/README.md).

### 15:20:00 +05:30
- Created [WBS.md](./WBS.md) as a brief user-facing A–Z summary of the major
  project and C4 implementation steps.
- Kept [LOG.md](./LOG.md) as the detailed AI-agent work record and
  [PLAN.md](./PLAN.md) as the forward-looking work plan.
- Validated the repository with 9 passing tests, Python compilation, demo
  execution, JSON validation, and `git diff --check`.

### 15:48:00 +05:30
- Resumed the interrupted Ollama setup after the network interruption.
- Installed the official Ollama macOS application and confirmed that its local
  API responds on `localhost:11434`.
- Deferred downloading the approximately 2.5 GB Qwen3 model because local
  storage is currently unavailable.
- Confirmed that the repository's offline deterministic generator and all C4
  demos remain usable without the model download.

### 2026-10-19 01:30:00 +05:30
- Resumed and completed the Qwen3 4B download through the locally installed
  Ollama application.
- Expanded the C4 pilot graph beyond heap to include arrays, recursion, stacks,
  and queues with graph facts and prerequisites.
- Added target selection to the demo and generated prerequisite paths for
  selected concepts.
- Fixed target-aware demo scenarios and singular/plural concept matching.
- Ran real Ollama-backed C4 generation for arrays and recursion.
- Configured local Qwen3 generation for non-thinking mode, bounded output, and
  repetition control.
- Switched the integration to Ollama's chat endpoint and added response
  cleanup for planning text and duplicate sentences.
- Added tests for the new multi-target behavior and model-response cleanup.
- Current validation: 11 tests pass; the branch is pushed and clean.

### 2026-10-19 02:30:00 +05:30
- Reviewed C4 against the PP1 mark sheet and the C1, C2, and C3 remote branches. Found that the demo scenarios did not show a clean supported claim or a cognitive-only violation, `pretty` mixed pre- and post-repair claims, cognitive violations could not be repaired, and there was no evaluation evidence.
- Fixed claim-to-concept matching (longest match, so "binary tree" no longer also counts as "tree"); the current target is exempt from the prerequisite check, and every other mentioned concept must be mastered.
- Added INCONCLUSIVE handling for high uncertainty, mastery within 0.05 of the threshold, and missing learner history.
- Replaced exact-substring factual checking with content-word similarity plus `known_false` graph statements, negation polarity, and closest-statement resolution (fixes LIFO vs FIFO false contradiction found during evaluation).
- Replaced the filler rewrite with targeted repair: a graph fact that itself verifies, else prerequisite-review guidance, else removal of a duplicate; added a rewrite trace, `review_first`, per-run metrics, latency, and report schema `c4-report/1.0`.
- Rewrote the demo report to show initial verification, rewrites, and re-verification separately; scenarios no longer edit the learner state.
- Added `c4/metrics.py` (frozen definitions, precision/recall/F1, exact McNemar, Wilson interval), `c4/paths.py`, and `c4/evaluation.py`; added `scripts/run_c4_eval.py` and committed `c4/results/`.
- Evaluation: 28-case, 84-claim controlled stress test (7 concepts x 4 learner profiles; baseline, factual-only, cognitive-only, full C4) and a 28-explanation cached Qwen3 4B natural set, plus an entailment-threshold sensitivity sweep.
- Changed the Ollama generator to a short prompt with schema-constrained JSON output because the 4B model echoed its planning text with the longer prompt.
- Results and limits: see [c4/results/RESULTS.md](./c4/results/RESULTS.md). The stress-test labels are recipe-built (no human annotators, no kappa), post-repair rates use the same verifier, and the natural set shows the rule-based matcher flagging every paraphrased Qwen sentence as not graph-supported.
- Tests: 28 pass; compilation, demo modes (including Ollama), and JSON output validated.
- Rewrote [c4/README.md](./c4/README.md) (fixed the broken run/test section; documented pipeline, parameters, and limitations).

### 2026-10-19 02:40:00 +05:30
- Started the C4 web workbench (frontend) as a stepwise piece of work; recorded the seven steps in [PLAN.md](./PLAN.md).
- Step 1: added `c4/service.py`, a transport-independent `Workbench` with `meta()`, `verify()`, `generate()`, and `results()`. Requests are validated (known target and concepts, mastery/uncertainty in [0, 1], whitelisted config keys with ranges, 2000-character explanation cap) and invalid input raises `ValueError`.
- Moved the demo scenario sentences into the service so the CLI demo and the web UI share one implementation; the CLI output is unchanged.
- Added `tests/test_service.py` (16 cases including parametrised invalid requests). 44 tests pass.
- Corrected the timestamp of the previous log entry (it was written ahead of the clock).

