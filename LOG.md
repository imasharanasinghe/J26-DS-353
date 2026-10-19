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

### 2026-10-19 02:52:00 +05:30
- Step 2: added `c4/server.py`, a localhost-only standard-library HTTP server with `GET /api/health|meta|results`, `POST /api/verify|generate`, and a static file handler restricted to `c4/web` (path-traversal safe, `nosniff`, `no-store`). Request bodies are capped at 64 KB; validation errors return 400, an unavailable Ollama returns 503.
- Added `scripts/run_c4_server.py` (`--port`, `--open`) and a placeholder `c4/web/index.html` so the static route can be tested before the real UI exists.
- Added `tests/test_server.py` (live server on an ephemeral port: round trip, bad JSON, oversize body, unknown routes, traversal) and an unreachable-Ollama test. 56 tests pass.
- Verified the running script manually with curl against `/api/health` and `/api/verify`.
- The server has no authentication; it binds to 127.0.0.1 and is documented as not for network exposure.

### 2026-10-19 03:08:00 +05:30
- Step 3: built the frontend shell in `c4/web/` (`index.html`, `styles.css`, `app.js`): responsive two-column layout, automatic light/dark theme, status chips for the API and Ollama/Qwen, target and learner-preset selectors, learner mastery summary chips, explanation editor with a character counter, and a pipeline stage indicator. The JavaScript builds the DOM with `textContent` only (no `innerHTML`) so server or user text cannot inject markup.
- The shell already calls `/api/meta`, `/api/health`, and `/api/verify`; the full result renderer follows in step 4.
- Checked the page with headless Chrome (screenshot) and `node --check`.
- Found by that check that the demo-learner preset contained `linked_list`, which is not in the pilot graph, so the service would have rejected it on Verify. Presets are now restricted to graph concepts and a test verifies that every preset and scenario round-trips through `verify`. 57 tests pass.

### 2026-10-19 03:25:00 +05:30
- Step 4: added the verification result views to `c4/web/app.js` and `styles.css`: metric tiles (Bloom ceiling, hallucination and cognitive-mismatch rate before and after, rewrite success, new violations, latency), claim cards with factual and cognitive badges, confidence tier, matched concepts, graph evidence and a plain-language reason for each typed violation, a before/after rewrite trace, the re-verification cards, the final explanation, unresolved and review-first notices, and the JSON report with a download button.
- Unresolved claims are shown in amber and explicitly labelled as not presented as verified, matching the failure policy in [GUIDELINES.md](./GUIDELINES.md).
- Added a `#run` URL hash that runs the default case on load, used for demos and for headless-Chrome screenshots, which I used to check the layout. Widened the metric tiles after the screenshot showed the rate values crowding.
- The verifier numbers shown in the UI come from the same `/api/verify` response as the CLI, so both interfaces report identical results.

### 2026-10-19 03:55:00 +05:30
- Step 5: added interactive controls to the workbench.
  - Example buttons (Mixed, Supported, Contradicted, Too advanced) load the same target-aware sentences as the CLI scenarios.
  - Learner editor: per-concept mastery and uncertainty sliders with a tick box to simulate missing history; any edit switches the preset to "Custom (edited)". Learner values are sent to the verifier unchanged.
  - Verifier settings: factual, cognitive, and rewrite toggles, max rewrite rounds, and mastery and uncertainty thresholds. Switching a check off reproduces the factual-only and cognitive-only ablations interactively.
  - Draft generators: "Template" and "Qwen (Ollama)" fill the explanation box; the Qwen button is disabled with a hint when Ollama or the model is unavailable, and the prompt actually sent to the model is shown in a collapsible block.
- Verified in headless Chrome with a scripted run: editing Binary Trees mastery to 0.95 flips the "true but too advanced" claim to verified; disabling the rewrite loop leaves the contradicted claim unresolved and labelled as not verified; template generation and target switching reset state correctly. Checked the editor layout in a screenshot.
- Added `tests/test_frontend.py` (ids used by the script exist in the page, no `innerHTML`, only local assets). 60 tests pass.

