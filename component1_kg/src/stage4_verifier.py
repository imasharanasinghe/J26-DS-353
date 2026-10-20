import pandas as pd
import networkx as nx

MISCONCEPTION_WHITELIST = [
    ("worst case", "average case"),
    ("recursion", "iteration"),
    ("o(log n)", "o(n log n)"),
    ("stack", "queue"),
    ("binary search tree", "binary tree"),
    ("merge sort", "quick sort"),
    ("linked list", "array"),
    ("depth-first search", "breadth-first search"),
    ("big-o notation", "time complexity"),
    ("binary search", "linear search"),
    ("heap", "stack"),
    ("dynamic programming", "recursion"),
    ("tree", "graph"),
    ("graph", "minimum spanning tree"),
    ("binary search tree", "graph"),
    ("priority queue", "stack"),
    ("queue", "stack"),
]

BLOOM_LEVELS = ["remember", "understand", "apply", "analyze", "evaluate", "create"]

def verify_relations(relations_df):
    verified = []
    rejected = []

    # Build prerequisite graph for cycle detection
    prereq_graph = nx.DiGraph()

    print("Running symbolic verifier...\n")

    for _, row in relations_df.iterrows():
        concept_a = str(row.get('concept_a', '')).lower().strip()
        concept_b = str(row.get('concept_b', '')).lower().strip()
        relation_type = str(row.get('relation_type', '')).lower().strip()

        reason = None

        # ── RULE 1: No self-loops ─────────────────────────────────
        if concept_a == concept_b:
            reason = "SELF_LOOP"

        # ── RULE 2: Misconception must be on whitelist ────────────
        elif relation_type == "common-misconception-of":
            pair  = (concept_a, concept_b)
            pair_r = (concept_b, concept_a)
            matched = False
            for (w_a, w_b) in MISCONCEPTION_WHITELIST:
                if (w_a in concept_a and w_b in concept_b) or \
                   (w_a in concept_b and w_b in concept_a):
                    matched = True
                    break
            if not matched and pair not in MISCONCEPTION_WHITELIST and pair_r not in MISCONCEPTION_WHITELIST:
                reason = "WHITELIST"

        # ── RULE 3: Bloom level must be valid ─────────────────────
        elif relation_type == "bloom-level":
            bloom = str(row.get('bloom_level', '')).lower().strip()
            if bloom not in BLOOM_LEVELS:
                reason = "BLOOM_INCONSISTENCY"

        # ── RULE 4: No cycles in prerequisites ────────────────────
        elif relation_type == "prerequisite-of":
            prereq_graph.add_edge(concept_a, concept_b)
            if not nx.is_directed_acyclic_graph(prereq_graph):
                prereq_graph.remove_edge(concept_a, concept_b)
                reason = "CYCLE"

        # Store result
        row_dict = row.to_dict()
        if reason:
            row_dict['rejection_reason'] = reason
            rejected.append(row_dict)
            print(f"  ❌ REJECTED [{reason}]: {concept_a} --[{relation_type}]--> {concept_b}")
        else:
            verified.append(row_dict)
            print(f"  ✅ VERIFIED: {concept_a} --[{relation_type}]--> {concept_b}")

    return pd.DataFrame(verified), pd.DataFrame(rejected)

if __name__ == "__main__":
    df = pd.read_csv('outputs/relations_unverified.csv')
    print(f"Total relations to verify: {len(df)}\n")

    verified_df, rejected_df = verify_relations(df)

    # Remove duplicates from verified set
    verified_df = verified_df.drop_duplicates(
        subset=['relation_type', 'concept_a', 'concept_b']
    )

    verified_df.to_csv('outputs/relations_verified.csv', index=False)
    rejected_df.to_csv('outputs/rejected_edges_log.csv', index=False)

    print(f"\n{'='*50}")
    print(f"✅ Verified edges : {len(verified_df)}")
    print(f"❌ Rejected edges : {len(rejected_df)}")

    if len(rejected_df) > 0:
        print(f"\nRejection breakdown:")
        print(rejected_df['rejection_reason'].value_counts().to_string())

    print(f"\nVerified relations breakdown:")
    print(verified_df['relation_type'].value_counts().to_string())

    print(f"\nAll verified relations:")
    print(verified_df[['relation_type','concept_a','concept_b','bloom_level']].to_string())