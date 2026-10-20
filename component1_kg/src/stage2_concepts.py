import spacy
import pandas as pd
import os

nlp = spacy.load("en_core_web_sm")

# Complete DSA concept list — covers both datasets fully
DSA_CONCEPTS = [
    # Core data structures
    "array", "arrays", "linked list", "linked lists", "doubly linked list",
    "stack", "stacks", "queue", "queues", "deque", "priority queue",
    "binary tree", "binary trees", "binary search tree", "bst",
    "avl tree", "red black tree", "b-tree", "trie", "heap", "min heap", "max heap",
    "hash table", "hash map", "hash set", "hash function", "hashing",
    "graph", "graphs", "directed graph", "undirected graph", "weighted graph",
    "adjacency list", "adjacency matrix",
    # Algorithms
    "sorting", "binary search", "linear search", "sequential search",
    "bubble sort", "selection sort", "insertion sort", "merge sort",
    "quick sort", "heap sort", "counting sort", "radix sort", "bucket sort",
    "depth-first search", "dfs", "breadth-first search", "bfs",
    "dijkstra", "bellman-ford", "floyd-warshall", "prim", "kruskal",
    "dynamic programming", "memoization", "tabulation",
    "recursion", "iteration", "divide and conquer",
    "greedy algorithm", "backtracking",
    # Concepts
    "time complexity", "space complexity", "big-o notation", "big o",
    "algorithm analysis", "asymptotic analysis",
    "pointer", "pointers", "memory allocation",
    "tree traversal", "inorder", "preorder", "postorder", "level order",
    "shortest path", "minimum spanning tree", "topological sort",
    "union find", "disjoint set",
    "two pointers", "sliding window", "prefix sum",
    "bit manipulation", "bitwise operations",
    "amortized analysis", "worst case", "average case", "best case",
    "symbol table", "balanced search tree",
]

def find_concepts_in_text(text):
    """Find which DSA concepts appear in this text"""
    text_lower = text.lower()
    found = []
    for concept in DSA_CONCEPTS:
        if concept in text_lower:
            found.append(concept)
    return list(set(found))

# Merge plural and variant forms into one canonical concept.
MERGE_MAP = {
    'arrays': 'array',
    'stacks': 'stack',
    'queues': 'queue',
    'pointers': 'pointer',
    'graphs': 'graph',
    'trees': 'tree',
    'heaps': 'heap',
    'tries': 'trie',
    'lists': 'list',
    'bst': 'binary search tree',
    'big o': 'big-o notation',
}

def run_concept_extraction(chunks_file, sample_size=100):
    df = pd.read_csv(chunks_file)
    df_sample = df.head(sample_size)

    all_concepts = set()
    results = []

    for i, (_, row) in enumerate(df_sample.iterrows()):
        concepts = find_concepts_in_text(row['text'])

        for concept in concepts:
            all_concepts.add(concept)
            results.append({
                'chunk_id': row['chunk_id'],
                'video_id': row['video_id'],
                'category': row['category'],
                'concept': concept
            })

        if concepts:
            print(f"[{i+1}/{sample_size}] Chunk {row['chunk_id']}: found {len(concepts)} → {concepts}")
        else:
            print(f"[{i+1}/{sample_size}] Chunk {row['chunk_id']}: none found")

    results_df = pd.DataFrame(results)
    results_df.to_csv('outputs/concepts_raw.csv', index=False)

    normalized = {
        MERGE_MAP.get(concept, concept)
        for concept in all_concepts
    }
    concept_nodes = pd.DataFrame({'concept': sorted(list(normalized))})
    concept_nodes.to_csv('outputs/concept_nodes.csv', index=False)

    print(f"\n✅ Total unique concepts found: {len(normalized)}")
    print(f"All concepts:\n{sorted(normalized)}")
    return concept_nodes

if __name__ == "__main__":
    run_concept_extraction('data/processed/chunks.csv', sample_size=100)