### 2026-10-19 04:20:00 +05:30
- Step 6: added the Evaluation tab to the workbench. It lazily loads `/api/results` and shows the stress-test conditions as paired bars (hallucination and cognitive-mismatch rate) and a table with Wilson intervals and exact McNemar results, detection precision/recall/F1 per dimension, rewrite statistics, the cached Qwen3 natural set with before/after examples, the entailment-threshold sensitivity table with the default highlighted, and a limitations list.
- The tab opens with an amber banner repeating the caveats (recipe-built labels, same-verifier post-repair rates) so the numbers cannot be shown without them. A `#eval` URL hash opens the tab directly.
- `scripts/run_c4_eval.py` now also writes `c4/results/sensitivity.json` so the tab and the markdown report use the same data; regenerated `c4/results/` (only latency values changed in the existing files).
- Simplified the frontend contract test for the tab ids. Checked the tab in a headless-Chrome screenshot. 60 tests pass.

### 2026-10-19 04:32:00 +05:30
- Added a Cmd/Ctrl+Enter shortcut in the explanation box to run the verifier and a tooltip on the button; no behaviour change otherwise. Syntax-checked the script; 60 tests pass.

### 2026-10-19 04:45:00 +05:30
- Step 7: documented the web workbench in [c4/README.md](./c4/README.md) (how to start it, tabs, settings, deep links, API, localhost-only warning) with a six-step PP1 demo run-sheet that includes the learner-relative edit and the rewrite-off ablation.
- Updated [WBS.md](./WBS.md) (items 40-47 and the server command), [PLAN.md](./PLAN.md) (step 7 done, remaining frontend follow-ups), and [GUIDELINES.md](./GUIDELINES.md) (replaced the outdated "no implementation yet" fact with a dated update and noted that the workbench may be used for the required demonstration).
- Final validation: 60 tests pass; Python compilation passes; the server was started from the script and the UI was exercised in headless Chrome.

### 2026-10-19 05:10:00 +05:30
- UI redesign, commit 1 (theme): replaced the workbench styling with a quiet editorial look at the user's request for a white, minimal, less "AI-looking" interface. White paper background (light only, dark mode removed), ink-black text, serif headings and claim text, monospace for labels and ids, hairline rules instead of cards and shadows, square corners, no gradients, no rounded pills; primary action is a solid ink button; status labels, violation labels and evidence are plain coloured text rather than badges; before/after rewrites use a struck-through red line and a green rule instead of tinted boxes; bars use two muted series colours.
- Updated the masthead and section labels in `c4/web/index.html` (no behaviour change) and the favicon.
- Checked the result in a headless-Chrome screenshot; it showed the before/after rate values overflowing their metric tiles, which is fixed in the next commit.

### 2026-10-19 05:25:00 +05:30
- UI redesign, commit 2 (metrics and polish): changed the metric strip to a three-column ruled grid so the before/after rates fit, and formatted percentages without trailing noise (33.3%, 100%). Checked the Verification and Evaluation tabs in headless-Chrome screenshots under the new white theme; the tables, bars, and caveat banner render as intended. No change to results, API, or tests (60 pass).

### 2026-10-19 05:45:00 +05:30
- Font change, commit 1 (assets): vendored Josefin Sans (variable roman and italic TrueType, about 250 KB, with its SIL Open Font License text) under `c4/web/fonts/` and declared it with `@font-face` in `styles.css`. It is self-hosted instead of loaded from Google Fonts so the live demo works offline and no request leaves the machine; the page still references only local assets.
- The server now sends `font/ttf` for font files. Added tests for serving the font and for the licence shipping with it. The font is not applied yet; that is the next commit.

### 2026-10-19 05:58:00 +05:30
- Font change, commit 2 (apply): set Josefin Sans as the single typeface for every element (headings, body, labels, inputs, tables, JSON) through one `--font` variable; the old serif and monospace variables now alias it. Retuned sizes and weights for Josefin's small x-height: light 300 for headings, metric values and the final explanation, larger body, claim, label and table text, and 600 for emphasis.
- Verified in a headless-Chrome screenshot that the self-hosted font loads and renders on the Verification view. 62 tests pass.

