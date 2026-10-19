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

### 2026-10-19 20:45:00 +05:30
- Wrote `C4PP1.md`, a short viva-ready summary of the work done on the `c4` branch (stages, results table, limitations, next steps), taken from the commit history and `c4/results/RESULTS.md`.
- Moved `C1.md`-`C4.md`, `GUIDELINES.md`, `LOG.md`, `PLAN.md`, `PP1MARKS.md`, and `WBS.md` into `docs/`; only `C4PP1.md` and `README.md` remain at the root. Updated the two code comments that cited `GUIDELINES.md` (`c4/metrics.py`, `c4/evaluation.py`). Links between the moved files are relative and still resolve. Earlier entries above still use the old root paths and are left as the historical record.
- Missed the required change sequence on the first pass (LOG update, validation, commit); done now. 76 tests pass.

### 2026-10-20 00:55:00 +05:30
- Started the response to the PP1 proposal-panel comment ("raise the student's cognitive level over time"). Read [GUIDELINES.md](./GUIDELINES.md), the C4 pipeline, service, evaluation, and fixtures first.
- Step 1: added `c4/progression.py`, a pure-function Bloom progression policy: per-concept demonstrated level (0-6) with an attempt history; target level = demonstrated level + 1 when the concept's prerequisites are mastered, otherwise consolidate; retry with full support after a failed stretch task; contingent scaffolding (full, partial, minimal) that fades with consecutive passes and returns after a failure; demotion only after two consecutive failures on an already demonstrated level (a failed stretch task never lowers the level).
- Added `tests/test_progression.py` (20 tests). 96 tests pass. The thresholds (pass 0.7, fail 0.4, two failures to demote, scaffold fading after one and two passes) are pilot parameters, not validated values.
- Added the "Bloom-level progression" section to [PLAN.md](./PLAN.md) with the ten steps and their status. Nothing in the pipeline uses the policy yet.

### 2026-10-20 01:10:00 +05:30
- Step 2: per-concept Bloom state in the learner state. `c4/data/learner_state.json` gains a `bloom` block (demonstrated level and attempt history per concept; seeded levels for arrays, linked lists, recursion, trees and a first passing attempt on heaps). C2 does not export a Bloom level, so this is a **C4-maintained extension** attached to the C2-shaped learner state; the field name and update rule must be agreed with C2 at integration.
- `Workbench` (`c4/service.py`) validates `learner.bloom` through `LearnerProgress.from_state` (unknown concepts, out-of-range levels, wrong shapes are client errors) and returns it in the learner payloads. Presets without a record get a demo seed (target at Remember with one passing attempt), documented as a demo seed, not learner data. The C2 adapter passes the block through unchanged and still works without it.
- Added 3 tests (service seeding, validation, adapter pass-through). 99 tests pass. No change to verification behaviour yet.

### 2026-10-20 02:05:00 +05:30
- Step 3: target-level verification. New opt-in `C4Config.progressive` (default off, so every existing result is unchanged) and `check_stagnation`. In progressive mode the Bloom ceiling is the learner's **target level** from the progression policy instead of the static 2/3 rule, and the verifier gains an explanation-level violation, **`BLOOM_STAGNATION`**: an explanation with no accepted check question at the target level is not helping the learner progress. The repair appends a "Check yourself" section (faded scaffold hints plus the target-level question) and records it in the rewrite trace as a step on claim `explanation`. With rewriting off the stagnation is reported, not repaired.
- A sentence ending in "?" is a **task** (`source: "task"`) in progressive mode: it asserts no domain fact, so it is ENTAILED and excluded from the hallucination denominator, but it is judged against the Bloom ceiling and counts in the cognitive-mismatch denominator. A question above the target level is a `BLOOM_MISMATCH` and is re-levelled to the target-level question. Questions, hints, and scaffolds that C4 writes itself (`grounding.task_sentence`, hint functions) are recognised by exact regeneration and marked grounded, as before; a lookalike is verified like any other claim.
- Report schema bumped to `c4-report/1.2` (adds `progression`: current and target level, action, scaffold, reason, `stagnation_before/after`, accepted question levels). `summarize` adds `stagnation_before/after`. The service accepts `progressive` and `check_stagnation`.
- Added `tests/test_progressive.py` (22 tests), including that each check-question template is estimated at its own Bloom level and that static mode is unchanged. Re-ran `scripts/run_c4_eval.py`: only latency noise differed, so the stress-test and natural results were not regenerated. 121 tests pass.
- Limitations: the Bloom estimator is the pilot verb-cue matcher (to be evaluated in step 5); the question templates are generic, not concept-specific; stagnation is judged on questions only, not on the style of the explanatory text.

