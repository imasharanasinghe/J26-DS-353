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

## Current limitation

The real C1 graph, C2 learner output, C3 runtime, shared Neo4j database, and
final production LLM configuration are not yet integrated. The current
fixtures and local Qwen3 option are suitable for a transparent PP1 proof of
concept.