### 2026-10-19 06:20:00 +05:30
- Palette redesign, commit 1 (theme): the pure white page with hairline rules made the structure hard to see, so the theme now uses a warm sand background with ivory panels, a dark-teal masthead, and a single teal accent. Inputs, results, claims, rewrites, metrics, JSON, and evaluation sections are separate panels with a subtle border and soft shadow (no gradients, no glow); claims carry a green or red left bar so pass/fail scans at a glance; status labels are tinted tags with small radius; the pipeline is a numbered stepper that fills with check marks; tabs are buttons that lift onto a panel.
- Kept Josefin Sans and all behaviour. Matched the favicon to the masthead colour and moved the section numbers into styled step markers. Checked a headless-Chrome screenshot of the verification view. 62 tests pass.

### 2026-10-19 06:45:00 +05:30
- Palette redesign, commit 2 (UX): added a plain-language verdict banner above the metrics ("2 of 3 claims needed repair, and now all pass", with the violation types and rounds; amber and explicit when claims remain unverified), tooltips on every status label and violation tag, a "Verify the example now" button in the empty state, `aria-busy` while verifying, automatic scroll to the results on narrow screens, and a loading message on the Evaluation tab.
- Re-ran the scripted headless-Chrome interaction test: empty-state button runs the verifier, the three verdict states render correctly (repaired, nothing to repair, unresolved with rewrite off), 22 tooltips are present, and the Evaluation tab renders its six sections. Checked screenshots of the verification and evaluation views. 62 tests pass.

### 2026-10-19 07:05:00 +05:30
- Recoloured the workbench from teal and warm sand to navy blues at the user's request: navy masthead, cool blue-grey page background, pale blue panels, royal-navy accent for the primary button, step markers, tabs, focus rings, links and chart series, and cool-toned shadows and borders. Pass, fail, and warning colours stay green, red, and amber because they carry meaning. Favicon matches the masthead. Layout, font, and behaviour are unchanged; checked a headless-Chrome screenshot. 62 tests pass.

### 2026-10-19 07:30:00 +05:30
- Removed the `Co-authored-by` trailer from the 16 commit messages that carried it (the commits made since the web-workbench work began, one of which was already pushed to `origin/c4`) so that commits show the repository owner only. File contents and authorship were not changed; only commit messages were rewritten, so those 16 commits have new hashes.
- Kept a local safety branch, `c4-backup-before-trailer-cleanup`, holding the pre-rewrite history.
- Updated [GUIDELINES.md](./GUIDELINES.md) and [PLAN.md](./PLAN.md), which previously required that trailer, to say that commits carry no co-author or tool-attribution trailer.

### 2026-10-19 13:40:00 +05:30
- Made the generate-then-verify flow a single call, matching C4.md Stage 2 (the draft is part of the component and is never delivered unverified). Added `Workbench.explain()` in `c4/service.py` and `POST /api/explain` in `c4/server.py`; the report carries the generator name, the prompt, and the draft as `original_explanation` next to the verified `final_explanation`.
- The workbench has a "Fully automatic" row with "Draft + verify (template)" and "Draft + verify (Qwen)"; the Qwen button is disabled while Ollama is offline. Documented in `c4/README.md`.
- Added service and endpoint tests, including an unreachable-generator case. 65 tests pass. Not exercised in a browser in this session.
- Limitations: the generator is still the template or local Qwen3 4B; the proposal's primary generator (GPT-4o) is not implemented, so Qwen results must not be presented as the final effect size. C1/C2/C3 inputs remain fixtures.

