# C3 – Path Planner (typed-violation critic)

Plans a learning path for one student and one target topic, and **guarantees the path
follows five teaching rules** before it is sent to C4.

> The AI suggests. The checker decides. Nothing reaches the student unless the checker approves it.

## Quick start

```bash
pip install pytest                      # only needed for tests
python -m pytest -q                     # 36 tests, all should pass
python scripts/run_demo.py --learner L02_intermediate --target heap
python scripts/run_ablation.py          # the PP1 comparison table (mock)
```

No API key is needed for the above: it uses the **mock proposer**, which makes typical LLM
mistakes on purpose so the checker has something to catch. **Mock numbers are for testing
only. Do not present them.**

## Run with a real LLM (your real PP1 numbers)

```bash
pip install anthropic          # or: pip install openai
export ANTHROPIC_API_KEY=...   # or OPENAI_API_KEY=... and C3_LLM_PROVIDER=openai
python scripts/run_demo.py --proposer llm --learner L03_strong_unsure --target dijkstra
python scripts/run_ablation.py --proposer llm
```

Optional: `C3_LLM_MODEL` picks the model. The ablation makes about 60 draft calls plus repair calls.

## The pipeline (file by file)

| Layer | What it does | File |
|---|---|---|
| L0 | Read the topic map (C1) and the learner state (C2) | `c3/kg.py`, `c3/learner.py` |
| L1 | What's still needed, what can start now, what to probe | `c3/frontier.py` |
| L2 | Ordering hint for the proposer (RL later) | `c3/rl/policy.py` |
| L3 | LLM writes K draft paths | `c3/proposer.py`, `c3/prompts.py` |
| L4 | Checker: 5 typed rules | `c3/critic.py` |
| L5 | Fix only the named steps, max 3 rounds | `c3/proposer.py` (`repair`), `c3/edits.py` |
| L6 | Pick the best **verified** path (RL later) | `c3/rl/reranker.py` |
| L7 | Safety net: topological sort | `c3/fallback.py` |
| L8 | JSON for C4 | `PlanResult.to_json` in `c3/pipeline.py` |

## The five rules and their exact error names

| Rule | Error types |
|---|---|
| R1 Prerequisites first | `MissingPrerequisite(heap, needs=binary_tree)` |
| R2 Not too hard, not already known | `TooHard(c, difficulty, level)`, `AlreadyKnown(c)` |
| R3 Clean structure | `UnknownStep`, `DuplicateStep`, `OffPath`, `TargetMissing`, `TargetNotLast` |
| R4 Probe before trusting an unsure topic | `MissingProbe(recursion, before=tree)` |
| R5 Fix wrong beliefs first | `UnremediatedMisconception(heap_is_sorted, before=heap)` |

All thresholds live in `c3/config.py`.

## The ablation set-ups

| Set-up | Meaning |
|---|---|
| A proposer only | Trust the LLM's first draft (what most LLM tutors do) |
| B + critic + repair | C3 without the safety net |
| C full C3 | B + topological-sort fallback |
| D topological sort only | Rule-based baseline, no LLM |

Key number for PP1: **violation rate A vs B**. The fallback rate in C shows how often repair was not enough.

## Swapping mocks for the real thing

- **C1 ready:** export the graph in the shape of `data/mock_kg.json` and pass `--kg path.json`.
  Run the tests: `test_kg_has_no_zpd_dead_ends` warns about concepts no valid path can reach.
- **C2 ready:** export learners like `data/mock_learners.json` and pass `--learners path.json`.
- **RL (PP2):** train IQL on `c3/rl/dataset.py` output, then replace `HeuristicPolicy`
  and `HeuristicReranker`. Keep the rule: RL only chooses among verified paths.

See `docs/interfaces.md` for the exact JSON contracts.
