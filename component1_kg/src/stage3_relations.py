import pandas as pd
import re
import os
from itertools import combinations

# ── Prerequisite linguistic patterns ─────────────────────────────────
PREREQ_PATTERNS = [
    r"before (we|you|we can) (learn|study|understand|look at|cover|discuss)",
    r"(requires?|needs?|depends? on|builds? on|based on) (a |an |the |knowledge of |understanding of )?",
    r"(must|should|need to) (know|understand|learn|have studied) .{0,30} (before|first|prior to)",
    r"(foundation|prerequisite|building block|basis) (of|for)",
    r"(now that|since) (you|we) (know|understand|have learned|have covered)",
    r"(recall|remember) (from|that|how) .{0,20} (we|you) (learned|covered|discussed|studied)",
    r"(extend|build|expand) (on|upon|from) .{0,20}(what|our)",
]

# ── Bloom level verb patterns ─────────────────────────────────────────
BLOOM_PATTERNS = {
    "remember":   [r"\b(recall|memorize|list|name|define|identify|state)\b"],
    "understand": [r"\b(explain|describe|summarize|interpret|classify|compare)\b"],
    "apply":      [r"\b(implement|use|apply|solve|execute|write|code|compute)\b"],
    "analyze":    [r"\b(analyze|examine|differentiate|distinguish|compare|contrast|break down)\b"],
    "evaluate":   [r"\b(evaluate|assess|justify|critique|argue|decide|choose between)\b"],
    "create":     [r"\b(design|construct|develop|formulate|build|produce|invent)\b"],
}

# ── Misconception whitelist ───────────────────────────────────────────
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
    ("arrays", "linked list"),
    ("dfs", "bfs"),
]

# Known DSA prerequisite pairs (factually correct, domain expert knowledge)
# These are injected as seeds since lecture text rarely states them explicitly
PREREQUISITE_SEEDS = [
    # Foundations
    ("array", "dynamic array"),
    ("array", "binary search"),
    ("array", "binary search tree"),
    ("array", "sorting"),
    ("array", "hash table"),
    ("array", "heap"),
    ("array", "trie"),
    ("array", "union find"),
    ("array", "radix sort"),
    ("array", "pointer"),
    ("array", "adjacency matrix"),
    ("array", "dynamic programming"),
    ("array", "segment tree"),
    ("array", "multidimensional array"),
    # Linked list family
    ("linked list", "singly linked list"),
    ("linked list", "doubly linked list"),
    ("linked list", "circular linked list"),
    ("array", "linked list"),
    # Stack & Queue
    ("array", "stack"),
    ("array", "queue"),
    ("stack", "recursion"),
    ("queue", "breadth-first search"),
    ("stack", "depth-first search"),
    ("stack", "stack top"),
    ("stack", "stack bottom"),
    ("queue", "circular queue"),
    ("queue", "deque"),
    ("heap", "priority queue"),
    # Tree family
    ("binary search", "binary search tree"),
    ("recursion", "binary search tree"),
    ("binary tree", "binary search tree"),
    ("binary search tree", "balanced binary tree"),
    ("balanced binary tree", "avl tree"),
    ("balanced binary tree", "red-black tree"),
    ("binary search tree", "b-tree"),
    ("b-tree", "b+ tree"),
    ("binary tree", "huffman tree"),
    ("heap", "heap sort"),
    ("binary tree", "heap"),
    ("array", "heap"),
    ("binary search tree", "symbol table"),
    ("array", "segment tree"),
    ("recursion", "trie"),
    ("linked list", "node"),
    ("binary tree", "root node"),
    ("binary tree", "leaf node"),
    ("binary tree", "traversal"),
    ("traversal", "level order traversal"),
    # Graph family
    ("array", "graph"),
    ("linked list", "adjacency list"),
    ("graph", "shortest path"),
    ("graph", "minimum spanning tree"),
    ("graph", "kruskal"),
    ("graph", "prim"),
    ("graph", "topological sort"),
    ("graph", "depth-first search"),
    ("graph", "breadth-first search"),
    ("graph", "directed graph"),
    ("graph", "undirected graph"),
    ("graph", "weighted graph"),
    ("graph", "connected graph"),
    ("connected graph", "strongly connected graph"),
    ("graph", "spanning tree"),
    # Sorting family
    ("sorting", "binary search"),
    ("sorting", "radix sort"),
    ("sorting", "divide and conquer"),
    ("array", "bubble sort"),
    ("array", "selection sort"),
    ("array", "insertion sort"),
    ("recursion", "merge sort"),
    ("divide and conquer", "merge sort"),
    ("recursion", "quicksort"),
    ("divide and conquer", "quicksort"),
    ("array", "counting sort"),
    ("array", "bucket sort"),
    # Search family
    ("array", "sequential search"),
    ("array", "linear search"),
    ("sorting", "binary search"),
    # Hashing
    ("array", "hashing"),
    ("hashing", "hash function"),
    ("hashing", "hash table"),
    ("hash function", "hash collision"),
    # Complexity
    ("algorithm", "time complexity"),
    ("algorithm", "space complexity"),
    ("time complexity", "computational complexity"),
    ("time complexity", "big-o notation"),
    ("big-o notation", "asymptotic analysis"),
    ("algorithm", "algorithm correctness"),
    ("algorithm", "algorithm complexity"),
    # Algorithm paradigms
    ("recursion", "divide and conquer"),
    ("recursion", "dynamic programming"),
    ("recursion", "backtracking"),
    ("dynamic programming", "memoization"),
    ("recursion", "recurrence"),
    # Memory & pointers
    ("pointer", "memory"),
    ("memory", "memory allocation"),
    ("memory allocation", "memory management"),
    ("memory", "dynamic array"),
    # String
    ("array", "string"),
    ("string", "string matching"),
    # Union Find
    ("array", "union find"),
    ("union find", "disjoint set"),
]

