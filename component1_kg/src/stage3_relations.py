import pandas as pd
import re
import os
from itertools import combinations

# ── Prerequisite linguistic patterns ─────────────────────────────────
# These are phrases that signal "A must come before B" in lecture text
PREREQ_PATTERNS = [
    r"before (we|you|we can) (learn|study|understand|look at|cover)",
    r"(requires?|needs?|assumes?|depends? on|builds? on|based on)",
    r"(first|previously|earlier) (learn|cover|introduc|discuss|defin)",
    r"(must|should|need to) (know|understand|learn|have) .{0,30} (before|first|prior)",
    r"(foundation|prerequisite|building block|basis) (of|for)",
    r"(recall|remember|review) (that|how|what)",
    r"(extend|build|expand) (on|upon|from)",
    r"(now that|since) (you|we) (know|understand|have learned|covered)",
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
    # and text contains a transition word
    if pos_a < pos_b:
        between = text_lower[pos_a:pos_b]
        transition_words = ['before', 'first', 'then', 'next', 'after',
                           'now', 'once', 'having', 'knowing']
        for word in transition_words:
            if word in between:
                snippet = text[pos_a:pos_a+80]
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