### 2026-10-20 02:30:00 +05:30
- Step 4: scaffold fading and check questions in the generator. In progressive mode `compose_explanation` (`c4/explainer.py`) reads the progression decision and (a) keeps all sections when the scaffold is "full", drops the Refresher and Common-mistakes sections for "partial", and keeps only a one-fact "About" plus "Where you stand" for "minimal"; (b) ends the draft with a "Check yourself" section built by the same `check_section` the repair uses (two hints, one hint, or none, then the target-level question). Static mode is unchanged. The Ollama generator inherits this because it uses the same composition.
- Added 3 tests (detail shrinks full > partial > minimal; every progressive draft ends with the target-level question and is not stagnant; static drafts have no check section). 124 tests pass. Printed the three scaffold levels for the demo learner to check them by eye.
- Limitation: which sections count as scaffolding and how many hints fade at each step are pilot design choices; they are not validated against learners.

### 2026-10-20 03:10:00 +05:30
- Step 5: Bloom-level estimator evaluation. The whole progression contribution rests on estimating a sentence's Bloom level, so it is now measured. Added `c4/data/bloom_items.json` (90 items, 15 per level, written and labelled by the C4 author as a single annotator) with three splits: `dev`, `test` (alternating items within each level), and `hard` (indirectly phrased items with no cue verb, never used for tuning).
- Moved the estimator into `c4/bloom.py`. V1 is the original PP1 verb-cue matcher; V2 uses the standard revised-taxonomy verb lists, applies them only to learner *tasks* (a question or an instruction), and treats a declarative statement as Remember, because V1 reads ordinary text such as "used to solve problems" as an Apply-level demand. V2 is used only in progressive mode, so static-mode results are unchanged (the regenerated stress-test numbers are identical; only the schema fields and timings moved).
- Scores (`c4/results/bloom_classifier.json`, `RESULTS.md` section C): V1 accuracy 52.8% on dev and on test; V2 97.2% on dev, 100% on test; both 16.7% on `hard`. Honest reading: the V2 lexicon was extended after reading dev errors, the test items share the same vocabulary family and author, so the 100% shows in-vocabulary coverage, not generalisation, and the `hard` split shows a verb-cue matcher cannot read indirect phrasing. There is no inter-annotator agreement (no Cohen's kappa): a second annotator and a learned or NLI-based classifier remain outstanding.
- Added `tests/test_bloom.py` (14 tests). 134 tests pass.

### 2026-10-20 04:20:00 +05:30
- Step 6: multi-session simulated-learner experiment (`c4/simulation.py`) for RQ2. A seeded cohort of simulated learners (novice, intermediate, advanced; hidden Bloom capability, learning rate, prerequisite mastery that grows regardless of condition) studies the heap target over several sessions under three paired conditions: **A** unverified (explanation level drawn uniformly from 1-4), **B** current C4 (the same draw, repaired down to the static ceiling), **C** progressive C4 (target level and scaffold from the real `C4Pipeline.progression_decision`, each session ending with a check question whose result updates the Bloom record). Two ablations of C isolate its parts: `C_no_fading` and `C_no_stretch`.
- Because a simulation partly returns its own assumptions, three learner models are run: a ZPD model (stretch within reach teaches best), a **flat** control (level does not matter) and a **matched** control (stretching hurts). Random streams are paired across conditions. Added to `c4/metrics.py`: seeded bootstrap interval for a mean, paired Wilcoxon signed-rank (normal approximation with tie and continuity correction), and Cohen's dz.
- Findings from a 300-learner, 8-session run (full output in step 7): under the ZPD model C gains 0.36 capability levels more than B (95% bootstrap interval 0.29 to 0.43, dz 0.59), but reaches level 3 no sooner (0.07 sessions saved, interval -0.11 to 0.23); the effect is about zero at 4 sessions and grows by 12; stretching is the active ingredient (C versus no-stretch +1.12), contingent fading adds nothing in this learner model (-0.02), the flat control ties exactly, and under the matched control C is no better than B at 8 sessions and worse at 12 (-0.29). The policy also wastes early sessions on learners who start high because an unseen concept starts at Remember.
- Added `tests/test_simulation.py` (10 tests; the suite now takes about 5 s). 144 tests pass.
- Limitations: all learner-model parameters are pilot values, not fitted to real learners; the models encode the theory they test; LLM-driven simulated learners (mentioned in the earlier PP1 summary) are not implemented, so the summaries are corrected in step 10.

### 2026-10-20 05:00:00 +05:30
- Step 7: reproducible result files for the progression work. Added `evaluate_progressive_stress` (RQ1 on the 28-case stress corpus, each case with the learner starting a new concept, at demonstrated level 1, and at level 2: 84 runs) and `scripts/run_c4_progression.py`, which runs RQ1 plus the simulated experiment and writes `c4/results/progression.json` and `c4/results/PROGRESSION.md` (seeded; no model or network).
- RQ1 result (same-verifier caveat): the unverified text and static C4 never contain a question at the target Bloom level (0%, 95% CI 0 to 4.4), progressive C4 does in 84 of 84 runs (100%, CI 95.6 to 100) with 0 runs left with a violation and 0 unresolved claims; hallucination and cognitive-mismatch rates after repair are 0.0%. Static C4's own sentences are judged with the static verifier because they are written for the static ceiling (judging them with the progressive verifier first produced a spurious 18.9% hallucination rate, an artefact of grounded-sentence recognition that was caught and fixed).
- RQ2 result (ZPD learner, 300 learners, 8 sessions): see the log entry for step 6 and `PROGRESSION.md`; the flat control ties exactly, the matched control shows no advantage, fading adds nothing, and the stretch is the active ingredient.
- Added 2 tests (RQ1 outcomes; the report renders every section). 146 tests pass.

### 2026-10-20 05:45:00 +05:30
- Step 8 (service and API): `Workbench.session` runs one progressive teaching session (progressive draft, verification, repair, the policy decision, and the check question with its faded hints) and `Workbench.answer` records an answer to a check question and returns the updated learner plus a preview of the next decision. The server stays stateless: the client sends the learner, including its `bloom` record, each time. New endpoints `POST /api/session` and `POST /api/answer`; `GET /api/results` now also returns `bloom` and `progression`. Inputs are validated (level 1-6, score 0-1, known scaffold, session 1-1000) and rejected with a 400.
- Added 8 service tests and 1 endpoint round-trip test (session, answer, bad answer). 159 tests pass. The browser UI for these endpoints comes next.

### 2026-10-20 07:10:00 +05:30
- Step 8 (workbench UI): added a **Progression** tab. It shows the six Bloom levels with the demonstrated and target levels, the policy decision (action, aim, support, reason), a "Start session" button that calls `/api/session` and renders the verified explanation with its check question and faded hints, three buttons that simulate the learner's answer (answered well, partly, not yet) through `/api/answer`, and a trajectory chart and table of the run. Editing mastery in the left panel switches the policy between advancing and consolidating. Switching target or preset resets the journey.
- The **Evaluation** tab gains the progression evidence before "Known limitations": RQ1 table, RQ2 chart and tables with a learner-model switch (ZPD, flat, matched), sensitivity to study length, and the Bloom-estimator scores; the limitations list now states the single-annotator and simulated-learner caveats. Charts are inline SVG with end labels kept in order.
- Checked in headless Chrome driven over the DevTools protocol: five sessions with the "all prerequisites mastered" preset (advance, advance, advance, fail then retry, pass), the demo learner (consolidate while a prerequisite is unmastered), and the three learner-model buttons; no console errors. The Qwen buttons were not exercised (Ollama offline).
- Made the oversized-request server test tolerate the client seeing the closed connection instead of the 413 response; it failed once in about 25 full-suite runs on a busy machine (a race, not related to this work). Added a frontend wiring test. 160 tests pass.

### 2026-10-20 07:40:00 +05:30
- Step 9: wrote [PILOT_STUDY.md](./PILOT_STUDY.md), the human pilot-study protocol for RQ2: pre-specified hypotheses, a counterbalanced within-subject design over three concepts and three conditions (unverified, current C4, progressive C4), 18 to 24 completers framed as exploratory (80% power only for a paired effect of about 0.7), Bloom-level scoring rubric with two blind raters and Cohen's kappa at the 0.70 threshold, analysis plan, privacy rules, and a materials checklist.
- This is a protocol only. The study was not run, no participants were contacted, and no ethics approval exists; the document says so at the top. Recruitment must wait for SLIIT IRB approval.

### 2026-10-20 08:00:00 +05:30
- Renamed the progression research questions to **RQ4a** (target-level faithfulness) and **RQ4b** (progression across sessions) in the code, result files, workbench, and the pilot-study protocol, because the proposal ([C4.md](./C4.md)) already numbers its research questions RQ1 to RQ3 (verification, cognitive appropriateness, correction). The new questions extend it as RQ4. Result keys in `progression.json` are now `rq4a` and `rq4b`; the earlier log entries above keep the old names as the historical record. Regenerated `PROGRESSION.md`; the numbers are unchanged. 160 tests pass.

### 2026-10-20 09:10:00 +05:30
- Step 10a (proposal and guidelines): updated [C4.md](./C4.md) for the panel response: abstract, a research-gap extension with **RQ4a** and **RQ4b**, objectives, metrics (3.4.7 and Table 5), success criterion 6, a validation subsection (3.5.9: estimator validation, simulated learners with control models, human pilot), the implemented-estimator note in 3.7.4, FR15 to FR17, WBS packages 1.5.8.5 and 1.5.10 (the effort estimate rises from about 162 to about 194 person-days), and two classic references ([18] Vygotsky, [19] Wood, Bruner and Ross, added from memory and to be checked against the sources).
- Added a "Bloom-level progression" section to [GUIDELINES.md](./GUIDELINES.md) freezing the definitions (demonstrated level, target level, `BLOOM_STAGNATION`, task claims, contingent scaffolding, demotion, pilot thresholds) and the evaluation rules, in particular that a simulation cannot validate the claim about real students; extended the contribution statement and the PP1 demonstration with the progression demo.

### 2026-10-20 09:25:00 +05:30
- Step 10b (plan, WBS, README): [PLAN.md](./PLAN.md) status lines updated (160 tests), a results summary and an outstanding list added to the progression section, step 10 marked done; [WBS.md](./WBS.md) gains items 52 to 64 and the progression command and limitation; [c4/README.md](./c4/README.md) gains a "Bloom-level progression" section with the demo run-sheet addition.

### 2026-10-20 09:40:00 +05:30
- Step 10c (PP1 summaries): rewrote [PP1.md](../PP1.md) (panel comment, response, implemented pieces, results, limitations, status, slide text, demo flow, likely questions) to match what is now implemented, and corrected the earlier draft, which described LLM-driven simulated learners (the simulated learners are parametric models) and called the research questions RQ1 and RQ2 (now RQ4a and RQ4b). Updated [COMP4.md](../COMP4.md) (the PP1 viva summary) with the panel response, a Stage 9, the progression results, limitations, and next steps. `C4PP1.md` had been renamed to `COMP4.md` in the working tree; the commit records that rename.

### 2026-10-20 11:00:00 +05:30
- Removed the offline template explanation generator at the user's request: the language model (Qwen via Ollama today, GPT-4o if it is added) is now the only draft writer. Deleted `TemplateExplanationGenerator`; `compose_explanation` now requires the model's body and raises if it is empty; `Workbench` takes a `generator` (default Ollama) and no longer accepts a `source` option; `/api/generate`, `/api/explain` and `/api/session` use it; `scripts/run_c4_demo.py` lost `--generated`; the workbench lost the "Template" and "Draft + verify (template)" buttons. Verifying pasted text, the Evaluation tab, and all simulation and evaluation scripts need no model. Starting a Progression session now needs Ollama online.
- Tests that needed a draft now inject `tests/stubs.py::StubGenerator`, a test double with the interface of the model generator that "writes" the target's graph facts; it is not part of the product. Added a test that composing without a model body is refused. The "Load example" buttons stay: they are verifier test inputs, not a generator. 161 tests pass; the Qwen path was not exercised (Ollama offline).
- Updated the README, PLAN, WBS, and COMP4 wording. The earlier log entries above still describe the template generator as the historical record.
