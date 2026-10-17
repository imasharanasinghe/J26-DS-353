# C3 hand-off formats

Share this with C1, C2 and C4 so everyone builds against the same shapes.

## From C1: knowledge graph

```json
{
  "concepts": {
    "heap": {"name": "Heaps", "difficulty": 4, "prerequisites": ["binary_tree", "arrays"]}
  },
  "misconceptions": {
    "heap_is_sorted": {"affects": "heap", "description": "Thinks a heap's array is fully sorted."}
  }
}
```

- `difficulty` is 1 (easiest) to 5 (hardest).
- `prerequisites` must exist and contain no loops.
- Every concept should have at least one prerequisite no more than 1 level easier than itself. Otherwise no valid path can reach it; the test suite flags this.

## From C2: learner state

```json
{
  "learner_id": "S123",
  "mastery":     {"arrays": 0.9, "recursion": 0.75},
  "uncertainty": {"arrays": 0.05, "recursion": 0.32},
  "misconceptions": ["recursion_no_base_case"]
}
```

- `mastery` is 0 to 1. A concept counts as known at 0.7 or above.
- `uncertainty` is 0 (sure) to 0.5 (no idea). At 0.25 or above, C3 adds a probe.
- Missing concepts are treated as unknown (mastery 0, uncertainty 0.5).

## To C4: verified path

```json
{
  "learner_id": "L05_uneven",
  "target": "priority_queue",
  "verified": true,
  "source": "repaired",
  "path": [
    {"step": 1, "kind": "probe", "id": "recursion", "name": "Recursion", "difficulty": 2, "prerequisites": ["functions"]},
    {"step": 2, "kind": "remediate", "id": "heap_is_sorted", "affects": "heap", "description": "..."},
    {"step": 3, "kind": "learn", "id": "tree", "name": "Trees", "difficulty": 3, "prerequisites": ["linked_list", "recursion"]}
  ],
  "summary": "probe:recursion -> remediate:heap_is_sorted -> tree -> ...",
  "drafts_considered": 3,
  "repair_rounds": [1, 1, 3],
  "violations_found": [{"rule": "R1", "type": "MissingPrerequisite", "concept": "binary_tree", "needs": "tree"}],
  "remaining_violations": []
}
```

- `source` is one of: `draft` (passed first time), `repaired`, `fallback`, `already_known`.
- C4 should only explain paths where `verified` is `true`.
