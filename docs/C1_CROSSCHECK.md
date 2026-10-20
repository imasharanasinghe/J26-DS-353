# C1 cross-check (read-only)

Written for: the C4 team. Source: `origin/Component1_KG` at commit `1118370` (`component1_kg/outputs/concept_nodes.csv` and `relations_verified.csv`), read through `c4.adapters.load_c1_csv_graph`. Nothing in `c4/data/` or the evaluation results was changed.

## What C1 provides today

- 83 concepts after adapter normalisation, 77 prerequisite edges (75 are hand-written "domain knowledge seed" entries, 2 come from caption text), 14 Bloom-level pair labels, 5 misconception pairs.
- No per-concept `facts` or `known_false` statements, which the C4 verifier needs, and no JSON export (stage 5 loads Neo4j and wipes the target database first).
- Evaluation files (`gold_corpus/annotations.csv`, `stage6_evaluate.py`) are empty.

## Prerequisites: C1 against the C4 fixture

| C4 concept | C4 prerequisites | C1 prerequisites | Agree |
|---|---|---|---|
| heap | arrays, binary_tree | array, binary tree | yes |
| stack | arrays | array | yes |
| queue | arrays | array | yes |
| tree | linked_list, recursion | (no `tree` concept) | no |
| binary_tree | tree | none recorded | no |
| arrays | none | data structure | no (C1 adds a generic root) |
| recursion | none | stack | no (see below) |

## Points to raise with C1

1. **Direction of `stack -> recursion`.** C1 lists stack as a prerequisite of recursion. C4 treats recursion as a root concept. One of the two is likely inverted for a first course; this needs a decision before the graphs are merged.
2. **No `tree` concept.** C1 has `binary tree` and `binary search tree` but no general tree, so the Trees node and its `linked list` / `recursion` prerequisites have no counterpart.
3. **Identifiers.** C1 uses names ("binary search tree"); C4 uses ids ("binary_tree", "arrays"). A mapping table is needed (`arrays` to `array` is already known).
4. **Misconceptions are concept pairs** (heap/stack), not false statements, so they cannot be used as `known_false` claims as they are.
5. **Linked list exists in C1** (array to linked list; linked list to singly, doubly and circular). This would fill the gap behind C4's out-of-graph `linked_list` prerequisite.

## What C4 needs from C1

- A JSON export with stable concept ids and the verified prerequisite edges.
- Five or more `facts` and `known_false` sentences for each of C4's seven target concepts (tree, binary_tree, heap, arrays, recursion, stack, queue).
- An agreed direction for the stack and recursion edge, and a `tree` concept.