def detect_prerequisite(text, concept_a, concept_b):
    """Check if text suggests concept_a is a prerequisite of concept_b"""
    text_lower = text.lower()
    pos_a = text_lower.find(concept_a)
    pos_b = text_lower.find(concept_b)

    if pos_a == -1 or pos_b == -1:
        return False, None

    # Check linguistic patterns
    for pattern in PREREQ_PATTERNS:
        matches = list(re.finditer(pattern, text_lower))
        for match in matches:
            match_pos = match.start()
            # The pattern should appear between or near both concepts
            min_pos = min(pos_a, pos_b)
            max_pos = max(pos_a, pos_b)
            if min_pos - 100 <= match_pos <= max_pos + 100:
                # concept_a should appear before concept_b for prerequisite
                if pos_a < pos_b:
                    snippet = text[max(0, match_pos-30):match_pos+60]
                    return True, snippet.strip()

    # Also check: if concept_a appears much earlier in text than concept_b
        # Tighter transition check — must have a strong transition word
    if pos_a < pos_b:
        between = text_lower[pos_a:pos_b]
        strong_transitions = ['before we', 'before you', 'must know',
                              'need to know', 'now that you', 'now that we',
                              'builds on', 'depends on', 'based on',
                              'requires knowledge', 'prerequisite']
        for phrase in strong_transitions:
            if phrase in between:
                snippet = text[pos_a:pos_a+100]
                return True, snippet.strip()

    return False, None

def detect_bloom_level(text, concept):
    """Detect Bloom level from verbs near the concept in text"""
    text_lower = text.lower()
    pos = text_lower.find(concept)
    if pos == -1:
        return None, None

    # Look at text window around the concept
    window = text_lower[max(0, pos-150):pos+150]

    for level, patterns in BLOOM_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, window)
            if match:
                snippet = text[max(0, pos-50):pos+80].strip()
                return level, snippet

    return None, None

def detect_misconception(concept_a, concept_b):
    """Check if this pair is a known misconception"""
    pair = (concept_a.lower(), concept_b.lower())
    pair_r = (concept_b.lower(), concept_a.lower())
    if pair in MISCONCEPTION_WHITELIST or pair_r in MISCONCEPTION_WHITELIST:
        return True
    # Also check partial matches
    for (w_a, w_b) in MISCONCEPTION_WHITELIST:
        if (w_a in concept_a and w_b in concept_b) or \
           (w_a in concept_b and w_b in concept_a):
            return True
    return False

