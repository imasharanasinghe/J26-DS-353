# Component 4 Work Breakdown Summary

This is a brief user-facing summary of the major work completed for Component
4. It is not a replacement for the detailed [LOG.md](./LOG.md).

## A–Z progress

- **A — Branch:** Created and used the `c4` branch.
- **B — Background:** Read the project README and identified the four-component
  architecture.
- **C — Component scope:** Confirmed that Component 4 owns explanation
  faithfulness, not C1, C2, or C3 implementation.
- **D — Documents:** Read C1, C2, C3, C4, PP1 marks, and project guidelines.
- **E — Evaluation plan:** Defined factual and learner-relative cognitive
  faithfulness criteria.
- **F — Fixtures:** Created local C1, C2, and C3-compatible pilot fixtures.
- **G — Graph evidence:** Added graph-grounded factual checking.
- **H — Handoff:** Inspected the C3 working folder and documented its JSON
  hand-off contract without copying it.
- **I — Interfaces:** Added adapters for the actual incomplete C1, C2, and C3
  branch shapes.
- **J — JSON:** Added structured claim, verification, and result output.
- **K — Knowledge checks:** Added prerequisite mastery and Bloom-ceiling checks.
- **L — LLM boundary:** Added a replaceable explanation-generation interface.
- **M — Mock generator:** Added an offline path- and learner-aware generator.
- **N — Neo4j review:** Inspected the C3 Neo4j loader and kept Neo4j optional
  until the shared database is available.
- **O — Ollama:** Added optional local Ollama integration using Qwen3.
- **P — Pipeline:** Implemented path validation, claim decomposition, checking,
  rewriting, and re-verification.
- **Q — Qwen3:** Documented `qwen3:4b` as the free local demo model.
- **R — Rewriting:** Added evidence-based correction for factual violations.
- **S — Scenarios:** Added valid, factual-error, and cognitive-error demos.
- **T — Tests:** Added automated tests for the pipeline, adapters, and
  explanation-generation boundary.
- **U — Upstream status:** Recorded that C1, C2, and C3 are incomplete and are
  not being presented as finished.
- **V — Verification report:** Added concise human-readable demo output.
- **W — Work tracking:** Maintained separate commits for logical changes and
  updated project documentation.
- **X — eXecution:** Validated demos, tests, compilation, and JSON output.
- **Y — Yield:** Produced a runnable C4 proof of concept for PP1.
- **Z — Zero false claims:** Kept real integrations, final thresholds, and
  research-grade evaluation explicitly marked as future work.

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