### 2026-10-19 14:10:00 +05:30
- Added an "Inputs (C1, C2, C3)" tab to the workbench so the three upstream inputs can be shown to the panel, as the PP1 demonstration in [GUIDELINES.md](./GUIDELINES.md) step 1 requires (target path step, learner state, graph context). It shows the C3 verified path (steps, kinds, difficulty, prerequisites, verified flag and source), the C2 mastery and uncertainty per concept, and the C1 true and known-false statements for the concepts on the path. It follows the selected target and learner state (including edits) while open, and labels C1 and C3 as fixtures.
- `/api/meta` now returns each target's `path` and `graph_context` (`c4/service.py`); no change to verification. Added a service test; 66 tests pass.
- Checked in headless Chrome: the tab renders, switching target and preset updates it, and the "Draft + verify (template)" button runs end to end. The Qwen button was not exercised.
- Observation, not fixed: the Trees step lists `linked_list` as a prerequisite, which is not a concept in the C1 fixture, so it shows as a raw id. This is a fixture inconsistency to resolve at integration.

### 2026-10-19 15:05:00 +05:30
- Reworked the explanation and the repair, because the final text for a weak learner was a true fact followed by a generic sentence ("review the earlier concepts on your verified learning path...") that explained nothing.
- Explanation: the draft is now a structured document (path diagram, About the concept, Before you start, Where you stand, Refresher, Common mistakes) with no length limit (2000 -> 20000 characters; request limit 64 -> 256 KB). Headings are structure and every sentence under them is a claim; the path line is static only when it equals the line C4 would write for the verified path. The template generator builds it from graph facts and C2/C3 data; the Qwen generator writes the concept section and the same code writes the rest (`compose_explanation` in `c4/explainer.py`). The Qwen prompt now asks for 3 or 4 sentences instead of exactly 2; the cached natural set (`natural_cache.json`) was produced with the earlier 2-sentence prompt and is unchanged.
- Repair (`c4/pipeline.py`): unmastered prerequisite -> `Review <concept> first: your mastery is 0.00, below the 0.70 this path needs, and it is a prerequisite of <target>.`; uncertain or missing history -> a quick-check sentence with the mastery and uncertainty values; contradicted misconception -> `Common mistake: "..." is false.` plus a verifying graph fact; Bloom mismatch -> a sentence saying it is saved for later plus a verifying fact; duplicates are dropped. Graph prerequisites are now also usable as evidence ("Before X, you need Y.").
- New `c4/grounding.py` holds the sentences C4 writes from learner, path, and graph data. The verifier recognises them by exact regeneration (a lookalike is still verified) and marks them `source: "grounded"`; they are excluded from the hallucination and cognitive-mismatch denominators so they cannot dilute the rates.
- Report schema bumped to `c4-report/1.1` (adds `final_layout` and per-claim `source`; the service adds a `visual` block). Interface: the final explanation is a document with a colour-coded path diagram, section icons, a status mark per sentence, numbered graph citations, and a copy-as-Markdown button, shown above the claim-level detail.
- Re-ran `scripts/run_c4_eval.py`. Detection is unchanged (precision, recall, F1 all 1.0 on the recipe-built corpus) and full C4 still reaches 0% after repair. The factual-only and cognitive-only ablation rates after repair rose (cognitive 21.43 -> 28.12, hallucination 17.81 -> 24.53) only because C4's own sentences no longer enlarge the denominators. These labels are still recipe-built, not human-annotated.
- 76 tests pass (10 new). Checked in headless Chrome with the template generator, and the real Qwen3 4B generator through the API (stack target, weak learner). The Qwen button in the UI was not clicked.
- Limitations: factual checking is still rule-based word matching, so a faithful paraphrase of a graph fact can be flagged unsupported (a real Qwen run showed this); the graph facts and known-false statements are still C4's own fixtures; GPT-4o is still not implemented.

### 2026-10-19 15:30:00 +05:30
- Fixed the alignment of the final-explanation document in the workbench: wrapped sentences no longer flow back under their status icon. Each sentence is now a two-column grid (fixed icon column, text column), section-heading icons share the same 24 px column and a 12 px gap so their centres line up with the sentence icons, and the top bar groups the counts on the left and the copy button on the right. CSS and markup only; no behaviour change. Checked in a headless-Chrome screenshot at 1300 px; 76 tests pass.