def run_relation_extraction(chunks_file, concepts_file, sample_chunks=100):
    df_chunks = pd.read_csv(chunks_file)
    df_concepts = pd.read_csv(concepts_file)
    concept_list = df_concepts['concept'].tolist()

    print(f"Loaded {len(concept_list)} concepts")
    print(f"Concepts: {concept_list}")
    print(f"\nProcessing {sample_chunks} chunks...\n")

    all_relations = []

    for i, (_, row) in enumerate(df_chunks.head(sample_chunks).iterrows()):
        text_lower = row['text'].lower()
        concepts_in_chunk = [c for c in concept_list if c in text_lower]

        if len(concepts_in_chunk) < 2:
            continue

        chunk_relations = 0

        for concept_a, concept_b in combinations(concepts_in_chunk[:10], 2):

            # --- Check 1: prerequisite-of ---
            is_prereq, snippet = detect_prerequisite(row['text'], concept_a, concept_b)
            if is_prereq:
                all_relations.append({
                    'relation_type': 'prerequisite-of',
                    'concept_a': concept_a,
                    'concept_b': concept_b,
                    'bloom_level': None,
                    'confidence': 'medium',
                    'source_text': snippet,
                    'chunk_id': row['chunk_id'],
                    'category': row['category'],
                    'video_id': row['video_id']
                })
                chunk_relations += 1
                print(f"  ✅ [prerequisite-of] {concept_a} → {concept_b}")
                continue  # one relation per pair

            # --- Check 2: bloom-level ---
            bloom_level, snippet = detect_bloom_level(row['text'], concept_b)
            if bloom_level:
                all_relations.append({
                    'relation_type': 'bloom-level',
                    'concept_a': concept_a,
                    'concept_b': concept_b,
                    'bloom_level': bloom_level,
                    'confidence': 'medium',
                    'source_text': snippet,
                    'chunk_id': row['chunk_id'],
                    'category': row['category'],
                    'video_id': row['video_id']
                })
                chunk_relations += 1
                print(f"  ✅ [bloom-level:{bloom_level}] {concept_b}")
                continue

            # --- Check 3: common-misconception-of ---
            if detect_misconception(concept_a, concept_b):
                all_relations.append({
                    'relation_type': 'common-misconception-of',
                    'concept_a': concept_a,
                    'concept_b': concept_b,
                    'bloom_level': None,
                    'confidence': 'high',
                    'source_text': f"known misconception pair: {concept_a} / {concept_b}",
                    'chunk_id': row['chunk_id'],
                    'category': row['category'],
                    'video_id': row['video_id']
                })
                chunk_relations += 1
                print(f"  ✅ [misconception] {concept_a} ↔ {concept_b}")

        if concepts_in_chunk:
            print(f"[{i+1}/{sample_chunks}] Chunk {row['chunk_id']}: {len(concepts_in_chunk)} concepts, {chunk_relations} relations")

        # Save BEFORE seeds so you can see the difference
    df_from_text = pd.DataFrame(all_relations)

    # Inject prerequisite seeds
    print("\nInjecting prerequisite seeds...")
    for (concept_a, concept_b) in PREREQUISITE_SEEDS:
        if concept_a in concept_list and concept_b in concept_list:
            all_relations.append({
                'relation_type': 'prerequisite-of',
                'concept_a': concept_a,
                'concept_b': concept_b,
                'bloom_level': None,
                'confidence': 'high',
                'source_text': 'domain knowledge seed',
                'chunk_id': 'seed',
                'category': 'seed',
                'video_id': 'seed'
            })
            print(f"  ✅ [prerequisite-of SEED] {concept_a} → {concept_b}")

    # Now save everything including seeds
    df_relations = pd.DataFrame(all_relations)
    df_relations.to_csv('outputs/relations_unverified.csv', index=False)

    print(f"\n{'='*50}")
    print(f"✅ Total relations extracted: {len(df_relations)}")
    if len(df_relations) > 0:
        print(f"\nBreakdown by relation type:")
        print(df_relations['relation_type'].value_counts().to_string())
        print(f"\nSample relations:")
        print(df_relations[['relation_type','concept_a','concept_b','bloom_level']].head(15).to_string())

    return df_relations

if __name__ == "__main__":
    run_relation_extraction(
        'data/processed/chunks.csv',
        'outputs/concept_nodes.csv',
        sample_chunks=100
    )