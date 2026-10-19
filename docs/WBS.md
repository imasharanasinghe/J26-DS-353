# Component 4 Work Breakdown Summary

This is a brief user-facing summary of the major work completed for Component
4. It is not a replacement for the detailed [LOG.md](./LOG.md).

## Major work breakdown

The work was completed in these major steps:

1. Created and used the `c4` branch.
2. Read the project README and identified the four-component architecture.
3. Confirmed that Component 4 owns explanation faithfulness, not C1, C2, or C3
   implementation.
4. Read the C1, C2, C3, and C4 proposals, PP1 marks, and research guidelines.
5. Defined factual and learner-relative cognitive faithfulness criteria.
6. Created the C4 work plan, research guidelines, and detailed work log.
7. Reviewed the group sprint-board requirements and recorded PP1 priorities.
8. Inspected the C3 working folder without copying it into the repository.
9. Documented the C3-to-C4 verified-path JSON hand-off contract.
10. Created local C1, C2, and C3-compatible pilot fixtures.
11. Implemented C4 verified-path gating and atomic claim decomposition.
12. Implemented graph-grounded factual verification.
13. Implemented prerequisite mastery and Bloom-ceiling checks.
14. Implemented typed violation reporting, rewriting, and re-verification.
15. Added initial-claim, final-claim, and unresolved-claim reporting.
16. Added automated tests for the C4 proof of concept.
17. Inspected the actual C1, C2, and C3 remote branches and confirmed that all
    three are incomplete.
18. Added adapters for the current C1 CSV, C2 learner-state, and C3 path
    formats.
19. Added C3 hand-off validation before C4 processing.
20. Added a replaceable explanation-generation interface.
21. Added an offline path- and learner-aware template generator.
22. Added valid, factual-error, and cognitive-error demo scenarios.
23. Added a concise human-readable C4 report mode.
24. Improved factual rewriting using graph evidence.
25. Added optional Ollama integration using the local Qwen3 model.
26. Documented the Ollama setup and offline fallback.
27. Installed the Ollama macOS application and confirmed its local API.
28. Temporarily deferred, then completed, the Qwen3 4B model download.
29. Expanded the pilot beyond heap to support arrays, recursion, stacks, and
    queues with selectable target concepts.
30. Ran real Ollama-backed demonstrations for multiple targets.
31. Validated tests, compilation, demos, JSON output, and Git checks.
32. Committed each logical change separately and pushed the work to `c4`.

33. Reviewed the work against the PP1 mark sheet and the C1, C2, and C3 branches.
34. Fixed concept matching, target exemption, and the demo scenarios.
35. Added INCONCLUSIVE handling and a documented mastery/uncertainty rule.
36. Replaced the factual matcher and added known-false graph statements.
37. Added cognitive repair (review guidance), a rewrite trace, and the
    `c4-report/1.0` report with metrics.
38. Added the metrics module, a 28-case stress test with ablations, a
    28-explanation Qwen3 set, and a threshold sensitivity sweep.
39. Documented results and their limitations in
    [c4/results/RESULTS.md](./c4/results/RESULTS.md).
40. Planned and built a local web workbench in seven committed steps.
41. Added a validated service layer shared by the CLI and the web UI.
42. Added a localhost HTTP API server with safe static serving.
43. Built the frontend shell with light/dark theme and status chips.
44. Added claim cards, rewrite trace, metrics, and JSON report views.
45. Added example loaders, a learner mastery editor, verifier settings and
    ablation toggles, and template/Qwen draft generation.
46. Added an evaluation tab with the stress-test, ablation, Qwen, and
    sensitivity results behind a caveat banner.
47. Verified the UI in headless Chrome and added frontend contract tests.
48. Redesigned the interface as a white, minimal editorial theme (serif text,
    hairline rules, plain-text labels) and fixed the metric strip layout.
49. Self-hosted Josefin Sans (SIL OFL) and applied it as the only typeface.
50. Replaced the stark white theme with a warm sand/ivory/teal palette and
    added UX improvements (verdict banner, tooltips, empty-state action).
51. Recoloured the interface to a navy-blue palette.
52. Added the one-call draft, verify, and repair flow (`/api/explain`) and an
    Inputs tab showing the C1, C2, and C3 inputs behind a run.
53. Reworked the explanation into a structured document with learner-specific
    repair, grounded sentences, and report schema 1.1.

Response to the PP1 proposal-panel comment (raise the student's cognitive level
over time; research contribution, not only a product), added 2026-10-20:

54. Defined the response: cognitive appropriateness as a trajectory, with new
    research questions RQ4a and RQ4b (see [PLAN.md](./PLAN.md) and
    [PP1.md](./PP1.md)).
55. Implemented the Bloom progression policy (`c4/progression.py`):
    demonstrated level, target level, contingent scaffolding, demotion.
56. Added a per-concept Bloom record to the learner state with validation.
57. Added target-level verification: progressive mode, `BLOOM_STAGNATION`, task
    claims, grounded check questions and hints, report schema 1.2.
58. Added scaffold fading and target-level check questions to the generators.
59. Built a labelled Bloom item set and evaluated the Bloom estimator (V1 and a
    task-aware V2) with development, test, and indirect-phrasing splits.
60. Built a seeded multi-session simulated-learner experiment with ZPD, flat,
    and matched learner models, ablations, and paired statistics (bootstrap
    interval, Wilcoxon signed-rank, Cohen's dz).
61. Evaluated target-level faithfulness on the stress corpus (RQ4a) and wrote
    `scripts/run_c4_progression.py` and `c4/results/PROGRESSION.md`.
62. Added `/api/session` and `/api/answer`, a Progression tab, and progression
    evidence in the Evaluation tab; checked them in headless Chrome.
63. Wrote the human pilot-study protocol ([PILOT_STUDY.md](./PILOT_STUDY.md));
    it has not been run and needs ethics approval.
64. Updated the proposal ([C4.md](./C4.md)), guidelines, plan, log, README, and
    the PP1 summaries for the new contribution, with its limitations.

## Current demo commands

Offline deterministic generator:

```bash
python3 scripts/run_c4_demo.py --generated --pretty
```

Optional local Qwen3 generator:

```bash
ollama serve
ollama pull qwen3:4b
python3 scripts/run_c4_demo.py --ollama --model qwen3:4b --pretty
```

Focused scenarios:

```bash
python3 scripts/run_c4_demo.py --scenario valid --pretty
python3 scripts/run_c4_demo.py --scenario factual --pretty
python3 scripts/run_c4_demo.py --scenario cognitive --pretty
```

Web workbench (frontend):

```bash
python3 scripts/run_c4_server.py --open
```

Preliminary evaluation:

```bash
python3 scripts/run_c4_eval.py
```

Bloom progression experiments (seeded, no model or network needed):

```bash
python3 scripts/run_c4_progression.py
```

## Current limitation

The real C1 graph, C2 learner output, C3 runtime, shared Neo4j database, and
final production LLM configuration are not yet integrated. The current
fixtures and local Qwen3 option are suitable for a transparent PP1 proof of
concept.

The progression results come from simulated learners with assumed parameters;
the human pilot has not been run, and the Bloom estimator has been scored
against items labelled by one annotator only. The per-concept Bloom record is a
C4 extension of the C2 learner state that C2 does not yet provide.
