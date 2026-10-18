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
28. Deferred the Qwen3 model download because approximately 2.5 GB of storage
    was not available.
29. Validated tests, compilation, demos, JSON output, and Git checks.
30. Committed each logical change separately and pushed the work to `c4`.

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

## Current limitation

The real C1 graph, C2 learner output, C3 runtime, shared Neo4j database, and
final production LLM configuration are not yet integrated. The current
fixtures and local Qwen3 option are suitable for a transparent PP1 proof of
concept.
